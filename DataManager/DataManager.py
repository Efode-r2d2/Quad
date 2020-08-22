import math
import sqlite3
import numpy as np
from collections import defaultdict
import operator

"""
    Creating a database consisting of four tables:
    1. Hashes Table: an R*Tree based virtual tables used to store hash values
    extracted using the association of four spectral peaks.
    2. Records Table: a table used to store required metadata's of a given song. 
    In this case we only store the title of the song as a metadata. 
    3. Quads Table: a table used to store raw data associated with each quad.
    4. Peaks Table: a table used to store raw information's associated with 
    each spectral peaks
"""


def __create_tables__(conn):
    conn.executescript("""
                CREATE VIRTUAL TABLE
                IF NOT EXISTS Hashes USING rtree(
                    id,
                    minNewCx, maxNewCx,
                    minNewCy, maxNewCy,
                    minNewDx, maxNewDx,
                    minNewDy, maxNewDy);
                CREATE TABLE
                IF NOT EXISTS Records(
                    id INTEGER PRIMARY KEY,
                    title TEXT);
                CREATE TABLE
                IF NOT EXISTS Quads(
                    hashid INTEGER PRIMARY KEY,
                    recordid INTEGER,
                    Ax INTEGER, Ay INTEGER,
                    Bx INTEGER, By INTEGER,
                    FOREIGN KEY(hashid) REFERENCES Hashes(id),
                    FOREIGN KEY(recordid) REFERENCES Records(id));
                CREATE TABLE
                IF NOT EXISTS Peaks(
                    recordid INTEGER, X INTEGER, Y INTEGER,
                    PRIMARY KEY(recordid, X, Y),
                    FOREIGN KEY(recordid) REFERENCES Records(id));""")


def __store_record__(cursor, title):
    cursor.execute("""INSERT INTO Records
                         VALUES (null,?)""", (title,))
    return cursor.lastrowid


def __record_exists__(cursor, title):
    cursor.execute("""SELECT id
                           FROM Records
                          WHERE title = ?""", (title,))
    record_id = cursor.fetchone()
    if record_id is None:
        return False
    else:
        print("record already exists...")
        return True


def __store_hash__(cursor, hash):
    cursor.execute("""INSERT INTO Hashes
                         VALUES (null,?,?,?,?,?,?,?,?)""",
                   (hash[0], hash[0], hash[1], hash[1], hash[2], hash[2], hash[3], hash[3]))


def __radius_nn__(cursor, hash, e=0.01):
    """
    Epsilon (e) neighbor search for a given hash. Matching hash ids
    can be retrieved from the cursor.
    """
    cursor.execute("""SELECT id FROM Hashes
                  WHERE minNewCx >= ? AND maxNewCx <= ?
                    AND minNewCy >= ? AND maxNewCy <= ?
                    AND minNewDx >= ? AND maxNewDx <= ?
                    AND minNewDy >= ? AND maxNewDy <= ?""",
                   (hash[0] - e, hash[0] + e,
                    hash[1] - e, hash[1] + e,
                    hash[2] - e, hash[2] + e,
                    hash[3] - e, hash[3] + e))


def __store_quad__(cursor, quad, record_id):
    hash_id = cursor.lastrowid
    values = (hash_id, record_id, int(quad[0]), int(quad[1]), int(quad[2]), int(quad[3]))
    cursor.execute("""INSERT INTO Quads
                         VALUES (?,?,?,?,?,?)""", values)


def __lookup_quads__(conn, hash_ids):
    cursor = conn.cursor()
    cursor.execute("""SELECT Ax,Ay,Bx,By,recordid FROM Quads
                          WHERE hashid=?""", hash_ids)
    row = cursor.fetchone()
    cursor.close()
    return [row[0], row[1], row[2], row[3]], row[4]


def __bin_times__(l, binwidth=20, ts=4):
    """
    Takes list of rough offsets and bins them in time increments of
    binwidth. These offsets are stored in a dictionary of
    {binned time : [list of scale factors]}. Binned time keys with
    less than Ts scale factor values are filtered out.
    """
    d = defaultdict(list)
    for rough_offset in l:
        div = rough_offset[0] / binwidth
        binname = int(math.floor(div) * binwidth)
        d[binname].append((rough_offset[1][0], rough_offset[1][1]))
    return {k: v for k, v in d.items() if len(v) >= ts}


