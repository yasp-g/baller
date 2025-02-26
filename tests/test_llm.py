import asyncio
from src.api.llm import LLMClient

async def test_llm():
    llm = LLMClient()
    
    # Test with just a question
    response1 = await llm.generate_response("Who won the Premier League last season?")
    print("=== Basic Question ===")
    print(response1)
    
    # Test with question and sample data
    sample_data = {
        "response": [
            {
                "league": {
                    "name": "Premier League",
                    "standings": [[
                        {"rank": 1, "team": {"name": "Manchester City"}, "points": 89},
                        {"rank": 2, "team": {"name": "Arsenal"}, "points": 86}
                    ]]
                }
            }
        ]
    }
    
    response2 = await llm.generate_response(
        "Who's at the top of the Premier League?", 
        sample_data
    )
    print("\n=== Question with Data ===")
    print(response2)

if __name__ == "__main__":
    asyncio.run(test_llm())