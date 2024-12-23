import sqlite3
from contextlib import closing

def create_table():
    with closing(sqlite3.connect('news.db')) as conn:
        with conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS news (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tg_ch_name TEXT,
                    timestamp DATETIME,
                    text TEXT
                )
            ''')

def insert_news(tg_ch_name, timestamp, text):
    with closing(sqlite3.connect('news.db')) as conn:
        with conn:
            conn.execute('''
                INSERT INTO news (tg_ch_name, timestamp, text)
                VALUES (?, ?, ?)
            ''', (tg_ch_name, timestamp, text))

def fetch_latest_news():
    with closing(sqlite3.connect('news.db')) as conn:
        with conn:
            cursor = conn.execute('''
                SELECT text FROM news
                ORDER BY timestamp DESC
                LIMIT 5
            ''')
            return [row[0] for row in cursor.fetchall()] 