import time
import logging
import os
import re
from datetime import datetime
from dotenv import load_dotenv
from backend.database import create_table, insert_news
import sys
from pathlib import Path
import argparse

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Получение конфигурации из .env
DB_PATH = os.getenv('DB_PATH', 'news.db')
TELEGRAM_DATA_DIR = os.getenv('TELEGRAM_DATA_DIR', 'telegram_channels_data')

# Интервал обновления из переменных окружения
UPDATE_INTERVAL = int(os.getenv('DOWNLOAD_INTERVAL_MINUTES', 1))

KEYWORDS = [
    'самокат', 'мобильности',
    'электросамокат', 'кикшеринг'
]

def contains_keywords(text):
    """Проверяет наличие ключевых слов в тексте"""
    text_lower = text.lower()
    return any(keyword.lower() in text_lower for keyword in KEYWORDS)

def parse_timestamp(text):
    """Извлекает временную метку из строки формата [YYYY-MM-DD HH:MM:SS+00:00]"""
    match = re.search(r'\[(.*?)\]', text)
    if match:
        timestamp_str = match.group(1)
        return datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S%z')
    return None

def parse_message(text):
    """Парсит текст сообщения и извлекает временную метку, содержание и ссылку на сообщение"""
    lines = text.strip().split('\n')
    timestamp = None
    content = []
    message_link = None

    for line in lines:
        if '[202' in line:  # Поиск строки с временной меткой
            if timestamp is not None and content:  # Если есть накопленный контент, возвращаем предыдущее сообщение
                yield {
                    'timestamp': timestamp,
                    'text': '\n'.join(content).strip(),
                    'message_link': message_link
                }
                content = []
                message_link = None
            # Извлекаем временную метку
            timestamp_extracted = parse_timestamp(line)
            if timestamp_extracted:
                timestamp = timestamp_extracted
                # Вычисляем длину временной метки вместе с квадратными скобками
                # str(timestamp) даст 'YYYY-MM-DD HH:MM:SS+00:00'
                # Добавляем 2 для учета '[' и ']'
                timestamp_length = len(str(timestamp)) + 2
                # Удаляем временную метку из строки
                line_without_timestamp = line[timestamp_length:].strip()
                if line_without_timestamp:
                    content.append(line_without_timestamp)
            else:
                # Если временная метка не найдена, добавляем строку как есть
                content.append(line)
        elif line.startswith('[MESSAGE_LINK:'):
            message_link = line[13:-1]  # Извлекаем ссылку
        elif line.strip():
            content.append(line)
    
    if timestamp is not None and content:
        yield {
            'timestamp': timestamp,
            'text': '\n'.join(content).strip(),
            'message_link': message_link
        }

def fetch_news_from_telegram(full_load=False):
    """
    Читает новости из файлов выгрузки Telegram с фильтрацией по ключевым словам
    
    Args:
        full_load (bool): Если True, загружает все файлы. Если False, только последний.
    """
    news_items = []
    base_dir = Path(TELEGRAM_DATA_DIR)
    
    channels = os.getenv('TELEGRAM_CHANNELS').split(',')
    logging.info(f"Обрабатываются каналы: {channels}")
    
    total_files_processed = 0
    total_messages_found = 0
    
    for channel in channels:
        channel_dir = base_dir / channel
        if not channel_dir.exists():
            logging.warning(f"Папка не найдена для канала {channel}")
            continue
            
        messages_files = list(channel_dir.glob('messages*.txt'))
        if not messages_files:
            logging.warning(f"Файлы с сообщениями не найдены для канала {channel}")
            continue
        
        # Определяем какие файлы обрабатывать
        files_to_process = messages_files if full_load else [max(messages_files, key=lambda x: x.stat().st_mtime)]
        logging.info(f"Канал {channel}: найдено {len(messages_files)} файлов, будет обработано {len(files_to_process)}")
        
        channel_messages_count = 0
        for file_path in files_to_process:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                file_messages_count = 0
                for message in parse_message(content):
                    if message['timestamp'] and message['text']:
                        if contains_keywords(message['text']):
                            news_items.append({
                                'tg_ch_name': channel,
                                'timestamp': message['timestamp'],
                                'text': message['text'],
                                'message_link': message.get('message_link', '')
                            })
                            file_messages_count += 1
                
                channel_messages_count += file_messages_count
                total_files_processed += 1
                logging.info(f"Обработан файл {file_path.name}: найдено {file_messages_count} релевантных сообщений")
                            
            except Exception as e:
                logging.error(f"Ошибка при чтении файла {file_path}: {str(e)}")
                continue
        
        total_messages_found += channel_messages_count
        logging.info(f"Канал {channel}: обработано {len(files_to_process)} файлов, найдено {channel_messages_count} релевантных сообщений")
    
    logging.info(f"Итого: обработано {total_files_processed} файлов, найдено {total_messages_found} релевантных сообщений")
    return news_items

def fetch_and_store_news(full_load=False):
    """
    Получает и сохраняет новости в БД
    
    Args:
        full_load (bool): Если True, загружает все файлы. Если False, только последний.
    """
    # Инициализация базы данных
    create_table()
    
    logging.info("Запуск сервиса сбора новостей")
    
    try:
        logging.info("Начало сбора новостей")
        
        # Получение новостей из Telegram
        news_items = fetch_news_from_telegram(full_load=full_load)
        
        # Сохранение новостей в БД
        new_items_count = 0
        for news in news_items:
            if insert_news(
                news['tg_ch_name'],
                news['timestamp'],
                news['text'],
                news['message_link']
            ):
                new_items_count += 1
        
        logging.info(
            f"Обработано {len(news_items)} сообщений, "
            f"добавлено {new_items_count} новых"
        )
        
    except Exception as e:
        logging.error(f"Ошибка при сборе новостей: {str(e)}")
        raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--full-load', action='store_true', help='Загрузить все файлы')
    args = parser.parse_args()
    
    try:
        fetch_and_store_news(full_load=args.full_load)
    except Exception as e:
        logging.error(f"Критическая ошибка в news_fetcher: {str(e)}", exc_info=True)
        sys.exit(1)