from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from offensive_stats import offensive_stats
from defensive_stats import defensive_stats
from special_teams_stats import special_teams_stats
from models import Team, TeamStats, FantasyGameStats
from teams import teams
from scoring import scoring

import httpx 
import re

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
        "https://fantasy-college-football.vercel.app",
        "https://fantasy-college-football.app",
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

@app.get("/espn/test/{event_id}")
async def test_espn_game(event_id: str):
    url = (
        "https://site.api.espn.com/apis/site/v2/"
        "sports/football/college-football/summary"
    )

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(
                url,
                params={"event": event_id},
            )
            response.raise_for_status()
            data = response.json()

    except httpx.HTTPError as error:
        raise HTTPException(
            status_code=502,
            detail=f"Could not fetch ESPN game: {error}",
        ) from error

    return {
        "header": data.get("header"),
        "boxscore": data.get("boxscore"),
        "plays": data.get("plays"),
        "scoringPlays": data.get("scoringPlays"),
    }

@app.get("/espn/plays/{event_id}")
async def test_espn_plays(event_id: str):
    url = (
        "https://site.api.espn.com/apis/site/v2/"
        "sports/football/college-football/playbyplay"
    )

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(
                url,
                params={"event": event_id},
            )
            response.raise_for_status()
            data = response.json()

    except httpx.HTTPError as error:
        raise HTTPException(
            status_code=502,
            detail=f"Could not fetch ESPN play-by-play: {error}",
        ) from error

    return {
        "event_id": event_id,
        "data": data,
    }

@app.get("/espn/inspect/{event_id}")
async def inspect_espn_game(event_id: str):
    url = (
        "https://site.api.espn.com/apis/site/v2/"
        "sports/football/college-football/summary"
    )

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(url, params={"event": event_id})
            response.raise_for_status()
            data = response.json()
    except (httpx.HTTPError, ValueError) as error:
        raise HTTPException(
            status_code=502,
            detail=f"Could not inspect ESPN game: {error}",
        ) from error

    plays = data.get("plays")
    scoring_plays = data.get("scoringPlays")

    return {
        "event_id": event_id,
        "top_level_keys": list(data.keys()),
        "plays_type": type(plays).__name__,
        "plays_count": len(plays) if isinstance(plays, list) else None,
        "scoring_plays_count": (
            len(scoring_plays)
            if isinstance(scoring_plays, list)
            else None
        ),
        "sample_play": plays[0] if isinstance(plays, list) and plays else None,
        "sample_scoring_play": (
            scoring_plays[0]
            if isinstance(scoring_plays, list) and scoring_plays
            else None
        ),
    }

@app.get("/espn/scoring-plays/{event_id}")
async def get_espn_scoring_plays(event_id: str):
    url = (
        "https://site.api.espn.com/apis/site/v2/"
        "sports/football/college-football/summary"
    )

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(url, params={"event": event_id})
            response.raise_for_status()
            data = response.json()
    except (httpx.HTTPError, ValueError) as error:
        raise HTTPException(
            status_code=502,
            detail=f"Could not fetch ESPN game: {error}",
        ) from error

    return {
        "event_id": event_id,
        "scoring_plays": [
            {
                "type": play.get("type", {}).get("text"),
                "text": play.get("text"),
                "team_id": play.get("team", {}).get("id"),
                "away_score": play.get("awayScore"),
                "home_score": play.get("homeScore"),
            }
            for play in data.get("scoringPlays", [])
        ],
    }

@app.get("/espn/scoreboard")
async def get_espn_scoreboard(date: str = Query(..., pattern=r"^\d{8}$")):
    url = (
        "https://site.api.espn.com/apis/site/v2/"
        "sports/football/college-football/scoreboard"
    )

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(
            url,
            params={
                "dates": date,
                "groups": 80,
                "limit": 500,
            },
        )
            response.raise_for_status()
            data = response.json()
    except (httpx.HTTPError, ValueError) as error:
        raise HTTPException(
            status_code=502,
            detail=f"Could not fetch ESPN scoreboard: {error}",
        ) from error

    games = []

    for event in data.get("events", []):
        competition = (event.get("competitions") or [{}])[0]
        competitors = competition.get("competitors", [])

        games.append({
            "event_id": event.get("id"),
            "name": event.get("name"),
            "start_time": event.get("date"),
            "status": event.get("status", {}).get("type", {}).get("name"),
            "teams": [
                {
                    "espn_team_id": entry.get("team", {}).get("id"),
                    "name": entry.get("team", {}).get("displayName"),
                    "home_away": entry.get("homeAway"),
                    "score": entry.get("score"),
                }
                for entry in competitors
            ],
        })

    return {"date": date, "games": games}

