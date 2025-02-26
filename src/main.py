import asyncio
import uvicorn
import threading
from bot.client import FootballBot

def run_api_server():
    """Run the FastAPI server in a separate thread"""
    uvicorn.run("api.server:app", host="0.0.0.0", port=8000, reload=False)

async def run_discord_bot():
    """Run the Discord bot"""
    bot = FootballBot()
    try:
        await bot.start_bot()
    except KeyboardInterrupt:
        await bot.close()

async def main():
    # Start the API server in a separate thread
    api_thread = threading.Thread(target=run_api_server)
    api_thread.daemon = True  # Thread will exit when main program exits
    api_thread.start()
    
    # Run the Discord bot in the main thread
    await run_discord_bot()

if __name__ == "__main__":
    asyncio.run(main())