import sqlite3
from pathlib import Path
from typing import Optional
from fastapi import HTTPException
import random
from rating import rating_update
from contextlib import contextmanager

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "tennis_app.db"
print("USING DATABASE FILE:", DB_PATH.resolve())


SCHEMA_PATH = Path("schema.sql")

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # access columns by name
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError("schema.sql not found")

    with get_db() as conn:
        with open(SCHEMA_PATH, "r") as f:
            conn.executescript(f.read())

def create_league(name: str, owner_user_id: int) -> int:
    with get_db() as conn:
        cur = conn.execute(
            """
            INSERT INTO leagues (name, owner_user_id)
            VALUES (?, ?)
            """,
            (name, owner_user_id),
        )
        return cur.lastrowid

def create_club(league_id: int, name: str) -> int:
    with get_db() as conn:
        cur = conn.execute(
            """
            INSERT INTO clubs (league_id, name)
            VALUES (?, ?)
            """,
            (league_id, name),
        )
        return cur.lastrowid


def get_clubs_for_league(league_id: int):
    with get_db() as conn:
        cur = conn.execute(
            "SELECT * FROM clubs WHERE league_id = ?",
            (league_id,),
        )
        return cur.fetchall()

def create_player(
    league_id: int,
    first_name: str,
    last_name: str,
    gender: Optional[str],
    city: Optional[str],
    state: Optional[str],
    email: Optional[str],
    phone: Optional[str],
    club_id: Optional[int],
    self_reported_rating: float,
):
    with get_db() as conn:
        cur = conn.execute(
            """
            INSERT INTO players (
                league_id,
                first_name,
                last_name,
                gender,
                city,
                state,
                email,
                phone,
                club_id,
                self_reported_rating,
                current_rating
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                league_id,
                first_name,
                last_name,
                gender,
                city,
                state,
                email,
                phone,
                club_id,
                self_reported_rating,
                self_reported_rating,
            ),
        )
        return cur.lastrowid

def get_players_by_league(league_id: int):
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT
                id,
                first_name,
                last_name,
                current_rating,
                matches_played,
                gender,
                city,
                state,
                email,
                phone,
                club_id
            FROM players
            WHERE league_id = ?
            ORDER BY current_rating DESC
            """,
            (league_id,),
        ).fetchall()

        return [dict(row) for row in rows]


def get_players_for_league(league_id: int):
    with get_db() as conn:
        cur = conn.execute(
            "SELECT * FROM players WHERE league_id = ?",
            (league_id,),
        )
        return cur.fetchall()

def create_court_assignment(
    league_id: int,
    assignment_date: str,
    location_club_id: int,
    num_courts: int,
    match_type: str,
    algorithm: str,
    status: str = "draft",
) -> int:
    with get_db() as conn:
        cur = conn.execute(
            """
            INSERT INTO court_assignments (
                league_id,
                assignment_date,
                location_club_id,
                num_courts,
                match_type,
                algorithm,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                league_id,
                assignment_date,
                location_club_id,
                num_courts,
                match_type,
                algorithm,
                status,
            ),
        )
        return cur.lastrowid

def create_court(court_assignment_id: int, court_number: int) -> int:
    with get_db() as conn:
        cur = conn.execute(
            """
            INSERT INTO courts (court_assignment_id, court_number)
            VALUES (?, ?)
            """,
            (court_assignment_id, court_number),
        )
        return cur.lastrowid

def create_match(court_id: int, is_independent: bool = False) -> int:
    with get_db() as conn:
        cur = conn.execute(
            """
            INSERT INTO matches (
                court_id,
                games_team_a,
                games_team_b,
                is_independent,
                is_completed
            )
            VALUES (?, 0, 0, ?, 0)
            """,
            (court_id, int(is_independent)),
        )
        return cur.lastrowid

def add_player_to_match(match_id: int, player_id: int, team: str):
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO match_players (match_id, player_id, team)
            VALUES (?, ?, ?)
            """,
            (match_id, player_id, team),
        )


