import asyncio
from src.api.llm import LLMClient

async def test_llm():
    llm = LLMClient()
    
    # Test with just a question
    response1 = await llm.generate_response("Who won the Bundesliga last season and when did it conclude?")
    print("=== Basic Question ===")
    print(response1)
    
    # Test with question and sample data
    sample_data = {
        "response": [
            {
                "league": {
                    "name": "Bundesliga",
                    "standings": [[
                        {"rank": 1, "team": {"name": "FC Bayern Munich"}, "points": 58},
                        {"rank": 2, "team": {"name": "Bayern 04 Leverkusen"}, "points": 50}
                    ]]
                }
            }
        ]
    }
    
    response2 = await llm.generate_response(
        "Who's at the top of the Bundesliga?", 
        sample_data
    )
    print("\n=== Question with Data ===")
    print(response2)

if __name__ == "__main__":
    asyncio.run(test_llm())