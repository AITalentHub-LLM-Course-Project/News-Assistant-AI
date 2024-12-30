import sqlite3
from contextlib import closing
import logging
from datetime import datetime
from typing import List, Dict

def create_table():
    with closing(sqlite3.connect('news.db')) as conn:
        with conn:
            # Создаем основную таблицу если её нет
            conn.execute('''
                CREATE TABLE IF NOT EXISTS news (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tg_ch_name TEXT,
                    timestamp DATETIME,
                    text TEXT,
                    message_link TEXT
                )
            ''')
            
            # Проверяем существование индекса
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) 
                FROM sqlite_master 
                WHERE type='index' AND name='idx_news_unique'
            ''')
            
            if cursor.fetchone()[0] == 0:
                # Удаляем дубликаты перед созданием уникального индекса
                conn.execute('''
                    DELETE FROM news 
                    WHERE rowid NOT IN (
                        SELECT MIN(rowid) 
                        FROM news 
                        GROUP BY timestamp, text
                    )
                ''')
                
                # Создаем уникальный индекс
                conn.execute('''
                    CREATE UNIQUE INDEX idx_news_unique 
                    ON news(timestamp, text)
                ''')
                logging.info("Создан уникальный индекс и удалены дубликаты")

def is_duplicate(timestamp, text):
    with closing(sqlite3.connect('news.db')) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) 
            FROM news 
            WHERE timestamp = ? AND text = ?
        ''', (timestamp, text))
        count = cursor.fetchone()[0]
        return count > 0

def insert_news(tg_ch_name, timestamp, text, message_link):
    try:
        if is_duplicate(timestamp, text):
            logging.info(f"Пропуск дубликата сообщения от {timestamp}")
            return False
            
        with closing(sqlite3.connect('news.db')) as conn:
            with conn:
                conn.execute('''
                    INSERT INTO news (tg_ch_name, timestamp, text, message_link)
                    VALUES (?, ?, ?, ?)
                ''', (tg_ch_name, timestamp, text, message_link))
        return True
    except sqlite3.IntegrityError:
        logging.info(f"Дубликат сообщения от {timestamp}")
        return False
    except Exception as e:
        logging.error(f"Ошибка при добавлении сообщения: {str(e)}")
        raise

def fetch_latest_news(limit: int = None) -> List[Dict]:
    """
    Получение новостей из БД с метаданными
    
    Args:
        limit: Максимальное количество возвращаемых записей. 
              Если None - возвращаются все записи
              
    Returns:
        List[Dict]: Список новостей с метаданными
    """
    with closing(sqlite3.connect('news.db')) as conn:
        with conn:
            query = '''
                SELECT text, timestamp, tg_ch_name, message_link 
                FROM news
                ORDER BY timestamp DESC
            '''
            
            if limit:
                query += ' LIMIT ?'
                cursor = conn.execute(query, (limit,))
            else:
                cursor = conn.execute(query)
                
            rows = cursor.fetchall()
            return [{
                'text': row[0],
                'date': datetime.fromisoformat(row[1]),
                'channel_id': row[2],
                'message_id': row[3].split('/')[-1] if row[3] else None
            } for row in rows] 