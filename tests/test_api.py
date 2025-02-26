import asyncio
import json
import time
from datetime import date, timedelta
from src.api.sports import FootballAPI

async def test_api_comprehensive():
    """Test all FootballAPI methods with Germany/Bundesliga focus"""
    api = FootballAPI()
    try:
        # Constants for Germany, Bundesliga, and Bayern Munich
        GERMANY_ID = 2088
        BUNDESLIGA_ID = 2002
        BAYERN_MUNICH_ID = 5
        today = date.today()

        # Test areas endpoint
        print("=== Areas ===")
        areas = await api.get_areas()
        print(f"Found {len(areas.get('areas', []))} total areas")
        
        # Test specific area (Germany)
        germany_area = await api.get_areas(area_id=GERMANY_ID)
        print(f"Area details: {germany_area.get('name')} (ID: {germany_area.get('id')})")
        
        # Test competitions endpoint for Germany
        print("\n=== German Competitions ===")
        competitions = await api.get_competitions(areas=str(GERMANY_ID))
        print(f"Found {len(competitions.get('competitions', []))} competitions in Germany")
        for comp in competitions.get('competitions', [])[:3]:
            print(f"- {comp.get('name')} (ID: {comp.get('id')})")
        
        # Test specific competition (Bundesliga)
        print("\n=== Bundesliga Details ===")
        competition = await api.get_competition(competition_id=BUNDESLIGA_ID)
        print(f"Competition: {competition.get('name')}")
        print(f"Current season: {competition.get('currentSeason', {}).get('startDate')} to {competition.get('currentSeason', {}).get('endDate')}")
        
        # Test standings endpoint for Bundesliga
        print("\n=== Bundesliga Standings ===")
        standings = await api.get_standings(competition_id=BUNDESLIGA_ID)
        table = standings.get('standings', [{}])[0].get('table', [])
        print(f"Top 5 teams in {standings.get('competition', {}).get('name')}:")
        for position in table[:5]:
            team = position.get('team', {}).get('name')
            team_id = position.get('team', {}).get('id')
            points = position.get('points')
            played = position.get('playedGames')
            print(f"- {position.get('position')}. {team} (ID: {team_id}): {points}pts from {played} games")
        
        # Test competition matches endpoint for Bundesliga
        print("\n=== Bundesliga Upcoming Matches ===")
        next_week = today + timedelta(days=7)
        matches = await api.get_competition_matches(
            competition_id=BUNDESLIGA_ID,
            date_from=today,
            date_to=next_week,
            status="SCHEDULED"
        )
        
        scheduled_matches = matches.get('matches', [])
        print(f"Found {len(scheduled_matches)} scheduled Bundesliga matches in next week")
        if scheduled_matches:
            match = scheduled_matches[0]
            print(f"Sample match: {match.get('homeTeam', {}).get('name')} vs {match.get('awayTeam', {}).get('name')}")
            print(f"Date: {match.get('utcDate')}")
            # Store a match ID for later head-to-head test
            sample_match_id = match.get('id')
        else:
            # If no scheduled matches, use general matches
            general_matches = await api.get_competition_matches(
                competition_id=BUNDESLIGA_ID,
                date_from=today - timedelta(days=30),  # Last 30 days
                date_to=today
            )
            if general_matches.get('matches'):
                sample_match_id = general_matches.get('matches', [])[0].get('id')
            else:
                sample_match_id = None
        
        # Test competition teams endpoint for Bundesliga
        print("\n=== Bundesliga Teams ===")
        teams = await api.get_competition_teams(competition_id=BUNDESLIGA_ID)
        print(f"Found {len(teams.get('teams', []))} teams in {teams.get('competition', {}).get('name')}")
        
        # Test top scorers endpoint for Bundesliga
        print("\n=== Bundesliga Top Scorers ===")
        scorers = await api.get_top_scorers(competition_id=BUNDESLIGA_ID, limit=5)
        print(f"Top 5 scorers in {scorers.get('competition', {}).get('name')}:")
        top_scorer_id = None
        for scorer in scorers.get('scorers', []):
            player = scorer.get('player', {})
            player_name = player.get('name')
            player_id = player.get('id')
            team = scorer.get('team', {}).get('name')
            goals = scorer.get('goals', 0)
            print(f"- {player_name} (ID: {player_id}) ({team}): {goals} goals")
            # Store first player ID for person test
            if top_scorer_id is None:
                top_scorer_id = player_id
        
        # Test team endpoint (Bayern Munich)
        print("\n=== Team Information (Bayern Munich) ===")
        team = await api.get_team(team_id=BAYERN_MUNICH_ID)
        print(f"Team: {team.get('name')}")
        print(f"Founded: {team.get('founded')}")
        print(f"Stadium: {team.get('venue')}")
        print(f"Website: {team.get('website')}")

        print("\n=== Starting delay after 10th query... ===")
        time.sleep(61)
        print("Delay finished.")
        
        # Test team matches endpoint for Bayern Munich
        print("\n=== Bayern Munich Matches ===")
        team_matches = await api.get_team_matches(
            team_id=BAYERN_MUNICH_ID,
            date_from=today - timedelta(days=30),  # Last 30 days
            date_to=today + timedelta(days=30),    # Next 30 days
            status="SCHEDULED",
            competitions=str(BUNDESLIGA_ID)        # Only Bundesliga matches
        )
        print(f"Found {len(team_matches.get('matches', []))} upcoming Bundesliga matches for {team.get('name')}")
        
        # Test person endpoint with top Bundesliga scorer
        if top_scorer_id:
            print(f"\n=== Top Scorer Information (ID: {top_scorer_id}) ===")
            person = await api.get_person(person_id=top_scorer_id)
            print(f"Player: {person.get('name')}")
            print(f"Position: {person.get('position', 'Unknown')}")
            print(f"Nationality: {person.get('nationality', 'Unknown')}")
            print(f"Birth: {person.get('dateOfBirth', 'Unknown')}")
            
            # Test person matches endpoint
            print(f"\n=== {person.get('name')}'s Recent Matches ===")
            person_matches = await api.get_person_matches(
                person_id=top_scorer_id,
                date_from=today - timedelta(days=90),  # Last 90 days
                date_to=today,
                competitions=str(BUNDESLIGA_ID),
                limit=5
            )
            print(f"Found {len(person_matches.get('matches', []))} recent Bundesliga matches for {person.get('name')}")
            for match in person_matches.get('matches', [])[:2]:
                home = match.get('homeTeam', {}).get('name', 'Unknown')
                away = match.get('awayTeam', {}).get('name', 'Unknown')
                date_played = match.get('utcDate', '?')[:10]  # Just the date part
                score_home = match.get('score', {}).get('fullTime', {}).get('home', '?')
                score_away = match.get('score', {}).get('fullTime', {}).get('away', '?')
                print(f"- {date_played}: {home} {score_home}-{score_away} {away}")
        
        # Test match endpoint
        if sample_match_id:
            print("\n=== Match Details ===")
            match = await api.get_match(match_id=sample_match_id)
            print(f"Match: {match.get('homeTeam', {}).get('name')} vs {match.get('awayTeam', {}).get('name')}")
            print(f"Competition: {match.get('competition', {}).get('name')}")
            print(f"Status: {match.get('status')}")
            
            # Test head-to-head endpoint
            print("\n=== Head to Head ===")
            h2h = await api.get_head_to_head(match_id=sample_match_id, limit=5)
            print(f"Found {len(h2h.get('matches', []))} previous encounters")
            for h2h_match in h2h.get('matches', [])[:2]:
                score_home = h2h_match.get('score', {}).get('fullTime', {}).get('home', '?')
                score_away = h2h_match.get('score', {}).get('fullTime', {}).get('away', '?')
                h_team = h2h_match.get('homeTeam', {}).get('name')
                a_team = h2h_match.get('awayTeam', {}).get('name')
                date_played = h2h_match.get('utcDate', '?')[:10]  # Just the date part
                print(f"- {date_played}: {h_team} {score_home}-{score_away} {a_team}")
        
        # Test matches endpoint across multiple competitions
        print("\n=== German Football Matches ===")
        german_competitions = [comp.get('id') for comp in competitions.get('competitions', [])[:3]]
        if german_competitions:
            comp_ids = ",".join(str(cid) for cid in german_competitions)
            multi_comp_matches = await api.get_matches(
                competitions=comp_ids,
                date_from=today,
                date_to=today + timedelta(days=3)
            )
            print(f"Found {len(multi_comp_matches.get('matches', []))} upcoming matches across German competitions")
            
            # Show matches by competition
            competitions_found = {}
            for match in multi_comp_matches.get('matches', []):
                comp_name = match.get('competition', {}).get('name')
                if comp_name not in competitions_found:
                    competitions_found[comp_name] = 0
                competitions_found[comp_name] += 1
            
            for comp_name, count in competitions_found.items():
                print(f"- {comp_name}: {count} matches")
        
    except Exception as e:
        print(f"Error during testing: {str(e)}")
    finally:
        await api.close()
        print("\nAPI connection closed")

if __name__ == "__main__":
    print("Running comprehensive football-data.org API tests (Germany/Bundesliga focus)...")
    asyncio.run(test_api_comprehensive())