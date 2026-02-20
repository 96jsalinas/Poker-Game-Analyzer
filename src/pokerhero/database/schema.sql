CREATE TABLE IF NOT EXISTS players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    preferred_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_type TEXT NOT NULL,
    limit_type TEXT NOT NULL,
    max_seats INTEGER NOT NULL,
    small_blind REAL NOT NULL,
    big_blind REAL NOT NULL,
    ante REAL NOT NULL DEFAULT 0,
    start_time TEXT NOT NULL,
    hero_buy_in REAL,
    hero_cash_out REAL
);

CREATE TABLE IF NOT EXISTS hands (
    id TEXT NOT NULL PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES sessions(id),
    board_flop TEXT,
    board_turn TEXT,
    board_river TEXT,
    total_pot REAL NOT NULL,
    uncalled_bet_returned REAL NOT NULL DEFAULT 0,
    rake REAL NOT NULL DEFAULT 0,
    timestamp TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS hand_players (
    hand_id TEXT NOT NULL REFERENCES hands(id),
    player_id INTEGER NOT NULL REFERENCES players(id),
    position TEXT NOT NULL,
    starting_stack REAL NOT NULL,
    hole_cards TEXT,
    vpip INTEGER NOT NULL DEFAULT 0,
    pfr INTEGER NOT NULL DEFAULT 0,
    went_to_showdown INTEGER NOT NULL DEFAULT 0,
    net_result REAL NOT NULL,
    PRIMARY KEY (hand_id, player_id)
);

CREATE TABLE IF NOT EXISTS actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hand_id TEXT NOT NULL REFERENCES hands(id),
    player_id INTEGER NOT NULL REFERENCES players(id),
    is_hero INTEGER NOT NULL DEFAULT 0,
    street TEXT NOT NULL,
    action_type TEXT NOT NULL,
    amount REAL NOT NULL DEFAULT 0,
    amount_to_call REAL NOT NULL DEFAULT 0,
    pot_before REAL NOT NULL DEFAULT 0,
    is_all_in INTEGER NOT NULL DEFAULT 0,
    sequence INTEGER NOT NULL,
    spr REAL,
    mdf REAL
);
