import time
import logging
import os
import re
from datetime import datetime
from dotenv import load_dotenv
from backend.database import create_table, insert_news
import sys
from pathlib import Path

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
    'самокат', 'сим', 'мобильности',
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
    """Парсит текст сообщения и извлекает временную метку и содержание"""
    lines = text.strip().split('\n')
    timestamp = None
    content = []
    message_link = None
    
    for line in lines:
        if '[202' in line:  # Поиск строки с временной меткой
            if content:  # Если есть накопленный контент, возвращаем предыдущее сообщение
                yield {
                    'timestamp': timestamp,
                    'text': '\n'.join(content).strip(),
                    'message_link': message_link
                }
                content = []
                message_link = None
            timestamp = parse_timestamp(line)
            content.append(line)
        elif line.startswith('[MESSAGE_LINK:'):
            message_link = line[13:-1]  # Извлекаем ссылку
        elif line.strip():
            content.append(line)
    
    if content:
        yield {
            'timestamp': timestamp,
            'text': '\n'.join(content).strip(),
            'message_link': message_link
        }

def fetch_news_from_telegram():
    """Читает новости из файлов выгрузки Telegram с фильтрацией по ключевым словам"""
    news_items = []
    base_dir = Path(TELEGRAM_DATA_DIR)
    
    # Получаем список каналов из переменных окружения
    channels = os.getenv('TELEGRAM_CHANNELS').split(',')
    logging.info(f"Обрабатываются каналы: {channels}")
    
    for channel in channels:
        channel_dir = base_dir / channel
        if not channel_dir.exists():
            logging.warning(f"Папка не найдена для канала {channel}")
            continue
            
        # Получаем последний файл с сообщениями для канала
        messages_files = list(channel_dir.glob('messages*.txt'))
        if not messages_files:
            logging.warning(f"Файлы с сообщениями не найдены для канала {channel}")
            continue
            
        latest_file = max(messages_files, key=lambda x: x.stat().st_mtime)
        
        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            for message in parse_message(content):
                if message['timestamp'] and message['text']:
                    if contains_keywords(message['text']):
                        news_items.append({
                            'tg_ch_name': channel,
                            'timestamp': message['timestamp'],
                            'text': message['text'],
                            'message_link': message.get('message_link', '')  # Добавляем ссылку с пустым значением по умолчанию
                        })
                        logging.debug(
                            f"Добавлено сообщение с ключевыми словами: "
                            f"timestamp={message['timestamp']}"
                        )
            
        except Exception as e:
            logging.error(f"Ошибка при чтении файла {latest_file}: {str(e)}")
            continue
            
    return news_items

def fetch_and_store_news():
    # Инициализация базы данных
    create_table()
    
    logging.info("Запуск сервиса сбора новостей")
    
    try:
        logging.info("Начало сбора новостей")
        
        # Получение новостей из Telegram
        news_items = fetch_news_from_telegram()
        
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
    try:
        fetch_and_store_news()
    except Exception as e:
        logging.error(f"Критическая ошибка в news_fetcher: {str(e)}", exc_info=True)
        sys.exit(1)