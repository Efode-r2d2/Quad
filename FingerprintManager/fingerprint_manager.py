import math
import operator
import sqlite3
from collections import defaultdict, namedtuple

import numpy as np


def __create_tables__(conn):
    """
    A function to create tables to store hashes(Hashes table), audio  information's (Audios table) and raw data
    associated with each hash(Quads table).

    Parameters:
        conn (String): a connection to the database.

    """
    conn.executescript("""
                CREATE VIRTUAL TABLE
                IF NOT EXISTS Hashes USING rtree(
                    id,
                    minNewCx, maxNewCx,
                    minNewCy, maxNewCy,
                    minNewDx, maxNewDx,
                    minNewDy, maxNewDy);
                CREATE TABLE
                IF NOT EXISTS Audios(
                    id INTEGER PRIMARY KEY,
                    audio_title TEXT);
                CREATE TABLE
                IF NOT EXISTS Quads(
                    hash_id INTEGER PRIMARY KEY,
                    audio_id INTEGER,
                    Ax INTEGER, Ay INTEGER,
                    Bx INTEGER, By INTEGER,
                    FOREIGN KEY(hash_id) REFERENCES Hashes(id),
                    FOREIGN KEY(audio_id) REFERENCES Records(id));""")


def store_audio(cursor, audio_title):
    """
    A function to store an audio record into the database.

    Parameters:
        cursor : the current cursor of the database.
        audio_title (String): The title of the audio.

    """
    cursor.execute("""INSERT INTO Audios
                         VALUES (null,?)""", (audio_title,))
    return cursor.lastrowid


def audio_exists(cursor, audio_title):
    """
    A function to check whether a given audio record exist or not.

    Parameters:
        cursor : the current cursor of the database.
        audio_title (String): Title of the audio.

    Returns:
        boolean: True if the record already exist or False if the record doesn't exist.

    """
    cursor.execute("""SELECT id
                           FROM Audios
                          WHERE audio_title = ?""", (audio_title,))
    record_id = cursor.fetchone()
    if record_id is None:
        return False
    else:
        print("Audio already exists...")
        return True


def radius_nn(cursor, hash_value, e=0.01):
    """
    A function to retrieve all the matching hashes with in the range of e.

    Parameters:
        cursor : The current cursor of the database.
        hash_value (tuple): A hash extracted from a query audio.
        e (float): A look up radius for the r-tree.

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


def store_quads(cursor, quad, audio_id):
    """
    A function to store raw data associated with each hash to reference fingerprint database. This data will be used
    later for filtering and verification purpose.

    Parameters:
        cursor: the current cursor of the database.
        quad (tuple): the raw information to be stored into the database.
        audio_id (int): Id of the audio.
    """
    hash_id = cursor.lastrowid
    values = (hash_id, audio_id, int(quad[0]), int(quad[1]), int(quad[2]), int(quad[3]))
    cursor.execute("""INSERT INTO Quads
                         VALUES (?,?,?,?,?,?)""", values)


def lookup_quads(conn, hash_id):
    """
    A function to retrieve raw data of the reference hash given its hash id.

    Parameters:
        conn : Connection object to the reference fingerprint database.
        hash_id (int): ID of reference audio hash.

    Returns:
        tuple : Raw data of for a given hash ID, the raw data consists of AX,AY,BX and By.

    """
    cursor = conn.cursor()
    cursor.execute("""SELECT Ax,Ay,Bx,By,audio_id FROM Quads
                          WHERE hash_id=?""", hash_id)
    row = cursor.fetchone()
    cursor.close()
    return [row[0], row[1], row[2], row[3]], row[4]


def bin_times(l, bin_width=20, ts=4):
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


def outlier_removal(d):
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


def scales(d):
    """
    Receives dictionary of {binned time : [scale factors]}
    Performs variance-based outlier removal on these scales. If 4 or more
    matches remain after outliers are removed, a list with form
    [(rough offset, num matches, scale averages)]] is created. This result
    is sorted by # of matches in descending order and returned.
    """
    o_rm = {k: outlier_removal(v) for k, v in d.items()}
    res = [(i[0], len(i[1]), np.mean(i[1], axis=0))
           for i in o_rm.items() if len(i[1]) >= 4]
    sorted_mc = sorted(res, key=operator.itemgetter(1), reverse=True)
    return sorted_mc


def filter_candidates(conn, cursor, query_quad, filtered, tolerance=0.31, e_fine=1.8):
    for hash_ids in cursor:
        reference_quad, audio_id = lookup_quads(conn, hash_ids)
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
        filtered[audio_id].append((offset, (sTime, sFreq)))


def store_hash(cursor, hash_value):
    """
    A function to store hashes into a reference fingerprint database.

    Parameters:
        cursor : the current cursor of the reference fingerprint database.
        hash_value (tuple) : hash values.

    """
    cursor.execute("""INSERT INTO Hashes VALUES (null,?,?,?,?,?,?,?,?)""",
                   (hash_value[0], hash_value[0], hash_value[1], hash_value[1],
                    hash_value[2], hash_value[2], hash_value[3], hash_value[3]))


def lookup_record(cursor, audio_id):
    """
    Returns title of given recordid
    """
    cursor.execute("""SELECT audio_title
                   FROM Audios
                  WHERE id = ?""", (audio_id,))
    title = cursor.fetchone()
    return title[0]


class FingerprintManager(object):
    """
    A class to manager audio fingerprints. This class is aimed at providing interfaces to store audio fingerprints
    and to query matching audios based on extracted fingerprints.

    Attributes:
        db_path (String): Path for reference audio fingerprints database.

    """

    def __init__(self, db_path):
        """
        A constructor method to FingerprintManager class.

        Parameters:
            db_path (String): Path of reference audio fingerprints database.

        """
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

    def store_fingerprints(self, audio_fingerprints, audio_title):
        """
        A method to store audion fingerprints.

        Parameters:
            audio_fingerprints (List): List of audio fingerprints.
            audio_title (String): Title of the audio.

        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if not audio_exists(cursor=cursor, audio_title=audio_title):
                record_id = store_audio(cursor=cursor, audio_title=audio_title)
                for i in audio_fingerprints:
                    store_hash(cursor=cursor, hash_value=i[0])
                    store_quads(cursor=cursor, quad=i[1], audio_id=record_id)
        conn.commit()
        conn.close()

    def query_audio(self, audio_fingerprints):
        match_candidates = self.__find_match_candidates(audio_fingerprints)
        conn = sqlite3.connect(self.db_path)

        cursor = conn.cursor()
        print(match_candidates)
        if len(match_candidates) > 0 and match_candidates[0][2] > 5:
            audio_id = lookup_record(cursor=cursor, audio_id=match_candidates[0][0])
            cursor.close()
            conn.close()
            return audio_id, match_candidates[0][2]
        else:
            return "No Match", 0

    def __find_match_candidates(self, audio_fingerprints):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        filtered = defaultdict(list)
        for i in audio_fingerprints:
            radius_nn(cursor, i[0])
            with np.errstate(divide='ignore', invalid='ignore'):
                filter_candidates(conn, cursor, i[1], filtered)
        binned = {k: bin_times(v) for k, v in filtered.items()}
        results = list()
        for k, v in binned.items():
            for j, m in v.items():
                results.append([k, j, len(m)])
        sorted_results = sorted(results, key=operator.itemgetter(2), reverse=True)
        cursor.close()
        conn.close()
        return sorted_results
