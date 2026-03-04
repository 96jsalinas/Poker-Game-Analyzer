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

-- WARNING: This schema file does NOT perform automatic structural
-- migrations for existing databases. All tables use CREATE TABLE
-- IF NOT EXISTS, which is safe for additive changes (adding tables,
-- columns, or indexes), but SQLite does not support changing a
-- PRIMARY KEY or CHECK constraint via ALTER TABLE.
--
-- The action_ev_cache table below relies on the NEW composite
-- primary key (action_id, hero_id, ev_type) and a CHECK constraint
-- on ev_type. If you are upgrading from an older version that
-- created action_ev_cache with a different PK (for example, only
-- (action_id, hero_id)) or without this CHECK, simply re-running
-- this script WILL NOT update the existing table definition.
--
-- On such upgraded databases, application code that uses
-- INSERT OR REPLACE into action_ev_cache will cause different
-- ev_type variants for the same (action_id, hero_id) to overwrite
-- each other under the old PK, producing incorrect and unstable
-- EV behavior without raising a hard error.
--
-- To avoid corrupted EV caches, you MUST ensure that any existing
-- action_ev_cache table is dropped and recreated before using this
-- schema. The simplest way is to clear/reset the database from the
-- application UI (e.g. "Clear Database" in Settings), or to
-- manually DROP TABLE action_ev_cache in SQLite and then allow
-- the application to recreate it on next startup.
--
-- Because this project is single-user and hand history files can
-- be re-imported from disk, a full database reset is the recommended
-- and supported migration path when upgrading across schema versions
-- that change the PK or CHECK on action_ev_cache.
CREATE TABLE IF NOT EXISTS action_ev_cache (
    action_id              INTEGER NOT NULL REFERENCES actions(id),
    hero_id                INTEGER NOT NULL REFERENCES players(id),
    equity                 REAL    NOT NULL,
    ev                     REAL    NOT NULL,
    ev_type                TEXT    NOT NULL CHECK(ev_type IN (
                               'exact', 'exact_multiway',
                               'range', 'range_multiway_approx',
                               'allin_exact', 'allin_exact_multiway'
                           )),
    blended_vpip           REAL,
    blended_pfr            REAL,
    blended_3bet           REAL,
    villain_preflop_action TEXT,
    contracted_range_size  INTEGER,
    fold_equity_pct        REAL,
    sample_count           INTEGER NOT NULL,
    computed_at            TEXT    NOT NULL,
    PRIMARY KEY (action_id, hero_id, ev_type)
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
