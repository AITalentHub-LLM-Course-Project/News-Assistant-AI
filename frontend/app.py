from datetime import datetime

import requests
import streamlit as st

# Настройка страницы
st.set_page_config(page_title="RAGa и копыта Chatbot", page_icon="🤖", layout="wide")

# Применение пользовательских стилей CSS
st.markdown(
    """
<style>
    .stChat message {
        border-radius: 10px;
        padding: 10px;
    .stChat .user-message {
        background-color: #e6f3ff;
        text-align: right;
    }
    .stChat .bot-message {
        background-color: #f0f0f0;
    }
    .stChat .message-content {
        font-size: 16px;
    }
</style>
""",
    unsafe_allow_html=True,
)

# Конфигурация API
API_URL = "http://localhost:8000/ask"

# Боковая панель
with st.sidebar:
    st.title("🤖 RAGa и копыта Chatbot")
    st.markdown("""
    ## About
    Этот чат-бот создан для помощи в ПДД для электросамокатов.
    Он может ответить на вопросы о:
    - Правилах использования электросамокатов
    - Как вести себя на дороге
    - Расскажет об актуальных правилах ПДД
    """)

# Основная область чата
st.title("💬 Ассистент")

# Инициализация истории чата
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "question": "Здравствуйте! Я AI-ассистент. Чем я могу вам помочь сегодня?",
        }
    ]

# Отображение истории чата
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["question"])


# Функция для отправки запроса к API
def query_api(question, start_date_str, end_date_str):
    try:
        response = requests.post(
            API_URL,
            json={
                "question": question,
                "start_date": start_date_str,
                "end_date": end_date_str,
            },
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Ошибка при обращении к API: {e!s}")
        return None


# Функция для обработки ввода пользователя
def handle_user_input(question, start_date_str, end_date_str):
    st.session_state.messages.append(
        {
            "role": "user",
            "question": question,
            "start_date": start_date_str,
            "end_date": end_date_str,
        }
    )
    with st.chat_message("user"):
        st.markdown(question)

    with st.spinner("AI думает..."):
        api_response = query_api(question, start_date_str, end_date_str)

    if api_response and "answer" in api_response:
        bot_response = api_response["answer"]
        st.session_state.messages.append(
            {"role": "assistant", "question": bot_response}
        )
        with st.chat_message("assistant"):
            st.markdown(bot_response)
    else:
        st.error("Не удалось получить корректный ответ от API.")


# Ввод пользователя
question = st.chat_input("Введите ваш вопрос здесь...")
start_date = st.date_input("Начальная дата", value=datetime.now().date())
end_date = st.date_input("Конечная дата", value=datetime.now().date())
if question and start_date and end_date:
    # Конвертирование дат в строчный формат
    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date_str = end_date.strftime("%Y-%m-%d")
    handle_user_input(question, start_date_str, end_date_str)

# Кнопка для очистки истории чата
if st.button("Очистить историю чата"):
    st.session_state.messages = [
        {
            "role": "assistant",
            "question": "История чата очищена. Чем я могу вам помочь?",
        }
    ]
    st.rerun()
