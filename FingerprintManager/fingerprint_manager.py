import math
import operator
import sqlite3
from bisect import bisect_left, bisect_right
from collections import defaultdict

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
                    FOREIGN KEY(audio_id) REFERENCES Audios(id));
                CREATE TABLE
                IF NOT EXISTS Peaks(
                    audio_id INTEGER, Px INTEGER, Py INTEGER,
                    PRIMARY KEY(audio_id, Px, Py),
                    FOREIGN KEY(audio_id) REFERENCES Audios(id));""")


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


def find_hash(cursor, hash_value, e=0.01):
    """
    A function to retrieve all the matching hashes with in the range of e.

    Parameters:
        cursor : The current cursor of the database.
        hash_value (tuple): A hash extracted from a query audio.
        e (float): A look up radius for the r-tree.

    """
    cursor.execute("""SELECT Quads.Ax,Quads.Ay,Quads.Bx,Quads.By,Quads.audio_id FROM Quads INNER JOIN Hashes
                    ON Quads.hash_id = Hashes.id
                  WHERE Hashes.minNewCx >= ? AND Hashes.maxNewCx <= ?
                    AND Hashes.minNewCy >= ? AND Hashes.maxNewCy <= ?
                    AND Hashes.minNewDx >= ? AND Hashes.maxNewDx <= ?
                    AND Hashes.minNewDy >= ? AND Hashes.maxNewDy <= ?""",
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


def filter_candidates(cursor, query_quad, filtered, tolerance=0.31, e_fine=1.8):
    for reference_quad in cursor:
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
        offset = reference_quad[0] - (query_quad[0] / sTime)
        filtered[reference_quad[4]].append((offset, (sTime, sFreq)))


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


def outlier_removal(binned_item, results):
    means = np.mean(binned_item[3], axis=0)
    stds = np.std(binned_item[3], axis=0)
    items = [v for v in binned_item[3] if
             (means[0] - 2 * stds[0] <= v[0] <= means[0] + 2 * stds[0]) and
             (means[1] - 2 * stds[1] <= v[1] <= means[1] + 2 * stds[1])]
    results.append([binned_item[0], binned_item[1], means[0], means[1], len(items)])


def store_peaks(cursor, spectral_peaks, audio_id):
    """
    Store spectral peaks extracted from reference audios.

    Parameters:
        cursor : the current cursor of the database.
        spectral_peaks (List) : list of spectral peaks extracted from the reference audio.
        audio_id (int): id of the audio.

    """
    for i in spectral_peaks:
        cursor.execute("""INSERT INTO Peaks
                     VALUES (?,?,?)""", (audio_id, int(i[0]), int(i[1])))


def lookup_peak_range(cursor, audio_id, offset, e=3750):
    """
    Queries Peaks table for peaks of given recordid that are within
    3750 samples (15s) of the estimated offset value.
    """
    data = (offset, offset + e, audio_id)
    cursor.execute("""SELECT Px, Py
                   FROM Peaks
                  WHERE Px >= ? AND Px <= ?
                    AND audio_id = ?""", data)
    return [p for p in cursor.fetchall()]


def verify_peaks(match, reference_peaks, query_peaks, eX=18, eY=12):
    """
    Checks for presence of a given set of reference peaks in the
    query fingerprint's list of peaks according to time and
    frequency boundaries (eX and eY). Each reference peak is adjusted
    according to estimated sFreq/sTime from candidate filtering
    stage.
    Returns: validation score (num. valid peaks / total peaks)
    """
    validated = 0
    for i in reference_peaks:
        reference_peak = (i[0] - match[1], i[1])
        reference_peak_scaled = (reference_peak[0] * match[2], reference_peak[1] * match[3])
        lBound = bisect_left(query_peaks, (reference_peak_scaled[0] - eX, None))
        rBound = bisect_right(query_peaks, (reference_peak_scaled[0] + eX, None))
        for j in range(lBound, rBound):
            if not reference_peak_scaled[1] - eY <= query_peaks[j][1] <= reference_peak_scaled[1] + eY:
                continue
            else:
                validated += 1
    vScore = (float(validated) / len(reference_peaks))
    return vScore


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
        conn.close()

    def store_fingerprints(self, audio_fingerprints, spectral_peaks, audio_title):
        """
        A method to store audion fingerprints.

        Parameters:
            audio_fingerprints (List): List of audio fingerprints.
            spectral_peaks (List): List of spectral peaks extracted from spectrogram of the audio.
            audio_title (String): Title of the audio.

        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if not audio_exists(cursor=cursor, audio_title=audio_title):
                audio_id = store_audio(cursor=cursor, audio_title=audio_title)
                store_peaks(cursor=cursor, spectral_peaks=spectral_peaks, audio_id=audio_id)
                for i in audio_fingerprints:
                    store_hash(cursor=cursor, hash_value=i[0])
                    store_quads(cursor=cursor, quad=i[1], audio_id=audio_id)
        conn.commit()
        conn.close()

    def query_audio(self, audio_fingerprints, query_peaks):
        match_candidates = self.find_matches(audio_fingerprints)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        if len(match_candidates) > 0:
            reference_peaks = lookup_peak_range(cursor=cursor, audio_id=match_candidates[0][0],
                                                offset=match_candidates[0][1])

            v_score = verify_peaks(match=match_candidates[0], reference_peaks=reference_peaks,
                                   query_peaks=query_peaks)
            print(match_candidates[0][0], match_candidates[0][1], len(reference_peaks), v_score)
            if v_score > 0.2:
                audio_title = lookup_record(cursor=cursor, audio_id=match_candidates[0][0])
                cursor.close()
                conn.close()
                return audio_title, match_candidates[0][2], match_candidates[0][1]
            else:
                return "No Match", 0
        else:
            return "No Match", 0

    def find_matches(self, audio_fingerprints):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        filtered = defaultdict(list)
        for i in audio_fingerprints:
            find_hash(cursor=cursor, hash_value=i[0])
            with np.errstate(divide='ignore', invalid='ignore'):
                filter_candidates(cursor=cursor, query_quad=i[1], filtered=filtered)
        binned = {k: bin_times(v) for k, v in filtered.items()}
        results = list()
        binned_items = list()
        for k, v in binned.items():
            for j, m in v.items():
                # print(v)
                binned_items.append([k, j, len(m), m])
        for i in binned_items:
            outlier_removal(binned_item=i, results=results)
        sorted_results = sorted(results, key=operator.itemgetter(4), reverse=True)
        cursor.close()
        conn.close()
        return sorted_results
