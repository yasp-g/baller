import httpx
import logging
import time
from datetime import date
from typing import Dict, Any, Optional, List, Union
from ..config import config
from .utils import async_retry
from ..exceptions import (
    APIConnectionError,
    APIAuthenticationError,
    APIRateLimitError,
    APIResourceNotFoundError
)

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
        
    async def _handle_request_exception(self, e: httpx.HTTPError, resource_type: Optional[str] = None, resource_id: Optional[str] = None) -> None:
        """Handle HTTP exceptions and raise appropriate custom exceptions"""
        if isinstance(e, httpx.TimeoutException):
            raise APIConnectionError(
                message="Request timed out",
                details={"url": str(e.request.url) if e.request else None}
            ) from e
        
        if isinstance(e, httpx.ConnectError):
            raise APIConnectionError(
                message="Failed to connect to API server",
                details={"url": str(e.request.url) if e.request else None}
            ) from e
            
        if isinstance(e, httpx.HTTPStatusError):
            status_code = e.response.status_code
            
            if status_code == 401:
                raise APIAuthenticationError(
                    message="Authentication failed with football data API",
                    details={"url": str(e.request.url)}
                ) from e
                
            if status_code == 404:
                raise APIResourceNotFoundError(
                    message=f"Resource not found: {resource_type or 'Unknown'} {resource_id or ''}",
                    resource_type=resource_type,
                    resource_id=resource_id
                ) from e
                
            if status_code == 429:
                retry_after = e.response.headers.get("Retry-After")
                if retry_after:
                    try:
                        retry_after = int(retry_after)
                    except ValueError:
                        retry_after = None
                        
                raise APIRateLimitError(
                    message="Football data API rate limit exceeded",
                    retry_after=retry_after,
                    details={"url": str(e.request.url)}
                ) from e
                
            # Generic HTTP error for other status codes
            raise APIConnectionError(
                message=f"HTTP {status_code} error",
                status_code=status_code,
                details={
                    "url": str(e.request.url),
                    "response": e.response.text
                }
            ) from e
            
    @async_retry(max_retries=3, initial_backoff=1.0, backoff_factor=2.0)
    async def _make_request(self, method: str, endpoint: str, resource_type: str, resource_id: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Make an API request with proper error handling and retry mechanism.
        
        Args:
            method: HTTP method (get, post, etc.)
            endpoint: API endpoint URL
            resource_type: Type of resource being requested (for error reporting)
            resource_id: ID of the resource (for error reporting)
            **kwargs: Additional arguments to pass to the httpx request
            
        Returns:
            JSON response data as dictionary
            
        Raises:
            APIConnectionError: For general connection issues
            APIAuthenticationError: For 401 errors
            APIResourceNotFoundError: For 404 errors
            APIRateLimitError: For 429 errors
        """
        # For performance tracking
        start_time = time.time()
        
        try:
            # Get the request method (get, post, etc.)
            request_method = getattr(self.client, method.lower())
            
            # Make the request
            response = await request_method(endpoint, **kwargs)
            response.raise_for_status()
            
            # Parse the response
            data = response.json()
            
            # Track performance metrics
            duration_ms = round((time.time() - start_time) * 1000)
            self.logger.info(
                f"API request: {method.upper()} {resource_type} successful",
                extra={
                    "duration_ms": duration_ms,
                    "status_code": response.status_code,
                    "endpoint": endpoint,
                    "resource_type": resource_type,
                    "resource_id": resource_id
                }
            )
            
            return data
            
        except httpx.HTTPError as e:
            # Log the failure duration
            duration_ms = round((time.time() - start_time) * 1000)
            self.logger.error(
                f"API request failed: {method.upper()} {resource_type}",
                extra={
                    "duration_ms": duration_ms,
                    "endpoint": endpoint,
                    "resource_type": resource_type,
                    "resource_id": resource_id,
                    "error": str(e)
                }
            )
            await self._handle_request_exception(e, resource_type, resource_id)
    
    async def get_areas(self, area_id=None):
        """Get available areas, optionally filtered by area_id"""
        if area_id:
            endpoint = f"{self.base_url}/areas/{area_id}"
        else:
            endpoint = f"{self.base_url}/areas"
        
        return await self._make_request(
            "get", 
            endpoint, 
            "area", 
            str(area_id) if area_id else None
        )
    
    async def get_competitions(self, areas=None):
        """Get available competitions (leagues), optionally filtered by areas"""
        filters = {}
        if areas:
            filters["areas"] = areas
        
        return await self._make_request(
            "get", 
            f"{self.base_url}/competitions", 
            "competitions",
            params=filters
        )
    
    async def get_competition(self, competition_id):
        """Get detailed information about a specific competition"""
        return await self._make_request(
            "get", 
            f"{self.base_url}/competitions/{competition_id}", 
            "competition", 
            str(competition_id)
        )
        
    async def get_standings(self, competition_id, season=None, matchday=None, date=None):
        """Get competition standings"""
        filters = {}
        if season:
            filters["season"] = season
        if matchday:
            filters["matchday"] = matchday
        if date:
            filters["date"] = date
            
        return await self._make_request(
            "get",
            f"{self.base_url}/competitions/{competition_id}/standings",
            "standings",
            str(competition_id),
            params=filters
        )
    
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
            
        return await self._make_request(
            "get",
            f"{self.base_url}/competitions/{competition_id}/matches",
            "competition_matches",
            str(competition_id),
            params=filters
        )
    
    async def get_competition_teams(self, competition_id, season=None):
        """Get teams for a specific competition"""
        filters = {}
        if season:
            filters["season"] = season
            
        return await self._make_request(
            "get",
            f"{self.base_url}/competitions/{competition_id}/teams",
            "competition_teams",
            str(competition_id),
            params=filters
        )
    
    async def get_top_scorers(self, competition_id, limit=10, season=None):
        """Get top scorers for a competition"""
        filters = {}
        if limit:
            filters["limit"] = limit
        if season:
            filters["season"] = season
            
        return await self._make_request(
            "get",
            f"{self.base_url}/competitions/{competition_id}/scorers",
            "top_scorers",
            str(competition_id),
            params=filters
        )
    
    async def get_team(self, team_id):
        """Get detailed information about a team"""
        return await self._make_request(
            "get",
            f"{self.base_url}/teams/{team_id}",
            "team",
            str(team_id)
        )
    
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
            
        return await self._make_request(
            "get",
            f"{self.base_url}/teams/{team_id}/matches",
            "team_matches",
            str(team_id),
            params=filters
        )
    
    async def get_person(self, person_id):
        """Get detailed information about a person (player or coach)"""
        return await self._make_request(
            "get",
            f"{self.base_url}/persons/{person_id}",
            "person",
            str(person_id)
        )
    
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
            
        return await self._make_request(
            "get",
            f"{self.base_url}/persons/{person_id}/matches",
            "person_matches",
            str(person_id),
            params=filters
        )
    
    async def get_match(self, match_id):
        """Get detailed information about a specific match"""
        return await self._make_request(
            "get",
            f"{self.base_url}/matches/{match_id}",
            "match",
            str(match_id)
        )
    
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
            
        return await self._make_request(
            "get",
            f"{self.base_url}/matches",
            "matches",
            params=filters
        )
    
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
            
        return await self._make_request(
            "get",
            f"{self.base_url}/matches/{match_id}/head2head",
            "head_to_head",
            str(match_id),
            params=filters
        )
    
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