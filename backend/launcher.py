import subprocess
import asyncio
import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

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
CHANNEL_NAME = os.getenv('TELEGRAM_CHANNEL')
DOWNLOAD_INTERVAL = int(os.getenv('DOWNLOAD_INTERVAL_MINUTES', 1))
MESSAGE_LIMIT = int(os.getenv('MESSAGE_LIMIT', 10))

async def run_downloader():
    while True:
        try:
            logger.info(f"Начало цикла загрузки для канала {CHANNEL_NAME}")
            start_time = datetime.now()
            
            # Запуск скрипта загрузки
            logger.info("Запуск download_channels.py")
            download_process = subprocess.Popen(
                [
                    "python", "backend/download_channels.py",
                    "--api-id", TELEGRAM_API_ID,
                    "--api-hash", TELEGRAM_API_HASH,
                    "--channel", CHANNEL_NAME,
                    "--limit", str(MESSAGE_LIMIT)
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = download_process.communicate()
            
            if download_process.returncode == 0:
                logger.info("Загрузка сообщений успешно завершена")
                if stdout:
                    logger.debug(f"Вывод download_channels.py: {stdout.decode('utf-8')}")
                
                # Запуск парсера и сохранения в БД
                logger.info("Запуск news_fetcher.py")
                parser_process = subprocess.run(
                    ["python", "-m", "backend.news_fetcher"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                if parser_process.returncode == 0:
                    execution_time = datetime.now() - start_time
                    logger.info(
                        f"Цикл успешно завершен. Время выполнения: {execution_time}"
                    )
                else:
                    logger.error(
                        f"Ошибка при обработке сообщений: {parser_process.stderr}"
                    )
            else:
                logger.error(
                    f"Ошибка при загрузке сообщений. Код: {download_process.returncode}"
                    f"\nОшибка: {stderr.decode('utf-8')}"
                )
            
        except Exception as e:
            logger.exception(f"Критическая ошибка в цикле загрузки: {str(e)}")
        
        logger.info(
            f"Ожидание {DOWNLOAD_INTERVAL} минут до следующего запуска"
        )
        await asyncio.sleep(DOWNLOAD_INTERVAL * 60)

if __name__ == "__main__":
    logger.info("Запуск сервиса загрузки Telegram сообщений")
    try:
        asyncio.run(run_downloader())
    except KeyboardInterrupt:
        logger.info("Сервис остановлен пользователем")
    except Exception as e:
        logger.exception(f"Критическая ошибка сервиса: {str(e)}") 