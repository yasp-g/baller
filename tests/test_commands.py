import asyncio
from src.api.sports import FootballAPI
from src.api.llm import LLMClient

class MockContext:
    """Mock Discord context for testing"""
    async def send(self, content=None, embed=None):
        print("\n=== Bot Response ===")
        if content:
            print(content)
        if embed:
            print(f"Embed Title: {embed.title}")
            for field in embed.fields:
                print(f"- {field.name}: {field.value}")

async def test_commands():
    api = FootballAPI()
    llm = LLMClient()
    ctx = MockContext()
    
    # Simulate processing a conversation
    user_message = "Who's playing in the Premier League today?"
    print(f"User: {user_message}")
    
    # Get relevant data (similar to what commands.py would do)
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    fixtures = await api.get_fixtures(league_id=39, date=today)
    
    # Generate response
    response = await llm.generate_response(user_message, fixtures)
    await ctx.send(content=response)
    
    # Test another query
    user_message2 = "What are the current Premier League standings?"
    print(f"\nUser: {user_message2}")
    
    # Get standings data
    standings = await api.get_standings(league_id=39)
    
    # Generate response
    response2 = await llm.generate_response(user_message2, standings)
    await ctx.send(content=response2)
    
    await api.close()

if __name__ == "__main__":
    asyncio.run(test_commands())