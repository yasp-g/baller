from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from .sports import FootballAPI

app = FastAPI(title="Football Bot API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Specify your frontend URLs in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency for API client
async def get_football_api():
    api = FootballAPI()
    try:
        yield api
    finally:
        await api.close()

class LeagueResponse(BaseModel):
    leagues: List[Dict[str, Any]]

@app.get("/leagues", response_model=LeagueResponse)
async def get_leagues(country: Optional[str] = None, api: FootballAPI = Depends(get_football_api)):
    """Get available leagues, optionally filtered by country"""
    try:
        result = await api.get_leagues(country)
        return {"leagues": result.get("response", [])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/fixtures")
async def get_fixtures(
    league_id: Optional[int] = None,
    team_id: Optional[int] = None,
    date: Optional[str] = None,
    api: FootballAPI = Depends(get_football_api)
):
    """Get fixtures with various filters"""
    try:
        result = await api.get_fixtures(league_id, team_id, date)
        return {"fixtures": result.get("response", [])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/standings/{league_id}")
async def get_standings(
    league_id: int,
    season: Optional[int] = None,
    api: FootballAPI = Depends(get_football_api)
):
    """Get standings for a specific league"""
    try:
        result = await api.get_standings(league_id, season)
        return {"standings": result.get("response", [])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))