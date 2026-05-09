PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS leagues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    owner_user_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS clubs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    league_id INTEGER NOT NULL,
    name TEXT NOT NULL,

    FOREIGN KEY (league_id) REFERENCES leagues(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    league_id INTEGER NOT NULL,

    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    gender TEXT,
    city TEXT,
    state TEXT,

    email TEXT UNIQUE,
    phone TEXT,

    club_id INTEGER,

    self_reported_rating REAL,
    current_rating REAL,
    matches_played INTEGER DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (league_id) REFERENCES leagues(id) ON DELETE CASCADE,
    FOREIGN KEY (club_id) REFERENCES clubs(id)
);
CREATE TABLE IF NOT EXISTS court_assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    league_id INTEGER NOT NULL,

    assignment_date DATE NOT NULL,
    location_club_id INTEGER NOT NULL,

    num_courts INTEGER NOT NULL,
    match_type TEXT NOT NULL,      -- "singles" or "doubles"
    algorithm TEXT NOT NULL,       -- "straight", "random", "blended"
    status TEXT NOT NULL,          -- "draft", "published", "completed"

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (league_id) REFERENCES leagues(id) ON DELETE CASCADE,
    FOREIGN KEY (location_club_id) REFERENCES clubs(id)
);
CREATE TABLE IF NOT EXISTS courts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    court_assignment_id INTEGER NOT NULL,
    court_number INTEGER NOT NULL,

    FOREIGN KEY (court_assignment_id) REFERENCES court_assignments(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    court_id INTEGER NOT NULL,

    games_team_a INTEGER NOT NULL,
    games_team_b INTEGER NOT NULL,

    display_score TEXT,

    is_independent BOOLEAN DEFAULT 0,
    is_completed BOOLEAN DEFAULT 0,
    completed_at TIMESTAMP,

    FOREIGN KEY (court_id) REFERENCES courts(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS match_players (
    match_id INTEGER NOT NULL,
    player_id INTEGER NOT NULL,
    team TEXT NOT NULL CHECK (team IN ('A', 'B')),

    PRIMARY KEY (match_id, player_id),

    FOREIGN KEY (match_id) REFERENCES matches(id) ON DELETE CASCADE,
    FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS court_players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    court_id INTEGER NOT NULL,
    player_id INTEGER NOT NULL,
    team TEXT NOT NULL CHECK (team IN ('A', 'B')),
    FOREIGN KEY (court_id) REFERENCES courts(id),
    FOREIGN KEY (player_id) REFERENCES players(id)
);

