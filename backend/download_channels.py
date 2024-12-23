from telethon import TelegramClient, sync
from telethon.tl.types import Channel
import asyncio
import os
from datetime import datetime
import argparse

async def download_channel_content(api_id, api_hash, channel_username, limit=100):
    """
    Download content from a Telegram channel
    
    Parameters:
    api_id (int): Telegram API ID
    api_hash (str): Telegram API hash
    channel_username (str): Channel username without '@'
    limit (int): Maximum number of messages to download
    """
    # Create client
    client = TelegramClient('session_name', api_id, api_hash)
    
    try:
        # Start client
        await client.start()
        
        # Get channel entity
        channel = await client.get_entity(channel_username)
        
        # Create directory for downloads
        directory = f"telegram_downloads_{channel_username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.makedirs(directory, exist_ok=True)
        
        # Download messages
        messages = await client.get_messages(channel, limit=limit)
        
        # Process messages
        for msg in messages:
            # Save text messages
            if msg.text:
                with open(f"{directory}/messages.txt", "a", encoding="utf-8") as f:
                    f.write(f"[{msg.date}] {msg.text}\n\n")
            
            # Download media
            # if msg.media:
            #     await client.download_media(msg, directory)
                
        print(f"Downloaded content saved to {directory}")
        
    except Exception as e:
        print(f"Error occurred: {e}")
        
    finally:
        await client.disconnect()

async def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Download Telegram channel content')
    parser.add_argument('--api-id', required=True, help='Telegram API ID')
    parser.add_argument('--api-hash', required=True, help='Telegram API hash')
    parser.add_argument('--channel', required=True, help='Channel username without @')
    parser.add_argument('--limit', type=int, default=100, help='Maximum number of messages to download (default: 100)')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Convert api_id to integer
    api_id = int(args.api_id)
    
    await download_channel_content(api_id, args.api_hash, args.channel, args.limit)

if __name__ == "__main__":
    asyncio.run(main())