def get_match_with_players(match_id: int):
    with get_db() as conn:
        match = conn.execute(
            """
            SELECT *
            FROM matches
            WHERE id = ?
            """,
            (match_id,),
        ).fetchone()

        if match is None:
            raise ValueError("Match not found")

        rows = conn.execute(
            """
            SELECT
                mp.team,
                p.id AS player_id,
                p.current_rating
            FROM match_players mp
            JOIN players p ON mp.player_id = p.id
            WHERE mp.match_id = ?
            """,
            (match_id,),
        ).fetchall()

        team_a = []
        team_b = []

        for row in rows:
            team = row["team"].strip().upper()

            if team == "A":
                team_a.append(row)
            elif team == "B":
                team_b.append(row)

        return match, team_a, team_b


def get_court_assignment(court_assignment_id: int):
    with get_db() as conn:
        assignment = conn.execute(
            """
            SELECT *
            FROM court_assignments
            WHERE id = ?
            """,
            (court_assignment_id,),
        ).fetchone()

        if assignment is None:
            raise ValueError("Court assignment not found")

        courts = conn.execute(
            """
            SELECT *
            FROM courts
            WHERE court_assignment_id = ?
            ORDER BY court_number
            """,
            (court_assignment_id,),
        ).fetchall()

        result = []

        for court in courts:
            players = conn.execute(
                """
                SELECT
                    cp.team,
                    p.id AS player_id,
                    p.first_name,
                    p.last_name,
                    p.current_rating
                FROM court_players cp
                JOIN players p ON cp.player_id = p.id
                WHERE cp.court_id = ?
                """,
                (court["id"],),
            ).fetchall()

            team_a = []
            team_b = []

            for row in players:
                player = {
                    "player_id": row["player_id"],
                    "name": f"{row['first_name']} {row['last_name']}",
                    "rating": row["current_rating"],
                }
                if row["team"] == "A":
                    team_a.append(player)
                else:
                    team_b.append(player)

            result.append(
                {
                    "court_id": court["id"],
                    "court_number": court["court_number"],
                    "team_a": team_a,
                    "team_b": team_b,
                }
            )

        return {
            "court_assignment_id": assignment["id"],
            "published": assignment["status"] == "published",
            "courts": result,
        }

