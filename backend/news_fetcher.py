import time
import logging
import os
import re
from datetime import datetime
from dotenv import load_dotenv
from backend.database import create_table, insert_news
import sys

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Получение конфигурации из .env
DB_PATH = os.getenv('DB_PATH', 'news.db')

# Интервал обновления из переменных окружения
UPDATE_INTERVAL = int(os.getenv('DOWNLOAD_INTERVAL_MINUTES', 1))

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
    
    for line in lines:
        if '[202' in line:  # Поиск строки с временной меткой
            if content:  # Если есть накопленный контент, возвращаем предыдущее сообщение
                yield {
                    'timestamp': timestamp,
                    'text': '\n'.join(content).strip()
                }
                content = []
            timestamp = parse_timestamp(line)
            content.append(line)
        elif line.strip():
            content.append(line)
    
    # Возвращаем последнее сообщение
    if content:
        yield {
            'timestamp': timestamp,
            'text': '\n'.join(content).strip()
        }

def fetch_news_from_telegram():
    """Читает новости из файлов выгрузки Telegram"""
    news_items = []
    downloads_dir = 'telegram_downloads_mosnow_'
    
    # Получаем название канала из переменных окружения
    channel_name = os.getenv('TELEGRAM_CHANNEL')
    logging.info(f"Используется канал: {channel_name}")
    
    # Поиск последней папки с выгрузкой
    download_folders = [d for d in os.listdir() if d.startswith(downloads_dir)]
    if not download_folders:
        logging.warning("Папки с выгрузкой не найдены")
        return []
    
    latest_folder = max(download_folders)
    messages_file = os.path.join(latest_folder, 'messages.txt')
    logging.info(f"Обработка файла: {messages_file}")
    
    try:
        with open(messages_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        for message in parse_message(content):
            if message['timestamp'] and message['text']:
                news_items.append({
                    'tg_ch_name': channel_name,
                    'timestamp': message['timestamp'],
                    'text': message['text']
                })
                logging.debug(
                    f"Добавлено сообщение: timestamp={message['timestamp']}, "
                    f"длина текста={len(message['text'])} символов"
                )
        
        logging.info(
            f"Прочитано {len(news_items)} сообщений из {messages_file} "
            f"для канала {channel_name}"
        )
        
    except Exception as e:
        logging.error(
            f"Ошибка при чтении файла {messages_file}: {str(e)}\n"
            f"Тип ошибки: {type(e).__name__}"
        )
        raise
    
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
                news['text']
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