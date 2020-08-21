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
                    Cx INTEGER, Cy INTEGER,
                    Dx INTEGER, Dy INTEGER,
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
                # self._store_peaks(c, fp, recordid)
                for i in fingerprints:
                    __store_hash__(cursor=cursor, hash=i[0])
                    #self._store_quad(cursor=cursor, quad=i[1], record_id=record_id)
        conn.commit()
        conn.close()

    def __store_peak__(self, cursor, fingerprint, record_id):
        pass

    def __store_quad__(self, cursor, quad, record_id):
        pass