def swap_players(
    court_assignment_id: int,
    player_id_1: int,
    player_id_2: int,
):
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT cp.id, cp.court_id
            FROM court_players cp
            JOIN courts c ON cp.court_id = c.id
            WHERE c.court_assignment_id = ?
              AND cp.player_id IN (?, ?)
            """,
            (court_assignment_id, player_id_1, player_id_2),
        ).fetchall()

        if len(rows) != 2:
            raise ValueError("Both players must be in this court assignment")

        cp1_id, cp2_id = rows[0]["id"], rows[1]["id"]

        conn.execute(
            """
            UPDATE court_players
            SET player_id = CASE
                WHEN id = ? THEN ?
                WHEN id = ? THEN ?
            END
            WHERE id IN (?, ?)
            """,
            (cp1_id, player_id_2, cp2_id, player_id_1, cp1_id, cp2_id),
        )

def publish_court_assignment(court_assignment_id: int):
    with get_db() as conn:

        # 1. Fetch assignment
        assignment = conn.execute(
            """
            SELECT id, status
            FROM court_assignments
            WHERE id = ?
            """,
            (court_assignment_id,),
        ).fetchone()

        if assignment is None:
            raise RuntimeError("Court assignment not found")

        if assignment["status"] == "published":
            raise RuntimeError("Court assignment already published")

        if assignment["status"] != "generated":
            raise RuntimeError(
                f"Cannot publish assignment in status '{assignment['status']}'"
            )

        # 2. Fetch courts
        courts = conn.execute(
            """
            SELECT id, court_number
            FROM courts
            WHERE court_assignment_id = ?
            ORDER BY court_number
            """,
            (court_assignment_id,),
        ).fetchall()

        if not courts:
            raise RuntimeError("No courts found to publish")

        created_match_ids = []

        # 3. Create matches + attach players
        for court in courts:

            # Create match
            cur = conn.execute(
                """
                INSERT INTO matches (
                    court_id,
                    is_independent,
                    completed,
                    is_rated
                )
                VALUES (?, 0, 0, 0)
                """,
                (court["id"],),
            )
            match_id = cur.lastrowid
            created_match_ids.append(match_id)

            # Attach players
            players = conn.execute(
                """
                SELECT player_id, team
                FROM court_players
                WHERE court_id = ?
                """,
                (court["id"],),
            ).fetchall()

            if not players:
                raise RuntimeError(
                    f"Court {court['court_number']} has no players"
                )

            for row in players:
                conn.execute(
                    """
                    INSERT INTO match_players (match_id, player_id, team)
                    VALUES (?, ?, ?)
                    """,
                    (match_id, row["player_id"], row["team"]),
                )

        # 4. Mark assignment as published
        conn.execute(
            """
            UPDATE court_assignments
            SET status = 'published'
            WHERE id = ?
            """,
            (court_assignment_id,),
        )

        return created_match_ids


    
def get_player_dashboard(player_id: int):
    with get_db() as conn:

        # 1. Player info
        player = conn.execute(
            """
            SELECT id, first_name, last_name, current_rating
            FROM players
            WHERE id = ?
            """,
            (player_id,),
        ).fetchone()

        if player is None:
            raise HTTPException(status_code=404, detail="Player not found")

        # 2. Fetch all match + player context
        rows = conn.execute(
            """
            SELECT
                m.id AS match_id,
                m.games_team_a,
                m.games_team_b,
                m.display_score,
                c.court_number,
                ca.assignment_date,
                mp.player_id,
                mp.team,
                p.first_name,
                p.last_name
            FROM match_players mp
            JOIN matches m ON m.id = mp.match_id
            JOIN players p ON p.id = mp.player_id
            JOIN courts c ON c.id = m.court_id
            JOIN court_assignments ca ON ca.id = c.court_assignment_id
            WHERE m.id IN (
                SELECT match_id
                FROM match_players
                WHERE player_id = ?
            )
            ORDER BY ca.assignment_date DESC, m.id
            """,
            (player_id,),
        ).fetchall()

        # 3. Rating history lookup
        rating_rows = conn.execute(
            """
            SELECT
                match_id,
                rating_before,
                rating_after
            FROM rating_history
            WHERE player_id = ?
            """,
            (player_id,),
        ).fetchall()

        rating_by_match = {
            r["match_id"]: r for r in rating_rows
        }

        matches = {}

        for row in rows:
            mid = row["match_id"]

            if mid not in matches:
                completed = (
                    row["games_team_a"] is not None
                    and row["games_team_b"] is not None
                )

                rating_change = None
                if completed and mid in rating_by_match:
                    rb = rating_by_match[mid]["rating_before"]
                    ra = rating_by_match[mid]["rating_after"]
                    rating_change = round(ra - rb, 3)

                matches[mid] = {
                    "match_id": mid,
                    "court_number": row["court_number"],
                    "assignment_date": row["assignment_date"],
                    "display_score": row["display_score"],
                    "completed": completed,
                    "rating_change": rating_change,
                    "partners": [],
                    "opponents": [],
                }

            # Skip self but capture team
            if row["player_id"] == player_id:
                player_team = row["team"]
                continue

            if row["team"] == player_team:
                matches[mid]["partners"].append(
                    f"{row['first_name']} {row['last_name']}"
                )
            else:
                matches[mid]["opponents"].append(
                    f"{row['first_name']} {row['last_name']}"
                )

        upcoming = []
        completed_matches = []

        for m in matches.values():
            if m["completed"]:
                completed_matches.append(m)
            else:
                upcoming.append(m)

        return {
            "player": {
                "id": player["id"],
                "name": f"{player['first_name']} {player['last_name']}",
                "current_rating": player["current_rating"],
            },
            "upcoming_matches": upcoming,
            "completed_matches": completed_matches,
        }


def get_owner_dashboard(owner_user_id: int):
    with get_db() as conn:

        # 1. League info
        league = conn.execute(
            """
            SELECT id, name
            FROM leagues
            WHERE owner_user_id = ?
            """,
            (owner_user_id,),
        ).fetchone()

        if league is None:
            raise ValueError("League not found for owner")

        league_id = league["id"]

        # 2. Stats
        player_count = conn.execute(
            """
            SELECT COUNT(*)
            FROM players
            WHERE league_id = ?
            """,
            (league_id,),
        ).fetchone()[0]

        active_assignments = conn.execute(
            """
            SELECT COUNT(*)
            FROM court_assignments
            WHERE league_id = ?
              AND status IN ('draft', 'generated', 'published')
            """,
            (league_id,),
        ).fetchone()[0]

        open_matches = conn.execute(
            """
            SELECT COUNT(*)
            FROM matches m
            JOIN courts c ON c.id = m.court_id
            JOIN court_assignments ca ON ca.id = c.court_assignment_id
            WHERE ca.league_id = ?
              AND m.completed = 0
            """,
            (league_id,),
        ).fetchone()[0]

        # 3. Court assignments
        assignments = conn.execute(
            """
            SELECT
                ca.id,
                ca.assignment_date,
                ca.status,
                ca.num_courts,
                cl.name AS location
            FROM court_assignments ca
            JOIN clubs cl ON cl.id = ca.location_club_id
            WHERE ca.league_id = ?
            ORDER BY ca.assignment_date DESC
            """,
            (league_id,),
        ).fetchall()

        # 4. Matches needing attention
        matches = conn.execute(
            """
            SELECT
                m.id AS match_id,
                ca.assignment_date,
                c.court_number,
                m.completed,
                m.is_rated
            FROM matches m
            JOIN courts c ON c.id = m.court_id
            JOIN court_assignments ca ON ca.id = c.court_assignment_id
            WHERE ca.league_id = ?
              AND m.completed = 0
            ORDER BY ca.assignment_date DESC
            """,
            (league_id,),
        ).fetchall()

        return {
            "league": {
                "id": league["id"],
                "name": league["name"],
            },
            "stats": {
                "players": player_count,
                "active_assignments": active_assignments,
                "open_matches": open_matches,
            },
            "court_assignments": [
                {
                    "id": a["id"],
                    "date": a["assignment_date"],
                    "location": a["location"],
                    "status": a["status"],
                    "num_courts": a["num_courts"],
                }
                for a in assignments
            ],
            "matches_needing_action": [
                {
                    "match_id": m["match_id"],
                    "assignment_date": m["assignment_date"],
                    "court_number": m["court_number"],
                    "completed": bool(m["completed"]),
                    "is_rated": bool(m["is_rated"]),
                }
                for m in matches
            ],
        }

def generate_court_assignment(court_assignment_id: int):
    with get_db() as conn:

        # 1. Fetch assignment
        assignment = conn.execute(
            """
            SELECT league_id, num_courts, match_type, algorithm, status
            FROM court_assignments
            WHERE id = ?
            """,
            (court_assignment_id,),
        ).fetchone()

        if assignment is None:
            raise RuntimeError("Court assignment not found")

        if assignment["status"] != "draft":
            raise RuntimeError(
                f"Cannot generate assignment in status '{assignment['status']}'"
            )

        num_courts = assignment["num_courts"]
        match_type = assignment["match_type"]
        algorithm = assignment["algorithm"]

        players_per_court = 4 if match_type == "doubles" else 2
        required_players = num_courts * players_per_court

        # 2. Fetch eligible players
        players = conn.execute(
            """
            SELECT id, current_rating, total_matches
            FROM players
            WHERE league_id = ?
            ORDER BY current_rating DESC, total_matches DESC
            """,
            (assignment["league_id"],),
        ).fetchall()

        if len(players) < required_players:
            raise RuntimeError("Not enough players to generate courts")

        selected_players = players[:required_players]

        # 3. Apply assignment algorithm
        ordered_ids = apply_assignment_algorithm(
            [p["id"] for p in selected_players],
            algorithm=algorithm,
        )

        # 4. Clear any previous generated data (safe because status=draft)
        conn.execute(
            """
            DELETE FROM court_players
            WHERE court_id IN (
                SELECT id FROM courts WHERE court_assignment_id = ?
            )
            """,
            (court_assignment_id,),
        )

        conn.execute(
            """
            DELETE FROM courts
            WHERE court_assignment_id = ?
            """,
            (court_assignment_id,),
        )

        # 5. Create courts + assign players
        idx = 0

        for court_number in range(1, num_courts + 1):
            cur = conn.execute(
                """
                INSERT INTO courts (court_assignment_id, court_number)
                VALUES (?, ?)
                """,
                (court_assignment_id, court_number),
            )
            court_id = cur.lastrowid

            court_players = ordered_ids[idx : idx + players_per_court]
            idx += players_per_court

            if match_type == "doubles":
                teams = ["A", "A", "B", "B"]
            else:
                teams = ["A", "B"]

            for pid, team in zip(court_players, teams):
                conn.execute(
                    """
                    INSERT INTO court_players (court_id, player_id, team)
                    VALUES (?, ?, ?)
                    """,
                    (court_id, pid, team),
                )

        # 6. Mark as generated
        conn.execute(
            """
            UPDATE court_assignments
            SET status = 'generated'
            WHERE id = ?
            """,
            (court_assignment_id,),
        )

def record_match_score(
    match_id: int,
    games_team_a: int,
    games_team_b: int,
    display_score: Optional[str] = None,
    *,
    finalize: bool = False,
    allow_override: bool = False,
):
    with get_db() as conn:

        match = conn.execute(
            "SELECT completed FROM matches WHERE id = ?",
            (match_id,),
        ).fetchone()

        if match is None:
            raise RuntimeError("Match not found")

        if match["completed"] and not allow_override:
            raise RuntimeError("Match already finalized")

        # Always save the score
        conn.execute(
            """
            UPDATE matches
            SET games_team_a = ?,
                games_team_b = ?,
                display_score = ?
            WHERE id = ?
            """,
            (games_team_a, games_team_b, display_score, match_id),
        )

        if finalize:
            conn.execute(
                "UPDATE matches SET completed = 1 WHERE id = ?",
                (match_id,),
            )

            # 🔑 THIS is where your EXISTING rating logic runs
            # whatever logic you already had that writes:
            # - rating_history
            # - players.current_rating




def owner_record_match_score(
    owner_user_id: int,
    match_id: int,
    games_team_a: int,
    games_team_b: int,
    display_score=None,
):
    with get_db() as conn:

        # Verify ownership
        row = conn.execute(
            """
            SELECT
                m.id,
                m.games_team_a,
                l.owner_user_id
            FROM matches m
            JOIN courts c ON c.id = m.court_id
            JOIN court_assignments ca ON ca.id = c.court_assignment_id
            JOIN leagues l ON l.id = ca.league_id
            WHERE m.id = ?
            """,
            (match_id,),
        ).fetchone()

        if row is None:
            raise HTTPException(status_code=404, detail="Match not found")

        if row["owner_user_id"] != owner_user_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        already_scored = row["games_team_a"] is not None

        if already_scored:
            # 1. Identify affected matches
            match_ids = get_matches_to_recompute(match_id, conn)

            # 2. Roll back ratings
            rollback_ratings(match_id, conn)

            # 3. Clear history + scores
            clear_future_matches(match_ids, conn)

        # 4. Apply new score
        record_match_score(
            match_id=match_id,
            games_team_a=games_team_a,
            games_team_b=games_team_b,
            display_score=display_score,
        )

        # 5. Reapply downstream matches
        if already_scored:
            reapply_matches(match_ids[1:], conn)

        return {
            "status": "scored",
            "override": already_scored,
            "recomputed_matches": len(match_ids) if already_scored else 1,
        }

    

def revert_match_ratings(match_id: int, conn):
    # MVP: disallow override until rating history is implemented
    raise HTTPException(
        status_code=400,
        detail="Override scoring not enabled yet (rating history required)",
    )

def get_matches_to_recompute(match_id: int, conn):
    rows = conn.execute(
        """
        SELECT id
        FROM matches
        WHERE id >= ?
          AND games_team_a IS NOT NULL
        ORDER BY id
        """,
        (match_id,),
    ).fetchall()

    return [r["id"] for r in rows]

def rollback_ratings(match_id: int, conn):
    rows = conn.execute(
        """
        SELECT player_id, rating_before
        FROM rating_history
        WHERE match_id = ?
        """,
        (match_id,),
    ).fetchall()

    if not rows:
        raise RuntimeError("No rating history to roll back")

    for r in rows:
        conn.execute(
            """
            UPDATE players
            SET current_rating = ?
            WHERE id = ?
            """,
            (r["rating_before"], r["player_id"]),
        )

def clear_future_matches(match_ids: list[int], conn):
    placeholders = ",".join("?" for _ in match_ids)

    conn.execute(
        f"""
        DELETE FROM rating_history
        WHERE match_id IN ({placeholders})
        """,
        match_ids,
    )

    conn.execute(
        f"""
        UPDATE matches
        SET games_team_a = NULL,
            games_team_b = NULL,
            display_score = NULL
        WHERE id IN ({placeholders})
        """,
        match_ids,
    )

def reapply_matches(match_ids: list[int], conn):
    for mid in match_ids:
        row = conn.execute(
            """
            SELECT games_team_a, games_team_b, display_score
            FROM matches
            WHERE id = ?
            """,
            (mid,),
        ).fetchone()

        if row is None or row["games_team_a"] is None:
            continue

        record_match_score(
            match_id=mid,
            games_team_a=row["games_team_a"],
            games_team_b=row["games_team_b"],
            display_score=row["display_score"],
            allow_override=True,
            conn=conn,  # 🔑 SAME CONNECTION
        )



def get_player_rating_history(player_id: int):
    with get_db() as conn:

        # Player info
        player = conn.execute(
            """
            SELECT id, first_name, last_name, current_rating
            FROM players
            WHERE id = ?
            """,
            (player_id,),
        ).fetchone()

        if player is None:
            raise HTTPException(status_code=404, detail="Player not found")

        # Rating history
        rows = conn.execute(
            """
            SELECT
                rh.match_id,
                rh.rating_before,
                rh.rating_after,
                m.display_score,
                ca.assignment_date
            FROM rating_history rh
            JOIN matches m ON m.id = rh.match_id
            JOIN courts c ON c.id = m.court_id
            JOIN court_assignments ca ON ca.id = c.court_assignment_id
            WHERE rh.player_id = ?
            ORDER BY ca.assignment_date DESC, rh.id DESC
            """,
            (player_id,),
        ).fetchall()

        history = []
        for r in rows:
            history.append({
                "match_id": r["match_id"],
                "rating_before": r["rating_before"],
                "rating_after": r["rating_after"],
                "delta": round(r["rating_after"] - r["rating_before"], 3),
                "date": r["assignment_date"],
                "display_score": r["display_score"],
            })

        return {
            "player": {
                "id": player["id"],
                "name": f"{player['first_name']} {player['last_name']}",
                "current_rating": player["current_rating"],
            },
            "history": history,
        }


def override_match_score(
    match_id: int,
    games_team_a: int,
    games_team_b: int,
    display_score: Optional[str] = None,
):
    with get_db() as conn:

        # 1. Ensure match exists and was scored
        match = conn.execute(
            """
            SELECT id, completed
            FROM matches
            WHERE id = ?
            """,
            (match_id,),
        ).fetchone()

        if match is None:
            raise RuntimeError("Match not found")

        if not match["completed"]:
            raise RuntimeError("Cannot override an unscored match")

        # 2. Determine affected matches (this match + future)
        match_ids = get_matches_to_recompute(match_id, conn)

        if not match_ids:
            raise RuntimeError("No matches to recompute")

        # 3. Roll back ratings for THIS match
        rollback_ratings(match_id, conn)

        # 4. Clear scores + rating history for ALL affected matches
        clear_future_matches(match_ids, conn)

        # 5. Update the overridden match score
        conn.execute(
            """
            UPDATE matches
            SET games_team_a = ?,
                games_team_b = ?,
                display_score = ?,
                completed = 1
            WHERE id = ?
            """,
            (games_team_a, games_team_b, display_score, match_id),
        )

        # 6. Reapply all matches in order
        reapply_matches(match_ids, conn)


def force_complete_match(
    match_id: int,
    reason: Optional[str] = None,
):
    with get_db() as conn:
        match = conn.execute(
            "SELECT * FROM matches WHERE id = ?",
            (match_id,),
        ).fetchone()

        if match is None:
            raise ValueError("Match not found")

        conn.execute(
            """
            UPDATE matches
            SET completed = 1,
                is_rated = 0,
                display_score = ?
            WHERE id = ?
            """,
            (reason or "Not played", match_id),
        )


def get_court_assignment_scores(court_assignment_id: int):
    with get_db() as conn:

        # 1. Assignment metadata
        assignment = conn.execute(
            """
            SELECT
                ca.id,
                ca.assignment_date,
                ca.status,
                cl.name AS location
            FROM court_assignments ca
            JOIN clubs cl ON cl.id = ca.location_club_id
            WHERE ca.id = ?
            """,
            (court_assignment_id,),
        ).fetchone()

        if assignment is None:
            raise ValueError("Court assignment not found")

        # 2. Courts + matches + players
        rows = conn.execute(
            """
            SELECT
                c.id AS court_id,
                c.court_number,

                m.id AS match_id,
                m.games_team_a,
                m.games_team_b,
                m.display_score,
                m.completed,
                m.is_rated,

                mp.player_id,
                mp.team,
                p.first_name,
                p.last_name
            FROM courts c
            JOIN matches m ON m.court_id = c.id
            JOIN match_players mp ON mp.match_id = m.id
            JOIN players p ON p.id = mp.player_id
            WHERE c.court_assignment_id = ?
            ORDER BY c.court_number, mp.team, p.last_name
            """,
            (court_assignment_id,),
        ).fetchall()

        courts = {}

        for row in rows:
            cid = row["court_id"]

            if cid not in courts:
                courts[cid] = {
                    "court_number": row["court_number"],
                    "match_id": row["match_id"],
                    "completed": bool(row["completed"]),
                    "is_rated": bool(row["is_rated"]),
                    "display_score": row["display_score"],
                    "teams": {
                        "A": [],
                        "B": [],
                    },
                }

            courts[cid]["teams"][row["team"]].append({
                "player_id": row["player_id"],
                "name": f"{row['first_name']} {row['last_name']}",
            })

        return {
            "court_assignment": {
                "id": assignment["id"],
                "date": assignment["assignment_date"],
                "location": assignment["location"],
                "status": assignment["status"],
            },
            "courts": list(courts.values()),
        }

def apply_assignment_algorithm(
    player_ids: list[int],
    algorithm: str,
) -> list[int]:
    """
    Returns ordered player IDs based on assignment algorithm.
    Assumes player_ids are already sorted by rating DESC.
    """

    if algorithm == "straight":
        return player_ids

    if algorithm == "random":
        shuffled = player_ids[:]
        random.shuffle(shuffled)
        return shuffled

    if algorithm == "blended":
        # Hardcoded blended pattern
        # Example for 12 players:
        # [1,2,3,4,5,6,7,8,9,10,11,12]
        # -> swap middle tiers
        blended = player_ids[:]

        if len(blended) >= 12:
            blended[2], blended[4] = blended[4], blended[2]
            blended[3], blended[5] = blended[5], blended[3]
            blended[6], blended[8] = blended[8], blended[6]
            blended[7], blended[9] = blended[9], blended[7]

        return blended

    raise ValueError(f"Unknown algorithm: {algorithm}")

