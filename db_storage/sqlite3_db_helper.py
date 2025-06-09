import sqlite3


class SQLiteSession:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = None
        self.cursor = None

    def __enter__(self):
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        return self.conn, self.cursor

    def __exit__(self, exc_type, exc_value, traceback):
        if self.conn is not None:
            if exc_type:
                self.conn.rollback()
            else:
                self.conn.commit()
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
