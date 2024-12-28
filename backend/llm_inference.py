import os
from dotenv import load_dotenv
from langchain.chat_models.gigachat import GigaChat
from langchain.schema import HumanMessage, SystemMessage
from backend.database import fetch_latest_news
from sentence_transformers import SentenceTransformer, util

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
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

    def generate_response(self, prompt: str) -> str:
        try:
            # подтягиваем последние новости
            latest_news = fetch_latest_news()

            # преобразуем запрос и новости в векторы
            # prompt_embedding = self.embedding_model.encode(prompt, convert_to_tensor=True)
            # news_embeddings = self.embedding_model.encode(latest_news, convert_to_tensor=True)

            # вычисляем косинусное сходство
            # similarities = util.pytorch_cos_sim(prompt_embedding, news_embeddings)

            # выбираем наиболее релевантные новости
            # top_k = 5  # количество наиболее релевантных новостей
            # top_k_indices = similarities.topk(k=top_k).indices

            # объединяем контекст наиболее релевантных новостей с запросом
            # relevant_news = [latest_news[i] for i in top_k_indices]
            relevant_news = ['дела хорошо', 'дела отлично']
            news_context = " ".join(relevant_news)
            print('news_context', news_context)
            full_prompt = f"Ответь на вопрос, используя следующие новости:\n{news_context}\n вопрос: {prompt}"

            print('try to generate messages')
            messages = [
                SystemMessage(content="You are a helpful assistant."),
                HumanMessage(content=full_prompt)
            ]
            print('try to generate response')
            response = self.model(messages)
            
            # Получаем текст ответа из AIMessage
            return response.content

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

        response = llm_inference.generate_response(messages)
        messages.append(response)
        print("Assistant: ", response)