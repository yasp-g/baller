import httpx
from datetime import date
# from ..config import API_SPORTS_KEY, API_SPORTS_BASE_URL
from ..config import FOOTBALL_DATA_API_KEY

class FootballAPI:
    def __init__(self):
        self.base_url = "https://api.football-data.org/v4"
        self.headers = {
            "X-Auth-Token": FOOTBALL_DATA_API_KEY,
        }
        self.client = httpx.AsyncClient(headers=self.headers)
    
    async def get_competitions(self, country=None):
        """Get available competitions (leagues), optionally filtered by country"""
        params = {}
        if country:
            params["areas"] = country
        
        response = await self.client.get(f"{self.base_url}/competitions", params=params)
        response.raise_for_status()
        return response.json()
    
    async def get_matches(self, competition_id=None, team_id=None, date_from=None, date_to=None, status=None):
        """Get matches with various filters"""
        params = {}
        
        if date_from:
            params["dateFrom"] = date_from
        if date_to:
            params["dateTo"] = date_to
        if status:
            params["status"] = status
            
        # Endpoint changes based on filters
        if competition_id:
            endpoint = f"{self.base_url}/competitions/{competition_id}/matches"
        elif team_id:
            endpoint = f"{self.base_url}/teams/{team_id}/matches"
        else:
            endpoint = f"{self.base_url}/matches"
        
        response = await self.client.get(endpoint, params=params)
        response.raise_for_status()
        return response.json()
    
    async def get_match(self, match_id):
        """Get detailed information about a specific match"""
        response = await self.client.get(f"{self.base_url}/matches/{match_id}")
        response.raise_for_status()
        return response.json()
    
    async def get_standings(self, competition_id, season=None):
        """Get competition standings"""
        params = {}
        if season:
            params["season"] = season
            
        response = await self.client.get(f"{self.base_url}/competitions/{competition_id}/standings", params=params)
        response.raise_for_status()
        return response.json()
    
    async def get_team(self, team_id):
        """Get detailed information about a team"""
        response = await self.client.get(f"{self.base_url}/teams/{team_id}")
        response.raise_for_status()
        return response.json()
    
    async def get_team_matches(self, team_id, status=None, venue=None, limit=None):
        """Get matches for a specific team with optional filters"""
        params = {}
        if status:
            params["status"] = status
        if venue:
            params["venue"] = venue  # HOME or AWAY
        if limit:
            params["limit"] = limit
            
        response = await self.client.get(f"{self.base_url}/teams/{team_id}/matches", params=params)
        response.raise_for_status()
        return response.json()
    
    async def get_person(self, person_id):
        """Get detailed information about a person (player or coach)"""
        response = await self.client.get(f"{self.base_url}/persons/{person_id}")
        response.raise_for_status()
        return response.json()
    
    async def get_top_scorers(self, competition_id, season=None, limit=10):
        """Get top scorers for a competition"""
        params = {}
        if season:
            params["season"] = season
        if limit:
            params["limit"] = limit
            
        response = await self.client.get(f"{self.base_url}/competitions/{competition_id}/scorers", params=params)
        response.raise_for_status()
        return response.json()
    
    async def head_to_head(self, team1_id, team2_id, limit=10):
        """Get head-to-head matches between two teams"""
        # Football-data doesn't have a direct H2H endpoint, so we need to get team matches and filter
        team1_matches = await self.get_team_matches(team1_id, limit=50)
        
        # Filter matches where the opponent is team2
        h2h_matches = []
        for match in team1_matches.get("matches", []):
            home_team_id = match["homeTeam"]["id"]
            away_team_id = match["awayTeam"]["id"]
            
            if (home_team_id == team1_id and away_team_id == team2_id) or \
               (home_team_id == team2_id and away_team_id == team1_id):
                h2h_matches.append(match)
                
                # Stop once we have enough matches
                if len(h2h_matches) >= limit:
                    break
        
        return {"matches": h2h_matches[:limit]}
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()




# unfinished setup for API-Football from API-Sports
# class FootballAPI:
#     def __init__(self):
#         self.base_url = API_SPORTS_BASE_URL
#         self.headers = {
#             "x-rapidapi-host": "v3.football.api-sports.io", # TODO: don't hardcode this value
#             "x-rapidapi-key": API_SPORTS_KEY,
#         }
#         self.client = httpx.AsyncClient(headers=self.headers)

#     async def get_leagues(self, country=None):
#         """Get available leagues, optionally filtered by country"""
#         params = {}
#         if country:
#             params["country"] = country
        
#         response = await self.client.get(f"{self.base_url}/leagues", params=params)
#         response.raise_for_status()
#         return response.json()
    
#     async def get_fixtures(self, league_id=None, season=date.today().year, team_id=None, date=date.today(), status=None):
#         """Get fixtures with various filters"""
#         print(f"date: {date}")
#         print(f"season: {season}")
#         params = {}
#         if league_id:
#             params["league"] = league_id
#         if season:
#             params["season"] = season    
#         if team_id:
#             params["team"] = team_id
#         if date:
#             params["date"] = date
#         if status:
#             params["status"] = status
            
#         response = await self.client.get(f"{self.base_url}/fixtures", params=params)
#         response.raise_for_status()
#         return response.json()
    
#     async def get_standings(self, league_id, season=2023):
#         """Get league standings"""
#         params = {"league": league_id}
#         if season:
#             params["season"] = season
            
#         response = await self.client.get(f"{self.base_url}/standings", params=params)
#         response.raise_for_status()
#         return response.json()
    
#     async def close(self):
#         """Close the HTTP client"""
#         await self.client.aclose()