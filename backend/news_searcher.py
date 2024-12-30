from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.schema import Document
from datetime import datetime
from typing import List, Dict
import logging
from tqdm import tqdm
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NewsSearcher:
    def __init__(self, persist_directory: str = "./chroma_db", collection_name: str = "news"):
        """
        Инициализация векторного хранилища новостей
        
        Args:
            persist_directory (str): Путь к директории для хранения векторной БД
        """
        logger.info(f"Инициализация NewsSearcher с директорией {persist_directory}")
        
        self.embedding_function = SentenceTransformerEmbeddings(
            model_name="sergeyzh/rubert-tiny-turbo"
        )
        
        try:
            self.db = Chroma(
                persist_directory=persist_directory,
                embedding_function=self.embedding_function,
                collection_name=collection_name
            )
            self.last_sync_time = datetime.now()
            self.download_interval = int(os.getenv('DOWNLOAD_INTERVAL_MINUTES', 1))
            logger.info("Векторная БД успешно инициализирована")
        except Exception as e:
            logger.error(f"Ошибка при инициализации векторной БД: {e}")
            raise

    def _sync_if_needed(self):
        """Проверяет необходимость синхронизации с SQLite и выполняет её при необходимости"""
        current_time = datetime.now()
        time_diff = (current_time - self.last_sync_time).total_seconds() / 60

        if time_diff >= self.download_interval:
            logger.info("Синхронизация с SQLite требуется")
            try:
                from backend.database import fetch_latest_news_after
                new_items = fetch_latest_news_after(self.last_sync_time)
                
                if new_items:
                    self.add_news(new_items)
                    logger.info(f"Добавлено {len(new_items)} новых записей в Chroma")
                
                self.last_sync_time = current_time
                logger.info("Синхронизация успешно завершена")
            except Exception as e:
                logger.error(f"Ошибка при синхронизации с SQLite: {e}")
                raise

    def add_news(self, news_items: List[Dict]):
        """
        Добавляет новости в векторную базу данных
        
        Args:
            news_items: Список словарей с новостями, каждый должен содержать:
                - text: текст новости
                - date: дата публикации (datetime)
                - channel_id: ID канала
                - message_id: ID сообщения
        """
        try:
            documents = []
            ids = []
            
            for item in tqdm(news_items):
                doc = Document(
                    page_content=item['text'],
                    metadata={
                        'date': item['date'].timestamp(),
                        'channel_id': str(item['channel_id']),
                        'message_id': str(item['message_id'])
                    }
                )
                documents.append(doc)
                ids.append(f"{item['channel_id']}_{item['message_id']}")
            
            if documents:
                self.db.add_documents(documents, ids=ids)
                self.db.persist()
                logger.info(f"Добавлено {len(documents)} документов в векторную БД")
            
        except Exception as e:
            logger.error(f"Ошибка при добавлении новостей в векторную БД: {e}")
            raise

    def search_news(
        self, 
        query: str,
        start_date: datetime = None,
        end_date: datetime = None,
        k: int = 5
    ) -> List[tuple]:
        """
        Поиск новостей по запросу с фильтрацией по датам
        """
        try:
            self._sync_if_needed()
            
            filter_dict = {}
            if start_date and end_date:
                filter_dict = {
                    "$and": [
                        {"date": {"$gte": start_date.timestamp()}},
                        {"date": {"$lte": end_date.timestamp()}}
                    ]
                }
            
            results = self.db.similarity_search_with_score(
                query,
                k=k,
                filter=filter_dict if filter_dict else None
            )
            
            logger.info(f"Найдено {len(results)} релевантных документов")
            return results
            
        except Exception as e:
            logger.error(f"Ошибка при поиске новостей: {e}")
            raise

    def get_collection_stats(self) -> Dict:
        """
        Получение статистики о коллекции
        """
        try:
            return {
                "total_documents": self.db._collection.count(),
                "collection_name": self.db._collection.name
            }
        except Exception as e:
            logger.error(f"Ошибка при получении статистики: {e}")
            raise
