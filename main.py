import asyncio
import threading
from web_interface import create_web_app
from bot import bot
import os

def run_web_interface():
    """Run the web interface in a separate thread"""
    app = create_web_app()
    app.run(host='0.0.0.0', port=5000, debug=False)

async def main():
    """Main function to run both web interface and Discord bot"""
    # Start web interface in a separate thread
    web_thread = threading.Thread(target=run_web_interface, daemon=True)
    web_thread.start()
    
    # Get bot token from environment
    bot_token = os.getenv('DISCORD_BOT_TOKEN')
    if not bot_token:
        print("❌ DISCORD_BOT_TOKEN environment variable not set!")
        print("Please set your Discord bot token in the environment variables.")
        return
    
    try:
        print("🚀 Starting Discord bot...")
        await bot.start(bot_token)
    except Exception as e:
        print(f"❌ Failed to start bot: {e}")

if __name__ == "__main__":
    asyncio.run(main())
