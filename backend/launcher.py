import subprocess
import asyncio
import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Загрузка переменных окружения
load_dotenv()

# Создание директории для логов если её нет
log_dir = 'logs'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Настройка логирования
log_file = os.path.join(log_dir, 'telegram_fetcher.log')
formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
)

# Настройка файлового обработчика с ротацией
file_handler = RotatingFileHandler(
    log_file,
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5,
    encoding='utf-8'
)
file_handler.setFormatter(formatter)

# Настройка вывода в консоль
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

# Настройка корневого логгера
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Получение конфигурации из .env
TELEGRAM_API_ID = os.getenv('TELEGRAM_API_ID')
TELEGRAM_API_HASH = os.getenv('TELEGRAM_API_HASH')
TELEGRAM_CHANNELS = os.getenv('TELEGRAM_CHANNELS')
DOWNLOAD_INTERVAL = int(os.getenv('DOWNLOAD_INTERVAL_MINUTES', 1))
MESSAGE_LIMIT = int(os.getenv('MESSAGE_LIMIT', 10))
TELEGRAM_DATA_DIR = os.getenv('TELEGRAM_DATA_DIR', 'telegram_channels_data')

def is_new_channel(channel_name):
    """Проверяет, является ли канал новым (отсутствует папка канала)"""
    channel_dir = Path(TELEGRAM_DATA_DIR) / channel_name
    return not channel_dir.exists()

def ensure_channel_directory(channel_name):
    """Создает директорию для канала, если она не существует"""
    channel_dir = Path(TELEGRAM_DATA_DIR) / channel_name
    channel_dir.mkdir(parents=True, exist_ok=True)
    return channel_dir

async def run_downloader():
    # Флаг первого запуска
    first_run = True
    
    while True:
        try:
            channels = TELEGRAM_CHANNELS.split(',') if TELEGRAM_CHANNELS else []
            if not channels:
                logger.error("Не указаны каналы в TELEGRAM_CHANNELS")
                await asyncio.sleep(DOWNLOAD_INTERVAL * 60)
                continue

            logger.info(f"Начало цикла загрузки для каналов: {channels}")
            start_time = datetime.now()
            
            # Загрузка сообщений из Telegram
            for channel in channels:
                try:
                    message_limit = 10000 if is_new_channel(channel) else MESSAGE_LIMIT
                    channel_dir = ensure_channel_directory(channel)
                    
                    # Запуск скрипта загрузки
                    logger.info(f"Запуск download_channels.py для {channel} с лимитом {message_limit}")
                    download_process = subprocess.Popen(
                        [
                            "python", "backend/download_channels.py",
                            "--api-id", TELEGRAM_API_ID,
                            "--api-hash", TELEGRAM_API_HASH,
                            "--channel", channel,
                            "--limit", str(message_limit),
                            "--output-dir", str(channel_dir)
                        ],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                    
                    stdout, stderr = download_process.communicate()
                    
                    if download_process.returncode == 0:
                        logger.info(f"Загрузка сообщений для канала {channel} успешно завершена")
                        if stdout:
                            logger.debug(f"Вывод download_channels.py: {stdout.decode('utf-8')}")
                    else:
                        logger.error(
                            f"Ошибка при загрузке сообщений для канала {channel}. "
                            f"Код: {download_process.returncode}\n"
                            f"Ошибка: {stderr.decode('utf-8')}"
                        )
                except Exception as e:
                    logger.error(f"Ошибка при обработке канала {channel}: {str(e)}")
                    continue
            
            # Запуск парсера с флагом полной загрузки при первом запуске
            logger.info("Запуск news_fetcher.py")
            cmd = ["python", "-m", "backend.news_fetcher"]
            if first_run:
                cmd.append("--full-load")

            parser_process = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )

            # Всегда логируем вывод
            if parser_process.stdout:
                logger.info(f"STDOUT news_fetcher.py:\n{parser_process.stdout}")
            if parser_process.stderr:
                logger.info(f"STDERR news_fetcher.py:\n{parser_process.stderr}")

            if parser_process.returncode == 0:
                execution_time = datetime.now() - start_time
                logger.info(f"Цикл успешно завершен. Время выполнения: {execution_time}")
                first_run = False
            else:
                logger.error(f"Ошибка при обработке сообщений. Код возврата: {parser_process.returncode}")
            
        except Exception as e:
            logger.exception(f"Критическая ошибка в цикле загрузки: {str(e)}")
        
        logger.info(f"Ожидание {DOWNLOAD_INTERVAL} минут до следующего запуска")
        await asyncio.sleep(DOWNLOAD_INTERVAL * 60)

if __name__ == "__main__":
    logger.info("Запуск сервиса загрузки Telegram сообщений")
    try:
        asyncio.run(run_downloader())
    except KeyboardInterrupt:
        logger.info("Сервис остановлен пользователем")
    except Exception as e:
        logger.exception(f"Критическая ошибка сервиса: {str(e)}") 