def __outlier_removal__(d):
    """
    Calculates mean/std. dev. for sTime/sFreq values,
    then removes any outliers (defined as mean +/- 2 * stdv).
    Returns list of final means.
    """
    means = np.mean(d, axis=0)
    stds = np.std(d, axis=0)
    d = [v for v in d if
         (means[0] - 2 * stds[0] <= v[0] <= means[0] + 2 * stds[0]) and
         (means[1] - 2 * stds[1] <= v[1] <= means[1] + 2 * stds[1])]
    return d


def __scales__(d):
    """
    Receives dictionary of {binned time : [scale factors]}
    Performs variance-based outlier removal on these scales. If 4 or more
    matches remain after outliers are removed, a list with form
    [(rough offset, num matches, scale averages)]] is created. This result
    is sorted by # of matches in descending order and returned.
    """
    o_rm = {k: __outlier_removal__(v) for k, v in d.items()}
    res = [(i[0], len(i[1]), np.mean(i[1], axis=0))
           for i in o_rm.items() if len(i[1]) >= 4]
    sorted_mc = sorted(res, key=operator.itemgetter(1), reverse=True)
    return sorted_mc


def __store_peaks__(curosr, spectral_peaks, record_id):
    """
    Stores peaks from reference fingerprint
    """
    for i in spectral_peaks:
        curosr.execute("""INSERT INTO Peaks
                     VALUES (?,?,?)""", (record_id, int(i[0]), int(i[1])))


class DataManager(object):
    def __init__(self, db_path):
        self.db_path = db_path
        with sqlite3.connect(self.db_path) as conn:
            __create_tables__(conn)
        conn.close()

    def __store__(self, fingerprints, spectral_peaks, title):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if not __record_exists__(cursor=cursor, title=title):
                record_id = __store_record__(cursor=cursor, title=title)
                __store_peaks__(curosr=cursor, spectral_peaks=spectral_peaks, record_id=record_id)
                for i in fingerprints:
                    __store_hash__(cursor=cursor, hash=i[0])
                    __store_quad__(cursor=cursor, quad=i[1], record_id=record_id)
        conn.commit()
        conn.close()

    def __query__(self, audio_fingerprints, vThreshold=0.5):
        match_candidates = self.__find_match_candidates__(audio_fingerprints)

    def __find_match_candidates__(self, audio_fingerprints):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        filtered = defaultdict(list)
        for i in audio_fingerprints:
            __radius_nn__(cursor, i[0])
            with np.errstate(divide='ignore', invalid='ignore'):
                self.__filter_candidates__(conn, cursor, i[1], filtered)
        binned = {k: __bin_times__(v) for k, v in filtered.items()}
        results = {k: __scales__(v)
                   for k, v in binned.items() if len(v) >= 4}
        print(list(results.keys())[0])
        cursor.close()
        conn.close()

    def __filter_candidates__(self, conn, cursor, query_quad, filtered, tolerance=0.31, e_fine=1.8):
        for hash_ids in cursor:
            reference_quad, record_id = __lookup_quads__(conn, hash_ids)
            # Rough pitch coherence:
            #   1/(1+e) <= queAy/canAy <= 1/(1-e)
            if not 1 / (1 + tolerance) <= query_quad[1] / reference_quad[1] <= 1 / (1 - tolerance):
                continue
            # X transformation tolerance check:
            #   sTime = (queBx-queAx)/(canBx-canAx)
            sTime = (query_quad[2] - query_quad[0]) / (reference_quad[2] - reference_quad[0])
            if not 1 / (1 + tolerance) <= sTime <= 1 / (1 - tolerance):
                continue
            # Y transformation tolerance check:
            #   sFreq = (queBy-queAy)/(canBy-canAy)
            sFreq = (query_quad[3] - query_quad[1]) / (reference_quad[3] - reference_quad[1])
            if not 1 / (1 + tolerance) <= sFreq <= 1 / (1 - tolerance):
                continue
            # Fine pitch coherence:
            #   |queAy-canAy*sFreq| <= eFine
            if not abs(query_quad[1] - (reference_quad[1] * sFreq)) <= e_fine:
                continue
            offset = reference_quad[0] - (query_quad[0] * sTime)
            filtered[record_id].append((offset, (sTime, sFreq)))
