import time
from backend.database import insert_news

def fetch_and_store_news():
    while True:
        # Fetch news from Telegram (pseudo-code)
        news_items = fetch_news_from_telegram()
        for news in news_items:
            insert_news(news['tg_ch_name'], news['timestamp'], news['text'])
        
        # Wait for N minutes
        time.sleep(60 * N)  # Replace N with the desired interval in minutes 