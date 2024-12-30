from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.schema import Document
from datetime import datetime
from typing import List, Dict
import logging
from tqdm import tqdm

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
            logger.info("Векторная БД успешно инициализирована")
        except Exception as e:
            logger.error(f"Ошибка при инициализации векторной БД: {e}")
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

        Args:
            query: Поисковый запрос
            start_date: Начальная дата для фильтрации
            end_date: Конечная дата для фильтрации
            k: Количество результатов

        Returns:
            List[tuple]: Список кортежей (документ, score)
        """
        try:
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
