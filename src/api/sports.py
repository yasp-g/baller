import httpx
import logging
from datetime import date
from ..config import config

# Football-data API
class FootballAPI:
    def __init__(self):
        self.logger = logging.getLogger('baller.api.sports')
        self.base_url = config.FOOTBALL_DATA_BASE_URL
        self.headers = {
            "X-Auth-Token": config.FOOTBALL_DATA_API_KEY,
        }
        self.client = httpx.AsyncClient(
            headers=self.headers,
            timeout=10.0 
        )
        self.logger.debug("FootballAPI initialized")
    
    async def get_areas(self, area_id=None):
        """Get available areas, optionally filtered by area_id"""
        if area_id:
            endpoint = f"{self.base_url}/areas/{area_id}"
        else:
            endpoint = f"{self.base_url}/areas"
            
        response = await self.client.get(endpoint)
        response.raise_for_status()
        return response.json()
    
    async def get_competitions(self, areas=None):
        """Get available competitions (leagues), optionally filtered by areas"""
        filters = {}
        if areas:
            filters["areas"] = areas
        
        response = await self.client.get(f"{self.base_url}/competitions", params=filters)
        response.raise_for_status()
        return response.json()
    
    async def get_competition(self, competition_id):
        """Get detailed information about a specific competition"""
        response = await self.client.get(f"{self.base_url}/competitions/{competition_id}")
        response.raise_for_status()
        return response.json()
        
    async def get_standings(self, competition_id, season=None, matchday=None, date=None):
        """Get competition standings"""
        filters = {}
        if season:
            filters["season"] = season
        if matchday:
            filters["matchday"] = matchday
        if date:
            filters["date"] = date
            
        response = await self.client.get(f"{self.base_url}/competitions/{competition_id}/standings", params=filters)
        response.raise_for_status()
        return response.json()
    
    async def get_competition_matches(self, competition_id, date_from=None, date_to=None, stage=None, status=None, matchday=None, group=None, season=None):
        """Get matches for a specific competition with optional filters"""
        filters = {}
        if date_from:
            filters["dateFrom"] = date_from
        if date_to:
            filters["dateTo"] = date_to
        if stage:
            filters["stage"] = stage
        if status:
            filters["status"] = status
        if matchday:
            filters["matchday"] = matchday
        if group:
            filters["group"] = group
        if season:
            filters["season"] = season
            
        response = await self.client.get(f"{self.base_url}/competitions/{competition_id}/matches", params=filters)
        response.raise_for_status()
        return response.json()
    
    async def get_competition_teams(self, competition_id, season=None):
        """Get teams for a specific competition"""
        filters = {}
        if season:
            filters["season"] = season
            
        response = await self.client.get(f"{self.base_url}/competitions/{competition_id}/teams", params=filters)
        response.raise_for_status()
        return response.json()
    
    async def get_top_scorers(self, competition_id, limit=10, season=None):
        """Get top scorers for a competition"""
        filters = {}
        if limit:
            filters["limit"] = limit
        if season:
            filters["season"] = season
            
        response = await self.client.get(f"{self.base_url}/competitions/{competition_id}/scorers", params=filters)
        response.raise_for_status()
        return response.json()
    
    async def get_team(self, team_id):
        """Get detailed information about a team"""
        response = await self.client.get(f"{self.base_url}/teams/{team_id}")
        response.raise_for_status()
        return response.json()
    
    async def get_team_matches(self, team_id, date_from=None, date_to=None, season=None, competitions=None, status=None, venue=None, limit=None):
        """Get matches for a specific team with optional filters"""
        filters = {}
        if date_from:
            filters["dateFrom"] = date_from
        if date_to:
            filters["dateTo"] = date_to
        if season:
            filters["season"] = season
        if competitions:
            filters["competitions"] = competitions
        if status:
            filters["status"] = status
        if venue:
            filters["venue"] = venue  # HOME or AWAY
        if limit:
            filters["limit"] = limit
            
        response = await self.client.get(f"{self.base_url}/teams/{team_id}/matches", params=filters)
        response.raise_for_status()
        return response.json()
    
    async def get_person(self, person_id):
        """Get detailed information about a person (player or coach)"""
        response = await self.client.get(f"{self.base_url}/persons/{person_id}")
        response.raise_for_status()
        return response.json()
    
    async def get_person_matches(self, person_id, date_from=None, date_to=None, status=None, competitions=None, limit=None, offset=None):
        """Get matches for a specific person with optional filters"""
        filters = {}
        if date_from:
            filters["dateFrom"] = date_from
        if date_to:
            filters["dateTo"] = date_to
        if status:
            filters["status"] = status
        if competitions:
            filters["competitions"] = competitions
        if limit:
            filters["limit"] = limit
        if offset:
            filters["offset"] = offset
            
        response = await self.client.get(f"{self.base_url}/persons/{person_id}/matches", params=filters)
        response.raise_for_status()
        return response.json()
    
    async def get_match(self, match_id):
        """Get detailed information about a specific match"""
        response = await self.client.get(f"{self.base_url}/matches/{match_id}")
        response.raise_for_status()
        return response.json()
    
    async def get_matches(self, date_from=date.today(), date_to=None, competitions=None, ids=None, status=None):
        """Get matches across competitions with required date_from parameter"""
        filters = {
            "dateFrom": date_from,
        }
        
        if date_to:
            filters["dateTo"] = date_to
        if competitions:
            filters["competitions"] = competitions
        if ids:
            filters["ids"] = ids
        if status:
            filters["status"] = status
            
        response = await self.client.get(f"{self.base_url}/matches", params=filters)
        response.raise_for_status()
        return response.json()
    
    async def get_head_to_head(self, match_id, limit=10, date_from=None, date_to=None, competitions=None):
        """Get head-to-head matches for teams in a specific match"""
        filters = {}
        if limit:
            filters["limit"] = limit
        if date_from:
            filters["dateFrom"] = date_from
        if date_to:
            filters["dateTo"] = date_to
        if competitions:
            filters["competitions"] = competitions
            
        response = await self.client.get(f"{self.base_url}/matches/{match_id}/head2head", params=filters)
        response.raise_for_status()
        return response.json()
    
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