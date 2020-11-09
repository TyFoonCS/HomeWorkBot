import sqlite3


def db(mode):
    if mode == "testdb":
        conn = sqlite3.connect("test.db")
        cursor = conn.cursor()
    return conn, cursor
