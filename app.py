print("🚨 APP.PY RELOADED 🚨")


from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
from typing import Optional, List
from contextlib import asynccontextmanager
from datetime import date




from db import (
    init_db,
    create_league,
    create_club,
    create_player,
    get_players_by_league,
    create_court_assignment,
    create_match,
    add_player_to_match,
    record_match_score,
    get_court_assignment,
    swap_players,
    get_player_dashboard,
    generate_court_assignment,
    record_match_score,
    get_owner_dashboard,
    owner_record_match_score,
    get_player_rating_history,
    override_match_score,
    force_complete_match,
    get_court_assignment_scores


)


class LeagueCreate(BaseModel):
    name: str
    owner_user_id: int

class ClubCreate(BaseModel):
    league_id: int
    name: str

class PlayerCreate(BaseModel):
    league_id: int
    first_name: str
    last_name: str
    rating: float
    gender: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    club_id: Optional[int] = None

class CourtAssignmentCreate(BaseModel):
    league_id: int
    location_club_id: int
    assignment_type: str   # straight | random | blended
    num_courts: int
    is_doubles: bool

class MatchScoreCreate(BaseModel):
    games_team_a: int
    games_team_b: int
    display_score: Optional[str] = None

class SwapPlayers(BaseModel):
    player_id_1: int
    player_id_2: int


class MatchScoreCreate(BaseModel):
    games_team_a: int
    games_team_b: int
    display_score: Optional[str] = None

class OwnerMatchScoreCreate(BaseModel):
    games_team_a: int
    games_team_b: int
    display_score: Optional[str] = None

class MatchOverrideCreate(BaseModel):
    games_team_a: int
    games_team_b: int
    display_score: Optional[str] = None
    reason: Optional[str] = None
    owner_user_id: int

class ForceCompletePayload(BaseModel):
    reason: Optional[str] = None



@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    yield
    # Shutdown (nothing needed yet)

app = FastAPI(
    title="Tennis League App",
    lifespan=lifespan,
)


# ---------- Health ----------

@app.get("/")
def health_check():
    return {"status": "ok"}

# ---------- Leagues ----------

@app.post("/leagues")
def create_league_endpoint(payload: LeagueCreate = Body(...)):
    league_id = create_league(payload.name, payload.owner_user_id)
    return {"league_id": league_id}




# ---------- Clubs ----------

@app.post("/clubs")
def create_club_endpoint(payload: ClubCreate):
    club_id = create_club(payload.league_id, payload.name)
    return {"club_id": club_id}

# ---------- Players ----------

@app.post("/players")
def create_player_endpoint(payload: PlayerCreate):
    player_id = create_player(
        league_id=payload.league_id,
        first_name=payload.first_name,
        last_name=payload.last_name,
        gender=payload.gender,
        city=payload.city,
        state=payload.state,
        email=payload.email,
        phone=payload.phone,
        club_id=payload.club_id,
        self_reported_rating=payload.rating,
    )
    return {"player_id": player_id}



@app.get("/leagues/{league_id}/players")
def list_players_endpoint(league_id: int):
    return get_players_by_league(league_id)

# ---------- Court Assignments ----------


@app.post("/court-assignments")
def create_court_assignment_endpoint(payload: CourtAssignmentCreate):
    if payload.assignment_type not in {"straight", "random", "blended"}:
        raise HTTPException(status_code=400, detail="Invalid assignment type")

    assignment_id = create_court_assignment(
        league_id=payload.league_id,
        assignment_date=date.today().isoformat(),
        location_club_id=payload.location_club_id,
        num_courts=payload.num_courts,
        match_type="doubles" if payload.is_doubles else "singles",
        algorithm=payload.assignment_type,   # ← THIS IS THE MAPPING
        status="draft",
    )

    return {"court_assignment_id": assignment_id}


# ---------- Matches ----------

@app.post("/matches")
def create_match_endpoint(
    court_id: int,
    is_independent: bool = False,
):
    match_id = create_match(court_id, is_independent)
    return {"match_id": match_id}


