import asyncio
import uvicorn
import threading
import signal
from .bot.client import BallerBot

def run_api_server():
    """Run the FastAPI server in a separate thread"""
    uvicorn.run("src.api.server:app", host="0.0.0.0", port=8000, reload=False)

async def run_discord_bot():
    """Run the Discord bot"""
    bot = BallerBot()
    try:
        await bot.start_bot()
    except asyncio.CancelledError:
        print("Bot shutdown initiated...")
    finally:
        print("Closing bot connection...")
        await bot.close()
        print("Bot shutdown complete")

async def main():
    # Start the API server in a separate thread
    api_thread = threading.Thread(target=run_api_server)
    api_thread.daemon = True  # Thread will exit when main program exits
    api_thread.start()
    
    # Set up signal handlers
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(
            sig,
            lambda sig=sig: asyncio.create_task(shutdown(sig, loop))
        )
    
    # Run the Discord bot in the main thread
    await run_discord_bot()

async def shutdown(sig, loop):
    """Clean shutdown of the application"""
    print(f"Received exit signal {sig.name}...")
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    
    for task in tasks:
        task.cancel()
    
    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nApplication shut down by keyboard interrupt")
    except Exception as e:
        print(f"Unexpected error: {e}")