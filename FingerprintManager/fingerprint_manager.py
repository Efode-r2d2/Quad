import math
import operator
import sqlite3
from collections import defaultdict, namedtuple

import numpy as np

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


def __store_hash__(cursor, hash_value):
    """Strong hash value into Hashes table."""
    cursor.execute("""INSERT INTO Hashes VALUES (null,?,?,?,?,?,?,?,?)""",
                   (hash_value[0], hash_value[0], hash_value[1], hash_value[1],
                    hash_value[2], hash_value[2], hash_value[3], hash_value[3]))


def __radius_nn__(cursor, hash_value, e=0.01):
    """
    Looking for a matching hash values for a given hash value with in a range of e.
    """
    cursor.execute("""SELECT id FROM Hashes
                  WHERE minNewCx >= ? AND maxNewCx <= ?
                    AND minNewCy >= ? AND maxNewCy <= ?
                    AND minNewDx >= ? AND maxNewDx <= ?
                    AND minNewDy >= ? AND maxNewDy <= ?""",
                   (hash_value[0] - e, hash_value[0] + e,
                    hash_value[1] - e, hash_value[1] + e,
                    hash_value[2] - e, hash_value[2] + e,
                    hash_value[3] - e, hash_value[3] + e))


def __store_quad__(cursor, quad, record_id):
    """
    Storing raw values of A (Ax,Ay) and B (Bx,By) for each hash.
    Where the x-component defines the frame number (tempo information) and
    the y-component defines the pitch (frequency information) value of the respective hash.
    """
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


def __bin_times__(l, bin_width=20, ts=4):
    """
    Takes list of rough offsets and bins them in time increments of
    bin width. These offsets are stored in a dictionary of
    {binned time : [list of scale factors]}. Binned time keys with
    less than Ts scale factor values are filtered out.
    """
    d = defaultdict(list)
    for rough_offset in l:
        div = rough_offset[0] / bin_width
        bin_name = int(math.floor(div) * bin_width)
        d[bin_name].append((rough_offset[1][0], rough_offset[1][1]))
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


def __filter_candidates__(conn, cursor, query_quad, filtered, tolerance=0.31, e_fine=1.8):
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


class FingerprintManager(object):
    def __init__(self, db_path):
        self.db_path = db_path
        with sqlite3.connect(self.db_path) as conn:
            __create_tables__(conn)
        self._create_named_tuples()
        conn.close()

    def _create_named_tuples(self):
        self.Peak = namedtuple('Peak', ['x', 'y'])
        self.Quad = namedtuple('Quad', ['A', 'C', 'D', 'B'])
        mcNames = ['recordid', 'offset', 'num_matches', 'sTime', 'sFreq']
        self.MatchCandidate = namedtuple('MatchCandidate', mcNames)
        self.Match = namedtuple('Match', ['record', 'offset', 'vScore'])

    def __store__(self, fingerprints, title):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if not __record_exists__(cursor=cursor, title=title):
                record_id = __store_record__(cursor=cursor, title=title)
                for i in fingerprints:
                    __store_hash__(cursor=cursor, hash_value=i[0])
                    __store_quad__(cursor=cursor, quad=i[1], record_id=record_id)
        conn.commit()
        conn.close()

    def __query__(self, audio_fingerprints):
        match_candidates = self.__find_match_candidates__(audio_fingerprints)
        conn = sqlite3.connect(self.db_path)

        cursor = conn.cursor()
        if len(match_candidates) > 0:
            audio_id = self._lookup_record(c=cursor, recordid=match_candidates[0].recordid)
            cursor.close()
            conn.close()
            return audio_id, match_candidates[0].num_matches
        else:
            return "No Match", 0

    def __find_match_candidates__(self, audio_fingerprints):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        filtered = defaultdict(list)
        for i in audio_fingerprints:
            __radius_nn__(cursor, i[0])
            with np.errstate(divide='ignore', invalid='ignore'):
                __filter_candidates__(conn, cursor, i[1], filtered)
        binned = {k: __bin_times__(v) for k, v in filtered.items()}
        results = {k: __scales__(v)
                   for k, v in binned.items() if len(v) >= 4}
        match_candidates = [self.MatchCandidate(k, a[0], a[1], a[2][0], a[2][1])
                            for k, v in results.items() for a in v]
        cursor.close()
        conn.close()
        return match_candidates
