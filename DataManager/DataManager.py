import sqlite3


class DataManager(object):
    def __init__(self, db_path):
        self.db_path = db_path
        with sqlite3.connect(self.db_path) as conn:
            self.__create_tables__(conn)
        conn.close()

    def __create_tables__(self, conn):
        conn.executescript("""
                    CREATE VIRTUAL TABLE
                    IF NOT EXISTS Hashes USING rtree(
                        id,
                        minW, maxW,
                        minX, maxX,
                        minY, maxY,
                        minZ, maxZ);
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
