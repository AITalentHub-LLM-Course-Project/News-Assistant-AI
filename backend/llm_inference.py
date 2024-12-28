import os
import logging
from dotenv import load_dotenv
from langchain.chat_models.gigachat import GigaChat
from langchain.schema import HumanMessage, SystemMessage
from backend.database import fetch_latest_news
from sentence_transformers import SentenceTransformer, util
from backend.news_searcher import NewsSearcher
from datetime import datetime, timedelta
from typing import List, Dict

# Настройка логирования
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

class LLMInference:
    def __init__(self):
        self.api_key = os.getenv('GIGACHAT_API_KEY')
        self.model_name = os.getenv('GIGACHAT_MODEL_NAME')
        
        if not self.api_key or not self.model_name:
            raise ValueError("API key and model name must be set in environment variables.")
        
        self.model = GigaChat(
            credentials=self.api_key,
            model='GigaChat',
            verify_ssl_certs=False
        )
        
        # Инициализируем векторную БД
        self.news_searcher = NewsSearcher()
        
        # Загружаем начальные данные из SQLite
        self._initialize_vector_db()

    def _initialize_vector_db(self):
        """Инициализация векторной БД данными из SQLite"""
        news_items = fetch_latest_news(limit=100)  # Берем последние 100 записей для начальной инициализации
        if news_items:
            self.news_searcher.add_news(news_items)

    def generate_response(self, prompt: str) -> str:
        """
        Генерация ответа на основе контекста из новостей
        
        Args:
            prompt: Вопрос пользователя
            
        Returns:
            str: Ответ модели
        """
        try:
            # Убеждаемся, что prompt - это строка
            if isinstance(prompt, list):
                prompt = " ".join(prompt)
                
            # Ищем релевантные новости за последние 7 дней
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
            
            relevant_docs = self.news_searcher.search_news(
                query=prompt,
                start_date=start_date,
                end_date=end_date,
                k=5
            )
            print('relevant_docs', relevant_docs)
            
            # Формируем контекст из найденных документов
            context_parts = []
            for doc, score in relevant_docs:
                context_parts.append(f"Новость (релевантность: {score:.2f}):\n{doc.page_content}")
            
            context = "\n\n".join(context_parts)
            
            if not context:
                context = "К сожалению, релевантных новостей не найдено."
            
            full_prompt = (
                "На основе следующих новостей ответь на вопрос. "
                "Если в новостях нет релевантной информации, так и скажи.\n\n"
                f"Новости:\n{context}\n\n"
                f"Вопрос: {prompt}"
            )
            print('full_prompt', full_prompt)

            messages = [
                SystemMessage(content="You are a helpful assistant."),
                HumanMessage(content=full_prompt)
            ]
            
            response = self.model(messages)
            return response.content
            # return 'TODO: add good system prompt'

        except Exception as e:
            print(f"Error generating response: {e}")
            return f"An error occurred while generating the response: {str(e)}"

if __name__ == "__main__": # for testing
    messages = [
        SystemMessage(content="You are a helpful assistant."), # TODO: add good system prompt
    ]
    llm_inference = LLMInference()

    while True:
        user_message = input("User: ")
        if user_message.lower() in ['exit', 'quit']:
            break
        messages.append(HumanMessage(content=user_message))

        response = llm_inference.generate_response(user_message)
        messages.append(response)
        print("Assistant: ", response)