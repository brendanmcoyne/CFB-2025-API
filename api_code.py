from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from offensive_stats import offensive_stats
from defensive_stats import defensive_stats
from special_teams_stats import special_teams_stats
from models import Team, TeamStats
from teams import teams
from scoring import scoring

app = FastAPI(
    title="College Football Stats 2025 API",
    description="Team and season statistics for college football.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for team in teams.values():
    offense = offensive_stats.get(team.name, {})
    defense = defensive_stats.get(team.name, {})
    special = special_teams_stats.get(team.name, {})
    score = scoring.get(team.name, {})

    team.stats = team.stats.model_copy(
        update={
            **offense,
            **defense,
            **special,
            **score,
        }
    )
    
@app.get("/")
def home():
    return {
        "message": "College Football Statistics API is running",
        "documentation": "/docs"
    }


@app.get("/teams", response_model=List[Team])
def get_teams(
    conference: Optional[str] = Query(
        default=None,
        description="Filter teams by conference",
    )
):
    results = list(teams.values())

    if conference is not None:
        results = [
            team
            for team in results
            if team.conference.lower() == conference.lower()
        ]

    return results


@app.get("/teams/{team_id}", response_model=Team)
def get_team(team_id: int):
    team = teams.get(team_id)

    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")

    return team

@app.get("/conferences/{conference}/teams", response_model=List[Team])
def get_conference_teams(conference: str):
    results = [
        team
        for team in teams.values()
        if team.conference.lower() == conference.lower()
    ]

    if not results:
        raise HTTPException(status_code=404, detail="No teams found for that conference")

    return results


@app.get("/rankings/{stat_name}", response_model=List[Team])
def rank_teams(stat_name: str,descending: bool = True):
    valid_stats = TeamStats.model_fields.keys()

    if stat_name not in valid_stats:
        raise HTTPException(status_code=400, detail={"message": "Invalid statistic","valid_statistics": list(valid_stats)})

    ranked_teams = [
        team
        for team in teams.values()
        if getattr(team.stats, stat_name) is not None
    ]

    return sorted(
        ranked_teams,
        key=lambda team: getattr(team.stats, stat_name),
        reverse=descending
    )


@app.post("/teams", response_model=Team, status_code=201)
def create_team(team: Team):
    if team.id in teams:
        raise HTTPException(status_code=409,detail="A team with that ID already exists")

    for existing_team in teams.values():
        if existing_team.name.lower() == team.name.lower():
            raise HTTPException(status_code=409,detail="A team with that name already exists")

    teams[team.id] = team
    return team


@app.put("/teams/{team_id}", response_model=Team)
def update_team(team_id: int, updated_team: Team):
    if team_id not in teams:
        raise HTTPException(status_code=404, detail="Team not found")

    if updated_team.id != team_id:
        raise HTTPException(status_code=400,detail="The team ID in the URL must match the request body")

    teams[team_id] = updated_team
    return updated_team


@app.delete("/teams/{team_id}")
def delete_team(team_id: int):
    team = teams.pop(team_id, None)

    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")

    return {
        "message": "Team deleted",
        "team": team,
    }