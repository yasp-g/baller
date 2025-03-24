import pytest
import respx
from httpx import Response
import json
from datetime import date, timedelta
from src.api.sports import FootballAPI

@pytest.mark.asyncio
class TestFootballAPI:
    """Test suite for the FootballAPI class"""
    
    @respx.mock
    async def test_get_standings(self, sample_standings_data):
        """Test retrieving standings from the API"""
        # Mock the API response
        competition_id = 2002  # Bundesliga
        respx.get(f"https://api.football-data.org/v4/competitions/{competition_id}/standings").mock(
            return_value=Response(200, json=sample_standings_data)
        )
        
        # Call the API
        api = FootballAPI()
        result = await api.get_standings(competition_id=competition_id)
        await api.close()
        
        # Verify result
        assert result.get("competition", {}).get("name") == "Bundesliga"
        assert len(result.get("standings", [])[0].get("table")) == 2
        assert result.get("standings", [])[0].get("table")[0].get("team").get("name") == "FC Bayern München"
    
    @respx.mock
    async def test_get_matches(self, sample_matches_data):
        """Test retrieving matches from the API"""
        # Mock the API response
        url = "https://api.football-data.org/v4/matches"
        respx.get(url).mock(return_value=Response(200, json=sample_matches_data))
        
        # Call the API
        api = FootballAPI()
        result = await api.get_matches()
        await api.close()
        
        # Verify result
        assert len(result.get("matches", [])) == 2
        assert result.get("matches")[0].get("homeTeam").get("name") == "Bayer 04 Leverkusen"
        assert result.get("resultSet", {}).get("count") == 2
    
    @respx.mock
    async def test_get_competition(self):
        """Test retrieving a specific competition"""
        # Mock the API response
        competition_id = 2002  # Bundesliga
        mock_data = {
            "id": 2002,
            "name": "Bundesliga",
            "code": "BL1",
            "area": {"name": "Germany"},
            "currentSeason": {"startDate": "2024-08-23", "endDate": "2025-05-17"}
        }
        respx.get(f"https://api.football-data.org/v4/competitions/{competition_id}").mock(
            return_value=Response(200, json=mock_data)
        )
        
        # Call the API
        api = FootballAPI()
        result = await api.get_competition(competition_id=competition_id)
        await api.close()
        
        # Verify result
        assert result.get("name") == "Bundesliga"
        assert result.get("area").get("name") == "Germany"
        assert result.get("currentSeason").get("startDate") == "2024-08-23"
    
    @respx.mock
    async def test_get_competition_teams(self):
        """Test retrieving teams for a competition"""
        # Mock the API response
        competition_id = 2002  # Bundesliga
        mock_data = {
            "competition": {"id": 2002, "name": "Bundesliga"},
            "count": 18,
            "teams": [
                {"id": 5, "name": "FC Bayern München", "shortName": "Bayern", "tla": "FCB"},
                {"id": 3, "name": "Bayer 04 Leverkusen", "shortName": "Leverkusen", "tla": "B04"}
            ]
        }
        respx.get(f"https://api.football-data.org/v4/competitions/{competition_id}/teams").mock(
            return_value=Response(200, json=mock_data)
        )
        
        # Call the API
        api = FootballAPI()
        result = await api.get_competition_teams(competition_id=competition_id)
        await api.close()
        
        # Verify result
        assert result.get("competition").get("name") == "Bundesliga"
        assert len(result.get("teams")) == 2
        assert result.get("teams")[0].get("name") == "FC Bayern München"
    
    @respx.mock
    async def test_api_error_handling(self):
        """Test that API errors are properly handled"""
        # Mock an error response
        url = "https://api.football-data.org/v4/competitions/999999"
        respx.get(url).mock(return_value=Response(404, json={"message": "Resource not found"}))
        
        # Call the API with invalid ID
        api = FootballAPI()
        with pytest.raises(Exception) as exc_info:
            await api.get_competition(competition_id=999999)
        await api.close()
        
        # Verify exception contains error details
        assert "404" in str(exc_info.value)
    
    @respx.mock
    async def test_get_team(self):
        """Test retrieving team details"""
        # Mock the API response
        team_id = 5  # Bayern Munich
        mock_data = {
            "id": 5,
            "name": "FC Bayern München",
            "shortName": "Bayern",
            "tla": "FCB",
            "founded": 1900,
            "venue": "Allianz Arena",
            "website": "http://www.fcbayern.de"
        }
        respx.get(f"https://api.football-data.org/v4/teams/{team_id}").mock(
            return_value=Response(200, json=mock_data)
        )
        
        # Call the API
        api = FootballAPI()
        result = await api.get_team(team_id=team_id)
        await api.close()
        
        # Verify result
        assert result.get("name") == "FC Bayern München"
        assert result.get("founded") == 1900
        assert result.get("venue") == "Allianz Arena"