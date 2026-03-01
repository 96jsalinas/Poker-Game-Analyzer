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
    hero_cash_out REAL,
    currency TEXT NOT NULL DEFAULT 'PLAY',
    is_favorite INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS hands (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_hand_id TEXT NOT NULL UNIQUE,
    session_id INTEGER NOT NULL REFERENCES sessions(id),
    board_flop TEXT,
    board_turn TEXT,
    board_river TEXT,
    total_pot REAL NOT NULL,
    uncalled_bet_returned REAL NOT NULL DEFAULT 0,
    rake REAL NOT NULL DEFAULT 0,
    timestamp TEXT NOT NULL,
    is_favorite INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS hand_players (
    hand_id INTEGER NOT NULL REFERENCES hands(id),
    player_id INTEGER NOT NULL REFERENCES players(id),
    position TEXT NOT NULL,
    starting_stack REAL NOT NULL,
    hole_cards TEXT,
    vpip INTEGER NOT NULL DEFAULT 0,
    pfr INTEGER NOT NULL DEFAULT 0,
    three_bet INTEGER NOT NULL DEFAULT 0,
    went_to_showdown INTEGER NOT NULL DEFAULT 0,
    net_result REAL NOT NULL,
    PRIMARY KEY (hand_id, player_id)
);

CREATE TABLE IF NOT EXISTS actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hand_id INTEGER NOT NULL REFERENCES hands(id),
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

CREATE INDEX IF NOT EXISTS idx_actions_hand_id ON actions(hand_id);
CREATE INDEX IF NOT EXISTS idx_actions_player_id ON actions(player_id);
CREATE INDEX IF NOT EXISTS idx_actions_hand_sequence ON actions(hand_id, sequence);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS action_ev_cache (
    action_id              INTEGER NOT NULL REFERENCES actions(id),
    hero_id                INTEGER NOT NULL REFERENCES players(id),
    equity                 REAL    NOT NULL,
    ev                     REAL    NOT NULL,
    ev_type                TEXT    NOT NULL CHECK(ev_type IN ('exact', 'exact_multiway', 'range', 'range_multiway_approx')),
    blended_vpip           REAL,
    blended_pfr            REAL,
    blended_3bet           REAL,
    villain_preflop_action TEXT,
    contracted_range_size  INTEGER,
    fold_equity_pct        REAL,
    sample_count           INTEGER NOT NULL,
    computed_at            TEXT    NOT NULL,
    PRIMARY KEY (action_id, hero_id)
);

CREATE TABLE IF NOT EXISTS target_settings (
    stat       TEXT NOT NULL,
    position   TEXT NOT NULL,
    green_min  REAL NOT NULL,
    green_max  REAL NOT NULL,
    yellow_min REAL NOT NULL,
    yellow_max REAL NOT NULL,
    PRIMARY KEY (stat, position)
);
