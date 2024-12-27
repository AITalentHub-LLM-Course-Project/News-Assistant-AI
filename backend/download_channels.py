from telethon import TelegramClient, sync
from telethon.tl.types import Channel
import asyncio
import os
from datetime import datetime
import argparse

async def download_channel_content(api_id, api_hash, channel_username, limit=100, output_dir=None):
    """
    Download content from a Telegram channel
    
    Parameters:
    api_id (int): Telegram API ID
    api_hash (str): Telegram API hash
    channel_username (str): Channel username without '@'
    limit (int): Maximum number of messages to download
    output_dir (str): Directory to save downloaded content
    """
    # Create client
    client = TelegramClient('session_name', api_id, api_hash)
    
    try:
        # Start client
        await client.start()
        
        # Get channel entity
        channel = await client.get_entity(channel_username)
        
        # Use provided output directory or create default one
        if output_dir:
            directory = output_dir
        else:
            directory = f"telegram_downloads_{channel_username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        os.makedirs(directory, exist_ok=True)
        
        # Создаем новый файл с временной меткой
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        messages_file = os.path.join(directory, f"messages_{timestamp}.txt")
        
        # Download messages
        messages = await client.get_messages(channel, limit=limit)
        
        # Process messages
        with open(messages_file, "w", encoding="utf-8") as f:
            for msg in messages:
                if msg.text:
                    # Формируем ссылку на сообщение
                    message_link = f"https://t.me/{channel_username}/{msg.id}"
                    f.write(f"[{msg.date}] {msg.text}\n[MESSAGE_LINK:{message_link}]\n\n")
                
        print(f"Downloaded content saved to {messages_file}")
        
    except Exception as e:
        print(f"Error occurred: {e}")
        
    finally:
        await client.disconnect()

async def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Скачивание сообщений из Telegram каналов')
    parser.add_argument('--api-id', required=True, help='Telegram API ID')
    parser.add_argument('--api-hash', required=True, help='Telegram API Hash')
    parser.add_argument('--channel', required=True, help='Имя канала')
    parser.add_argument('--limit', type=int, default=10, help='Лимит сообщений')
    parser.add_argument('--output-dir', help='Директория для сохранения сообщений')
    
    args = parser.parse_args()
    api_id = int(args.api_id)
    
    await download_channel_content(
        api_id, 
        args.api_hash, 
        args.channel, 
        args.limit,
        args.output_dir
    )

if __name__ == "__main__":
    asyncio.run(main())