def player_stat(player_box: dict, category_name: str, *possible_keys: str):
    """Read a team total from an ESPN player-stat category."""
    category = next(
        (
            item
            for item in player_box.get("statistics", [])
            if item.get("name") == category_name
        ),
        None,
    )

    if category is None:
        return None

    keys = category.get("keys", [])
    totals = category.get("totals", [])

    for key in possible_keys:
        if key not in keys:
            continue

        index = keys.index(key)

        if index >= len(totals):
            continue

        try:
            return float(totals[index])
        except (TypeError, ValueError):
            continue

    return None


def team_stat(team_box: dict, *possible_names: str):
    """Read a statistic from ESPN's team box score."""
    for stat in team_box.get("statistics", []):
        if stat.get("name") not in possible_names:
            continue

        try:
            return float(stat["displayValue"].replace(",", ""))
        except (KeyError, AttributeError, TypeError, ValueError):
            continue

    return None


def made_attempted(player_box: dict, category_name: str, *possible_keys: str):
    """Parse ESPN kicking totals such as '2/3'."""
    category = next(
        (
            item
            for item in player_box.get("statistics", [])
            if item.get("name") == category_name
        ),
        None,
    )

    if category is None:
        return None, None

    keys = category.get("keys", [])
    totals = category.get("totals", [])

    for key in possible_keys:
        if key not in keys:
            continue

        index = keys.index(key)

        if index >= len(totals):
            continue

        match = re.fullmatch(
            r"\s*(\d+)\s*/\s*(\d+)\s*",
            str(totals[index]),
        )

        if match:
            return int(match.group(1)), int(match.group(2))

    return None, None


def as_int(value):
    return int(value) if value is not None else None


def classify_lost_fumbles(data: dict):
    counts = {}
    unclassified = set()
    seen_play_ids = set()

    for drive in (data.get("drives") or {}).get("previous", []):
        for play in drive.get("plays", []):
            if play.get("type", {}).get("text") != "Fumble Recovery (Opponent)":
                continue

            play_id = play.get("id")
            if play_id is not None and play_id in seen_play_ids:
                continue
            if play_id is not None:
                seen_play_ids.add(play_id)

            offense = next(
                (
                    participant
                    for participant in play.get("teamParticipants", [])
                    if participant.get("type") == "offense"
                ),
                None,
            )

            if offense is None:
                continue

            team_id = str(offense["id"])
            counts.setdefault(team_id, {"rushing": 0, "receiving": 0})

            text = play.get("text", "").lower()

            if "pass complete" in text and "caught" in text:
                counts[team_id]["receiving"] += 1
            elif re.search(r"\b(rush|rushed|rushing|run|ran)\b", text):
                counts[team_id]["rushing"] += 1
            else:
                unclassified.add(team_id)

    return counts, unclassified