@app.post("/matches/{match_id}/players")
def add_player_to_match_endpoint(
    match_id: int,
    player_id: int,
    team: str,
):
    try:
        add_player_to_match(match_id, player_id, team)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"status": "player added"}

# ---------- Scoring + Ratings ----------

@app.post("/matches/{match_id}/score")
def record_score_endpoint(
    match_id: int,
    payload: MatchScoreCreate,
):
    try:
        record_match_score(
            match_id,
            payload.games_team_a,
            payload.games_team_b,
            payload.display_score,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"status": "score recorded"}


@app.get("/court-assignments/{court_assignment_id}")
def get_court_assignment_endpoint(court_assignment_id: int):
    try:
        return get_court_assignment(court_assignment_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/court-assignments/{court_assignment_id}/swap")
def swap_players_endpoint(
    court_assignment_id: int,
    payload: SwapPlayers,
):
    try:
        swap_players(
            court_assignment_id,
            payload.player_id_1,
            payload.player_id_2,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"status": "players swapped"}



from db import publish_court_assignment

@app.post("/court-assignments/{court_assignment_id}/publish")
def publish_court_assignment_endpoint(court_assignment_id: int):
    try:
        match_ids = publish_court_assignment(court_assignment_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "status": "published",
        "match_ids": match_ids,
    }


@app.get("/players/{player_id}/dashboard")
def player_dashboard_endpoint(player_id: int):
    try:
        return get_player_dashboard(player_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/owners/{owner_user_id}/dashboard")
def owner_dashboard_endpoint(owner_user_id: int):
    return get_owner_dashboard(owner_user_id)

@app.get("/players/{player_id}/rating-history")
def player_rating_history_endpoint(player_id: int):
    return get_player_rating_history(player_id)



@app.post("/court-assignments/{court_assignment_id}/generate")
def generate_court_assignment_endpoint(court_assignment_id: int):
    generate_court_assignment(court_assignment_id)
    return {"status": "generated"}


@app.post("/matches/{match_id}/score")
def record_match_score_endpoint(
    match_id: int,
    payload: MatchScoreCreate,
):
    record_match_score(
        match_id,
        payload.games_team_a,
        payload.games_team_b,
        payload.display_score,
    )
    return {"status": "completed"}

@app.post("/matches/{match_id}/score")
def score_match_endpoint(match_id: int, payload: MatchScoreCreate):
    result = record_match_score(
        match_id=match_id,
        games_team_a=payload.games_team_a,
        games_team_b=payload.games_team_b,
        display_score=payload.display_score,
    )
    return {
        "status": "scored",
        **result,
    }

@app.post("/owners/{owner_user_id}/matches/{match_id}/score")
def owner_score_match_endpoint(
    owner_user_id: int,
    match_id: int,
    payload: OwnerMatchScoreCreate,
):
    return owner_record_match_score(
        owner_user_id=owner_user_id,
        match_id=match_id,
        games_team_a=payload.games_team_a,
        games_team_b=payload.games_team_b,
        display_score=payload.display_score,
    )

@app.post("/matches/{match_id}/override-score")
def override_score_endpoint(
    match_id: int,
    payload: MatchOverrideCreate,
):
    override_match_score(
        match_id=match_id,
        games_team_a=payload.games_team_a,
        games_team_b=payload.games_team_b,
        display_score=payload.display_score,
        overridden_by=payload.owner_user_id,
        reason=payload.reason,
    )
    return {"status": "overridden"}

@app.post("/matches/{match_id}/force-complete")
def force_complete_endpoint(
    match_id: int,
    payload: ForceCompletePayload,
):
    force_complete_match(match_id, payload.reason)
    return {"status": "completed_without_score"}

@app.get("/court-assignments/{court_assignment_id}/scores")
def get_court_assignment_scores_endpoint(court_assignment_id: int):
    try:
        return get_court_assignment_scores(court_assignment_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

