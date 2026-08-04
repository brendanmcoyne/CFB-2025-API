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

class Team(BaseModel):
    id: int
    name: str
    conference: str
    wins: int
    losses: int
    stats: TeamStats