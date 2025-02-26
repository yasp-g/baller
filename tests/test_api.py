import asyncio
from src.api.sports import FootballAPI
import json
from datetime import date, timedelta

async def test_api():
    api = FootballAPI()
    try:
        # Test competitions endpoint
        print("=== Competitions ===")
        competitions = await api.get_competitions(country="2088")
        print(f"Found {len(competitions.get('competitions', []))} competitions")
        for comp in competitions.get('competitions', [])[:3]:  # Show first 3 competitions
            print(f"- {comp.get('name')} (ID: {comp.get('id')})")
        
        # Test matches endpoint with Bundesliga (ID: 2002)
        print("\n=== Bundesliga Matches ===")
        start_date = date.today()
        end_date = start_date + timedelta(days=7)
        matches = await api.get_matches(competition_id=2002, date_from=start_date, date_to=end_date)
        
        match_count = len(matches.get('matches', []))
        print(f"Found {match_count} Bundesliga matches today")
        
        if match_count > 0:
            # Show sample match details
            sample_match = matches.get('matches', [])[0]
            print(f"Sample match: {sample_match.get('homeTeam', {}).get('name')} vs "
                  f"{sample_match.get('awayTeam', {}).get('name')}")
            print(f"Status: {sample_match.get('status')}")
            print(f"Score: {sample_match.get('score', {}).get('fullTime', {}).get('home')} - "
                  f"{sample_match.get('score', {}).get('fullTime', {}).get('away')}")
        
        # Test standings endpoint with Bundesliga (ID: 2002)
        print("\n=== Bundesliga Standings ===")
        standings = await api.get_standings(competition_id=2002)
        
        # Access the first standings table (usually the regular season table)
        if standings.get('standings') and len(standings.get('standings')) > 0:
            table = standings.get('standings')[0].get('table', [])
            print(f"Top 5 teams:")
            for position in table[:5]:  # Show top 5 teams
                team = position.get('team', {}).get('name')
                id = position.get('team', {}).get('id')
                points = position.get('points')
                played = position.get('playedGames')
                print(f"- {position.get('position')}. {team} ({id}): {points}pts from {played} games")
        
        # Test team information
        print("\n=== Team Information ===")
        # Bayern Munich team_id is typically 5
        team_info = await api.get_team(team_id=5)
        print(f"Team: {team_info.get('name')}")
        print(f"Founded: {team_info.get('founded')}")
        print(f"Stadium: {team_info.get('venue')}")
        print(f"Website: {team_info.get('website')}")
        
        # Test top scorers
        print("\n=== Top Scorers ===")
        scorers = await api.get_top_scorers(competition_id=2002)
        print(f"Top 5 scorers in the Bundesliga:")
        for scorer in scorers.get('scorers', [])[:5]:
            player = scorer.get('player', {}).get('name')
            team = scorer.get('team', {}).get('name')
            goals = scorer.get('goals')
            print(f"- {player} ({team}): {goals} goals")
        
    except Exception as e:
        print(f"Error during testing: {str(e)}")
    finally:
        await api.close()
        print("\nAPI connection closed")

if __name__ == "__main__":
    print("Running football-data.org API tests...")
    asyncio.run(test_api())