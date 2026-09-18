from typing import Optional
from pydantic import BaseModel


class TeamStats(BaseModel):
    games_played: Optional[int] = None

    points_scored: Optional[int] = None
    points_per_game: Optional[float] = None

    rushing_yards: Optional[int] = None
    rushing_yards_per_game: Optional[float] = None

    passing_yards: Optional[int] = None
    passing_yards_per_game: Optional[float] = None

    total_yards: Optional[int] = None
    total_yards_per_game: Optional[float] = None

    points_allowed: Optional[int] = None
    points_allowed_per_game: Optional[float] = None

    rushing_yards_allowed: Optional[int] = None
    rushing_yards_allowed_per_game: Optional[float] = None

    passing_yards_allowed: Optional[int] = None
    passing_yards_allowed_per_game: Optional[float] = None

    total_yards_allowed: Optional[int] = None
    total_yards_allowed_per_game: Optional[float] = None

    turnovers: Optional[int] = None
    takeaways: Optional[int] = None

    field_goals_attempted: Optional[int] = None
    field_goals_made: Optional[int] = None
    field_goal_percentage: Optional[float] = None

    extra_points_attempted: Optional[int] = None
    extra_points_made: Optional[int] = None
    extra_point_percentage: Optional[float] = None

    rushing_touchdowns: Optional[int] = None
    passing_touchdowns: Optional[int] = None
    defensive_touchdowns: Optional[int] = None
    special_teams_touchdowns: Optional[int] = None

class Team(BaseModel):
    id: int
    name: str
    conference: str
    wins: int
    losses: int
    stats: TeamStats

class FantasyGameStats(BaseModel):
    espn_team_id: str
    team_name: str
    event_id: str

    passing_yards: Optional[int] = None
    passing_touchdowns: Optional[int] = None
    interceptions_thrown: Optional[int] = None

    rushing_yards: Optional[int] = None
    rushing_touchdowns: Optional[int] = None
    rushing_fumbles_lost: Optional[int] = None

    receiving_yards: Optional[int] = None
    receiving_touchdowns: Optional[int] = None
    receiving_fumbles_lost: Optional[int] = None

    points_allowed: Optional[int] = None
    yards_allowed: Optional[int] = None
    defensive_interceptions: Optional[int] = None
    defensive_fumble_recoveries: Optional[int] = None
    defensive_touchdowns: Optional[int] = None
    sacks: Optional[float] = None
    safeties: Optional[int] = None

    field_goals_made: Optional[int] = None
    field_goals_attempted: Optional[int] = None
    made_field_goal_distances: Optional[list[int]] = None

    extra_points_made: Optional[int] = None
    extra_points_attempted: Optional[int] = None

    special_teams_touchdowns: Optional[int] = None
    blocked_kicks: Optional[int] = None