import sqlite3

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
    for j in cursor:
        print(j)


def __store_quad__(cursor, quad, record_id):
    hash_id = cursor.lastrowid
    values = (hash_id, record_id, quad[0], quad[1], quad[2], quad[3])
    cursor.execute("""INSERT INTO Quads
                         VALUES (?,?,?,?,?,?)""", values)


class DataManager(object):
    def __init__(self, db_path):
        self.db_path = db_path
        with sqlite3.connect(self.db_path) as conn:
            __create_tables__(conn)
        conn.close()

    def __store__(self, fingerprints, title):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if not __record_exists__(cursor=cursor, title=title):
                record_id = __store_record__(cursor=cursor, title=title)
                # self._store_peaks(c, fp, record_id)
                for i in fingerprints:
                    __store_hash__(cursor=cursor, hash=i[0])
                    __store_quad__(cursor=cursor, quad=i[1], record_id=record_id)
        conn.commit()
        conn.close()

    def __store_peak__(self, cursor, fingerprint, record_id):
        pass

    def __query__(self, audio_fingerprints, vThreshold=0.5):
        match_candidates = self.__find_match_candidates__(audio_fingerprints)

    def __find_match_candidates__(self, audio_fingerprints):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        for i in audio_fingerprints:
            __radius_nn__(cursor, i[0])
        cursor.close()
        conn.close()