@app.get(
    "/espn/fantasy-game/{event_id}",
    response_model=List[FantasyGameStats],
)
async def get_espn_fantasy_game(event_id: str):
    url = (
        "https://site.api.espn.com/apis/site/v2/"
        "sports/football/college-football/summary"
    )

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(
                url,
                params={"event": event_id},
            )
            response.raise_for_status()
            data = response.json()
    except (httpx.HTTPError, ValueError) as error:
        raise HTTPException(
            status_code=502,
            detail=f"Could not fetch ESPN game: {error}",
        ) from error

    competitions = data.get("header", {}).get("competitions", [])

    if not competitions:
        raise HTTPException(
            status_code=502,
            detail="ESPN did not return a game competition.",
        )

    competition = competitions[0]


    competitors = competition.get("competitors", [])
    team_boxes = data.get("boxscore", {}).get("teams", [])
    player_boxes = data.get("boxscore", {}).get("players", [])

    competitors_by_id = {
        str(entry["team"]["id"]): entry
        for entry in competitors
    }
    team_boxes_by_id = {
        str(entry["team"]["id"]): entry
        for entry in team_boxes
    }
    player_boxes_by_id = {
        str(entry["team"]["id"]): entry
        for entry in player_boxes
    }

    if (
        len(competitors_by_id) != 2
        or len(team_boxes_by_id) != 2
        or len(player_boxes_by_id) != 2
    ):
        raise HTTPException(
            status_code=502,
            detail="ESPN did not return a complete two-team box score.",
        )

    results = []

    fumble_counts, unclassified_fumble_teams = classify_lost_fumbles(data)

    for team_id, team_box in team_boxes_by_id.items():
        opponent_id = next(
            other_id
            for other_id in team_boxes_by_id
            if other_id != team_id
        )

        if (
            team_id not in competitors_by_id
            or opponent_id not in competitors_by_id
            or team_id not in player_boxes_by_id
        ):
            raise HTTPException(
                status_code=502,
                detail="Could not match ESPN team IDs.",
            )

        player_box = player_boxes_by_id[team_id]
        opponent_box = team_boxes_by_id[opponent_id]
        opponent_player_box = player_boxes_by_id[opponent_id]

        team_fumbles_lost = as_int(team_stat(team_box, "fumblesLost"))
        rushing_fumbles_lost = None
        receiving_fumbles_lost = None

        if team_fumbles_lost == 0:
            rushing_fumbles_lost = 0
            receiving_fumbles_lost = 0

        elif team_fumbles_lost is not None:
            counts = fumble_counts.get(
                team_id,
                {"rushing": 0, "receiving": 0},
            )

            classified_total = counts["rushing"] + counts["receiving"]

            if (
                team_id not in unclassified_fumble_teams
                and classified_total == team_fumbles_lost
            ):
                
                rushing_fumbles_lost = counts["rushing"]
                receiving_fumbles_lost = counts["receiving"]

        passing_yards = as_int(
            player_stat(player_box, "passing", "passingYards")
        )
        passing_tds = as_int(
            player_stat(player_box, "passing", "passingTouchdowns")
        )

        fg_made, fg_attempted = made_attempted(
            player_box,
            "kicking",
            "fieldGoalsMade/fieldGoalAttempts",
            "fieldGoalsMade/fieldGoalsAttempted",
        )

        xp_made, xp_attempted = made_attempted(
            player_box,
            "kicking",
            "extraPointsMade/extraPointAttempts",
            "extraPointsMade/extraPointsAttempted",
        )

        fg_distances = []

        for play in data.get("scoringPlays", []):
            if str(play.get("team", {}).get("id")) != team_id:
                continue

            if play.get("type", {}).get("text") != "Field Goal Good":
                continue

            match = re.search(
                r"(\d+)\s+Yd\s+Field\s+Goal",
                play.get("text", ""),
                flags=re.IGNORECASE,
            )

            if match:
                fg_distances.append(int(match.group(1)))

        # Only trust the distances if we found one for every made FG.
        verified_fg_distances = (
            fg_distances
            if fg_made is not None and len(fg_distances) == fg_made
            else None
        )

        opponent_score = competitors_by_id[opponent_id].get("score")

        results.append(
            FantasyGameStats(
                espn_team_id=team_id,
                team_name=team_box["team"]["displayName"],
                event_id=event_id,

                # PASSING
                passing_yards=passing_yards,
                passing_touchdowns=passing_tds,
                interceptions_thrown=as_int(player_stat( player_box, "passing", "interceptions", "passingInterceptions")),

                # RUSHING
                rushing_yards=as_int(player_stat( player_box, "rushing", "rushingYards" )),
                rushing_touchdowns=as_int(player_stat( player_box, "rushing", "rushingTouchdowns" )),
                rushing_fumbles_lost=rushing_fumbles_lost,


                # RECEIVING
                receiving_yards=passing_yards,
                receiving_touchdowns=passing_tds,
                receiving_fumbles_lost=receiving_fumbles_lost,

                # DEFENSE
                points_allowed=(
                    int(opponent_score)
                    if opponent_score is not None
                    else None
                ),
                yards_allowed=as_int(team_stat( opponent_box, "totalYards" )),
                defensive_interceptions=as_int(player_stat( opponent_player_box, "passing", "interceptions", "passingInterceptions" )),
                sacks=player_stat( player_box, "defensive", "sacks" ),

                field_goals_made=fg_made,
                field_goals_attempted=fg_attempted,
                made_field_goal_distances=verified_fg_distances,
                extra_points_made=xp_made,
                extra_points_attempted=xp_attempted,

                defensive_fumble_recoveries=None,
                defensive_touchdowns=None,
                safeties=None,
                special_teams_touchdowns=None,
                blocked_kicks=None,
            )
        )

    return results

@app.get("/espn/inspect-fumbles/{event_id}")
async def inspect_espn_fumbles(event_id: str):
    url = (
        "https://site.api.espn.com/apis/site/v2/"
        "sports/football/college-football/summary"
    )

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(url, params={"event": event_id})
            response.raise_for_status()
            data = response.json()
    except (httpx.HTTPError, ValueError) as error:
        raise HTTPException(
            status_code=502,
            detail=f"Could not fetch ESPN game: {error}",
        ) from error

    return {
        "teams": [
            {
                "team": entry.get("team", {}).get("displayName"),
                "fumble_stats": [
                    stat
                    for stat in entry.get("statistics", [])
                    if "fumbl" in str(stat).lower()
                ],
            }
            for entry in data.get("boxscore", {}).get("teams", [])
        ],
        "players": [
            {
                "team": entry.get("team", {}).get("displayName"),
                "fumble_categories": [
                    category
                    for category in entry.get("statistics", [])
                    if "fumbl" in str(category).lower()
                ],
            }
            for entry in data.get("boxscore", {}).get("players", [])
        ],
    }