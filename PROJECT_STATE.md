# Tennis League Backend – Project State

## Overview

This is a FastAPI + SQLite backend for managing a recreational tennis league.

The system supports:

- League creation
- Club and player management
- Court assignment generation
- Publishing match schedules
- Match score submission
- Elo-style rating updates
- Owner score override with full rating recomputation
- Owner and player dashboards

The backend is currently complete and functional.  
This document describes the system architecture and lifecycle before frontend development begins.

## High-Level Architecture

Entities:

League
  → Clubs
     → Players
  → CourtAssignments
     → Courts
        → Matches
           → MatchPlayers
           → RatingHistory

Key Design Decisions:

- Players belong to a club.
- Clubs belong to a league.
- CourtAssignments belong to a league.
- Matches are created only when an assignment is published.
- Ratings update only when a match is finalized.
- Overrides trigger rating rollback and full recomputation.


## Database Schema

PRAGMA table_info(players);
0|id|INTEGER|0||1
1|league_id|INTEGER|1||0
2|first_name|TEXT|1||0
3|last_name|TEXT|1||0
4|gender|TEXT|0||0
5|city|TEXT|0||0
6|state|TEXT|0||0
7|email|TEXT|0||0
8|phone|TEXT|0||0
9|club_id|INTEGER|0||0
10|self_reported_rating|REAL|0||0
11|current_rating|REAL|0||0
12|matches_played|INTEGER|0|0|0
13|created_at|TIMESTAMP|0|CURRENT_TIMESTAMP|0
14|total_matches|INTEGER|0|0|0

PRAGMA table_info(leagues);
0|id|INTEGER|0||1
1|name|TEXT|1||0
2|owner_user_id|INTEGER|1||0
3|created_at|TIMESTAMP|0|CURRENT_TIMESTAMP|0

PRAGMA table_info(clubs);
0|id|INTEGER|0||1
1|league_id|INTEGER|1||0
2|name|TEXT|1||0

PRAGMA table_info(court_assignments);
0|id|INTEGER|0||1
1|league_id|INTEGER|1||0
2|assignment_date|DATE|1||0
3|location_club_id|INTEGER|1||0
4|num_courts|INTEGER|1||0
5|match_type|TEXT|1||0
6|algorithm|TEXT|1||0
7|status|TEXT|1||0
8|created_at|TIMESTAMP|0|CURRENT_TIMESTAMP|0

PRAGMA table_info(courts);
0|id|INTEGER|0||1
1|court_assignment_id|INTEGER|1||0
2|court_number|INTEGER|1||0

PRAGMA table_info(court_players);
0|id|INTEGER|0||1
1|court_id|INTEGER|1||0
2|player_id|INTEGER|1||0
3|team|TEXT|1||0

PRAGMA table_info(matches);
0|id|INTEGER|0||1
1|court_id|INTEGER|1||0
2|games_team_a|INTEGER|0||0
3|games_team_b|INTEGER|0||0
4|display_score|TEXT|0||0
5|is_independent|INTEGER|1||0
6|completed|INTEGER|1|0|0
7|is_rated|INTEGER|0|1|0

PRAGMA table_info(match_players);
0|match_id|INTEGER|1||1
1|player_id|INTEGER|1||2
2|team|TEXT|1||0

PRAGMA table_info(rating_history);
0|id|INTEGER|0||1
1|player_id|INTEGER|1||0
2|match_id|INTEGER|1||0
3|rating_before|REAL|1||0
4|rating_after|REAL|1||0
5|created_at|TEXT|0|CURRENT_TIMESTAMP|0
sqlite> 


## State Machines

### CourtAssignment.status

draft → generated → published

Rules:
- Generate only allowed from draft.
- Publish only allowed from generated.
- Cannot regenerate after publish.

---

### Match State

Fields:
- completed (0/1)
- is_rated (0/1)

Lifecycle:

Draft Score → Finalized Score

Rules:
- Score submission sets completed = 1
- Rating applied only once (is_rated = 1)
- Owner override allowed after completion
- Override triggers:
    - rating rollback
    - clearing future match ratings
    - full recomputation


## Assignment Algorithms

Supported algorithms:

- straight → rating order
- random → shuffled order
- blended → controlled mixing pattern

Algorithm operates on ordered player IDs and returns a reordered list.
Court grouping is performed after algorithm execution.


## Rating System

- Elo-style rating update
- RatingHistory table stores:
    - player_id
    - match_id
    - rating_before
    - rating_after

Override process:

1. Roll back rating_history for target match.
2. Reset player ratings.
3. Clear future matches.
4. Reapply matches sequentially.


## Open Architectural Questions

- Should players belong directly to league instead of indirectly via club?
- Should GET /leagues and GET /clubs endpoints be added?
- Should match scoring allow draft save before finalization?
- Is override recomputation logic fully deterministic?
- Should assignment algorithm store metadata about generation?