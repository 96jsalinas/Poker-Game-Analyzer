"""Tests for the analysis layer: DB query functions and stat calculations."""

from pathlib import Path

import pandas as pd
import pytest

FRATERNITAS = Path(__file__).parent / "fixtures" / "play_money_two_hand_session.txt"


# ---------------------------------------------------------------------------
# Shared fixture: ingested in-memory DB from the Fraternitas file (2 hands).
# Hand 1 — jsalinas96 BB, folds preflop:  vpip=False, pfr=False, wts=False
# Hand 2 — jsalinas96 SB, sees flop, loses at showdown: vpip=True, wts=True
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def db_with_data(tmp_path_factory):
    from pokerhero.database.db import init_db
    from pokerhero.ingestion.pipeline import ingest_file

    tmp = tmp_path_factory.mktemp("analysis_db")
    conn = init_db(tmp / "test.db")
    ingest_file(FRATERNITAS, "jsalinas96", conn)
    conn.commit()
    yield conn
    conn.close()


@pytest.fixture(scope="module")
def hero_player_id(db_with_data):
    row = db_with_data.execute(
        "SELECT id FROM players WHERE username = ?", ("jsalinas96",)
    ).fetchone()
    assert row is not None
    return row[0]


@pytest.fixture(scope="module")
def session_id(db_with_data):
    row = db_with_data.execute("SELECT id FROM sessions LIMIT 1").fetchone()
    assert row is not None
    return row[0]


# ---------------------------------------------------------------------------
# TestQueries
# ---------------------------------------------------------------------------
class TestQueries:
    def test_get_sessions_returns_dataframe(self, db_with_data, hero_player_id):
        from pokerhero.analysis.queries import get_sessions

        result = get_sessions(db_with_data, hero_player_id)
        assert isinstance(result, pd.DataFrame)

    def test_get_sessions_has_expected_columns(self, db_with_data, hero_player_id):
        from pokerhero.analysis.queries import get_sessions

        df = get_sessions(db_with_data, hero_player_id)
        assert {
            "id",
            "start_time",
            "game_type",
            "small_blind",
            "big_blind",
            "hands_played",
            "net_profit",
        } <= set(df.columns)

    def test_get_sessions_returns_one_row_for_one_file(
        self, db_with_data, hero_player_id
    ):
        from pokerhero.analysis.queries import get_sessions

        assert len(get_sessions(db_with_data, hero_player_id)) == 1

    def test_get_hands_returns_dataframe(self, db_with_data, hero_player_id):
        from pokerhero.analysis.queries import get_hands, get_sessions

        session_id = get_sessions(db_with_data, hero_player_id)["id"].iloc[0]
        result = get_hands(db_with_data, session_id, hero_player_id)
        assert isinstance(result, pd.DataFrame)

    def test_get_hands_has_expected_columns(self, db_with_data, hero_player_id):
        from pokerhero.analysis.queries import get_hands, get_sessions

        session_id = get_sessions(db_with_data, hero_player_id)["id"].iloc[0]
        df = get_hands(db_with_data, session_id, hero_player_id)
        assert {
            "id",
            "source_hand_id",
            "timestamp",
            "total_pot",
            "net_result",
            "hole_cards",
        } <= set(df.columns)

    def test_get_hands_returns_correct_count(self, db_with_data, hero_player_id):
        from pokerhero.analysis.queries import get_hands, get_sessions

        session_id = get_sessions(db_with_data, hero_player_id)["id"].iloc[0]
        assert len(get_hands(db_with_data, session_id, hero_player_id)) == 2

    def test_get_hands_includes_position_and_flags(self, db_with_data, hero_player_id):
        """get_hands must include position, went_to_showdown, and saw_flop columns
        for use by the hand-level filter controls."""
        from pokerhero.analysis.queries import get_hands, get_sessions

        session_id = get_sessions(db_with_data, hero_player_id)["id"].iloc[0]
        df = get_hands(db_with_data, session_id, hero_player_id)
        assert {"position", "went_to_showdown", "saw_flop"} <= set(df.columns)

    def test_get_actions_returns_dataframe(self, db_with_data, hero_player_id):
        from pokerhero.analysis.queries import get_actions, get_hands, get_sessions

        session_id = get_sessions(db_with_data, hero_player_id)["id"].iloc[0]
        hand_id = get_hands(db_with_data, session_id, hero_player_id)["id"].iloc[0]
        result = get_actions(db_with_data, hand_id)
        assert isinstance(result, pd.DataFrame)

    def test_get_actions_has_expected_columns(self, db_with_data, hero_player_id):
        from pokerhero.analysis.queries import get_actions, get_hands, get_sessions

        session_id = get_sessions(db_with_data, hero_player_id)["id"].iloc[0]
        hand_id = get_hands(db_with_data, session_id, hero_player_id)["id"].iloc[0]
        df = get_actions(db_with_data, hand_id)
        assert {
            "sequence",
            "is_hero",
            "street",
            "action_type",
            "amount",
            "pot_before",
            "username",
            "position",
        } <= set(df.columns)

    def test_get_actions_is_ordered_by_sequence(self, db_with_data, hero_player_id):
        from pokerhero.analysis.queries import get_actions, get_hands, get_sessions

        session_id = get_sessions(db_with_data, hero_player_id)["id"].iloc[0]
        hand_id = get_hands(db_with_data, session_id, hero_player_id)["id"].iloc[1]
        df = get_actions(db_with_data, hand_id)
        assert list(df["sequence"]) == sorted(df["sequence"].tolist())

    def test_get_hero_hand_players_returns_dataframe(
        self, db_with_data, hero_player_id
    ):
        from pokerhero.analysis.queries import get_hero_hand_players

        result = get_hero_hand_players(db_with_data, hero_player_id)
        assert isinstance(result, pd.DataFrame)

    def test_get_hero_hand_players_has_expected_columns(
        self, db_with_data, hero_player_id
    ):
        from pokerhero.analysis.queries import get_hero_hand_players

        df = get_hero_hand_players(db_with_data, hero_player_id)
        assert {
            "vpip",
            "pfr",
            "went_to_showdown",
            "net_result",
            "big_blind",
            "saw_flop",
        } <= set(df.columns)

    def test_get_hero_hand_players_returns_all_hands(
        self, db_with_data, hero_player_id
    ):
        from pokerhero.analysis.queries import get_hero_hand_players

        assert len(get_hero_hand_players(db_with_data, hero_player_id)) == 2

    def test_get_hero_hand_players_saw_flop_correct(self, db_with_data, hero_player_id):
        """Hand 1: hero folds preflop (saw_flop=0).
        Hand 2: hero plays flop (saw_flop=1)."""
        from pokerhero.analysis.queries import get_hero_hand_players

        df = get_hero_hand_players(db_with_data, hero_player_id)
        assert df["saw_flop"].sum() == 1

    def test_get_hero_hand_players_includes_session_id(
        self, db_with_data, hero_player_id
    ):
        """get_hero_hand_players must include a session_id column for nav links."""
        from pokerhero.analysis.queries import get_hero_hand_players

        df = get_hero_hand_players(db_with_data, hero_player_id)
        assert "session_id" in df.columns


# ---------------------------------------------------------------------------
# TestStats — pure unit tests using hand-crafted DataFrames
# ---------------------------------------------------------------------------
class TestStats:
    def test_vpip_pct_basic(self):
        from pokerhero.analysis.stats import vpip_pct

        df = pd.DataFrame({"vpip": [1, 0, 1, 1, 0]})
        assert vpip_pct(df) == pytest.approx(0.6)

    def test_vpip_pct_all_vpip(self):
        from pokerhero.analysis.stats import vpip_pct

        df = pd.DataFrame({"vpip": [1, 1, 1]})
        assert vpip_pct(df) == pytest.approx(1.0)

    def test_vpip_pct_empty_returns_zero(self):
        from pokerhero.analysis.stats import vpip_pct

        assert vpip_pct(pd.DataFrame({"vpip": []})) == 0.0

    def test_pfr_pct_basic(self):
        from pokerhero.analysis.stats import pfr_pct

        df = pd.DataFrame({"pfr": [1, 0, 0, 1]})
        assert pfr_pct(df) == pytest.approx(0.5)

    def test_pfr_pct_empty_returns_zero(self):
        from pokerhero.analysis.stats import pfr_pct

        assert pfr_pct(pd.DataFrame({"pfr": []})) == 0.0

    def test_win_rate_bb100_positive(self):
        from pokerhero.analysis.stats import win_rate_bb100

        # +200 and -100 at BB=200 → +1 and -0.5 BB = +0.5BB / 2 hands * 100 = 25 bb/100
        df = pd.DataFrame({"net_result": [200.0, -100.0], "big_blind": [200.0, 200.0]})
        assert win_rate_bb100(df) == pytest.approx(25.0)

    def test_win_rate_bb100_negative(self):
        from pokerhero.analysis.stats import win_rate_bb100

        df = pd.DataFrame({"net_result": [-400.0], "big_blind": [200.0]})
        assert win_rate_bb100(df) == pytest.approx(-200.0)

    def test_win_rate_bb100_empty_returns_zero(self):
        from pokerhero.analysis.stats import win_rate_bb100

        df = pd.DataFrame({"net_result": [], "big_blind": []})
        assert win_rate_bb100(df) == 0.0

    def test_aggression_factor_basic(self):
        from pokerhero.analysis.stats import aggression_factor

        df = pd.DataFrame(
            {
                "action_type": ["BET", "RAISE", "CALL", "CALL", "FOLD"],
                "street": ["FLOP", "TURN", "FLOP", "RIVER", "FLOP"],
            }
        )
        # post-flop: 2 aggressive (BET+RAISE), 2 calls → AF = 2/2 = 1.0
        assert aggression_factor(df) == pytest.approx(1.0)

    def test_aggression_factor_no_calls_returns_infinity(self):
        from pokerhero.analysis.stats import aggression_factor

        df = pd.DataFrame(
            {
                "action_type": ["BET", "RAISE"],
                "street": ["FLOP", "TURN"],
            }
        )
        assert aggression_factor(df) == float("inf")

    def test_aggression_factor_preflop_excluded(self):
        from pokerhero.analysis.stats import aggression_factor

        df = pd.DataFrame(
            {
                "action_type": ["RAISE", "CALL"],
                "street": ["PREFLOP", "PREFLOP"],
            }
        )
        # All preflop — no post-flop actions → infinite aggression (0 calls post-flop)
        assert aggression_factor(df) == float("inf")

    def test_wtsd_pct_basic(self):
        from pokerhero.analysis.stats import wtsd_pct

        # 2 saw flop, 1 went to showdown → 50%
        df = pd.DataFrame({"went_to_showdown": [1, 0], "saw_flop": [1, 1]})
        assert wtsd_pct(df) == pytest.approx(0.5)

    def test_wtsd_pct_no_flops_returns_zero(self):
        from pokerhero.analysis.stats import wtsd_pct

        df = pd.DataFrame({"went_to_showdown": [0, 0], "saw_flop": [0, 0]})
        assert wtsd_pct(df) == 0.0

    def test_total_profit_positive(self):
        from pokerhero.analysis.stats import total_profit

        df = pd.DataFrame({"net_result": [500.0, -200.0, 100.0]})
        assert total_profit(df) == pytest.approx(400.0)

    def test_total_profit_empty_returns_zero(self):
        from pokerhero.analysis.stats import total_profit

        assert total_profit(pd.DataFrame({"net_result": []})) == 0.0


# ---------------------------------------------------------------------------
# TestHeroTimeline — get_hero_timeline (for bankroll graph)
# ---------------------------------------------------------------------------
class TestHeroTimeline:
    def test_get_hero_timeline_returns_dataframe(self, db_with_data, hero_player_id):
        from pokerhero.analysis.queries import get_hero_timeline

        assert isinstance(get_hero_timeline(db_with_data, hero_player_id), pd.DataFrame)

    def test_get_hero_timeline_has_expected_columns(self, db_with_data, hero_player_id):
        from pokerhero.analysis.queries import get_hero_timeline

        df = get_hero_timeline(db_with_data, hero_player_id)
        assert {"timestamp", "net_result"} <= set(df.columns)

    def test_get_hero_timeline_one_row_per_hand(self, db_with_data, hero_player_id):
        """Fraternitas file has 2 hands — expect 2 timeline rows."""
        from pokerhero.analysis.queries import get_hero_timeline

        assert len(get_hero_timeline(db_with_data, hero_player_id)) == 2

    def test_get_hero_timeline_ordered_by_timestamp(self, db_with_data, hero_player_id):
        from pokerhero.analysis.queries import get_hero_timeline

        df = get_hero_timeline(db_with_data, hero_player_id)
        timestamps = df["timestamp"].tolist()
        assert timestamps == sorted(timestamps)


# ---------------------------------------------------------------------------
# TestHeroActions — get_hero_actions (for per-position aggression factor)
# ---------------------------------------------------------------------------
class TestHeroActions:
    def test_get_hero_actions_returns_dataframe(self, db_with_data, hero_player_id):
        from pokerhero.analysis.queries import get_hero_actions

        assert isinstance(get_hero_actions(db_with_data, hero_player_id), pd.DataFrame)

    def test_get_hero_actions_has_expected_columns(self, db_with_data, hero_player_id):
        from pokerhero.analysis.queries import get_hero_actions

        df = get_hero_actions(db_with_data, hero_player_id)
        assert {"hand_id", "street", "action_type", "position"} <= set(df.columns)

    def test_get_hero_actions_only_postflop_streets(self, db_with_data, hero_player_id):
        """Only FLOP/TURN/RIVER rows must be returned — no PREFLOP."""
        from pokerhero.analysis.queries import get_hero_actions

        df = get_hero_actions(db_with_data, hero_player_id)
        assert set(df["street"].unique()) <= {"FLOP", "TURN", "RIVER"}

    def test_get_hero_actions_no_preflop_rows(self, db_with_data, hero_player_id):
        from pokerhero.analysis.queries import get_hero_actions

        df = get_hero_actions(db_with_data, hero_player_id)
        assert "PREFLOP" not in df["street"].values

    def test_get_hero_actions_has_rows_when_flop_seen(
        self, db_with_data, hero_player_id
    ):
        """Hand 2: hero sees flop → at least one post-flop action row."""
        from pokerhero.analysis.queries import get_hero_actions

        assert len(get_hero_actions(db_with_data, hero_player_id)) > 0


# ---------------------------------------------------------------------------
# TestOpportunityActions — get_hero_opportunity_actions (for 3-Bet%/C-Bet%)
# ---------------------------------------------------------------------------
class TestOpportunityActions:
    def test_returns_dataframe(self, db_with_data, hero_player_id):
        from pokerhero.analysis.queries import get_hero_opportunity_actions

        result = get_hero_opportunity_actions(db_with_data, hero_player_id)
        assert isinstance(result, pd.DataFrame)

    def test_has_expected_columns(self, db_with_data, hero_player_id):
        from pokerhero.analysis.queries import get_hero_opportunity_actions

        df = get_hero_opportunity_actions(db_with_data, hero_player_id)
        assert {
            "hand_id",
            "saw_flop",
            "sequence",
            "is_hero",
            "street",
            "action_type",
        } <= set(df.columns)

    def test_only_preflop_and_flop_streets(self, db_with_data, hero_player_id):
        from pokerhero.analysis.queries import get_hero_opportunity_actions

        df = get_hero_opportunity_actions(db_with_data, hero_player_id)
        assert set(df["street"].unique()) <= {"PREFLOP", "FLOP"}

    def test_has_rows(self, db_with_data, hero_player_id):
        from pokerhero.analysis.queries import get_hero_opportunity_actions

        assert len(get_hero_opportunity_actions(db_with_data, hero_player_id)) > 0


# ---------------------------------------------------------------------------
# TestThreeBetCBet — pure unit tests with hand-crafted DataFrames
# ---------------------------------------------------------------------------
class TestThreeBetCBet:
    def _make_preflop_df(self) -> pd.DataFrame:
        """Two hands: Hand 1 hero folds to raise, Hand 2 hero re-raises."""
        return pd.DataFrame(
            {
                "hand_id": [1, 1, 1, 2, 2, 2, 2],
                "saw_flop": [0, 0, 0, 0, 0, 0, 0],
                "sequence": [1, 2, 3, 4, 5, 6, 7],
                "is_hero": [0, 0, 1, 0, 0, 1, 0],
                "street": ["PREFLOP"] * 7,
                "action_type": [
                    "CALL",
                    "RAISE",
                    "FOLD",  # hand 1: raise before hero → opp, no 3-bet
                    "CALL",
                    "RAISE",
                    "RAISE",
                    "FOLD",  # hand 2: raise before hero → opp, 3-bet
                ],
            }
        )

    def _make_cbet_df(self) -> pd.DataFrame:
        """Two hands: Hand 1 hero c-bets, Hand 2 hero checks flop."""
        return pd.DataFrame(
            {
                "hand_id": [1, 1, 1, 1, 1, 2, 2, 2, 2, 2],
                "saw_flop": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
                "sequence": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                "is_hero": [0, 1, 0, 0, 1, 0, 1, 0, 0, 1],
                "street": [
                    "PREFLOP",
                    "PREFLOP",
                    "PREFLOP",
                    "FLOP",
                    "FLOP",
                    "PREFLOP",
                    "PREFLOP",
                    "PREFLOP",
                    "FLOP",
                    "FLOP",
                ],
                "action_type": [
                    "CALL",
                    "RAISE",
                    "CALL",
                    "CHECK",
                    "BET",  # hand 1: last PF raiser, bets flop
                    "CALL",
                    "RAISE",
                    "CALL",
                    "CHECK",
                    "CHECK",  # hand 2: last PF raiser, checks flop
                ],
            }
        )

    def test_three_bet_pct_empty_returns_zero(self):
        from pokerhero.analysis.stats import three_bet_pct

        df = pd.DataFrame(
            columns=[
                "hand_id",
                "saw_flop",
                "sequence",
                "is_hero",
                "street",
                "action_type",
            ]
        )
        assert three_bet_pct(df) == 0.0

    def test_three_bet_pct_no_opportunity_returns_zero(self):
        """No raise before hero preflop → no opportunities → 0.0."""
        from pokerhero.analysis.stats import three_bet_pct

        df = pd.DataFrame(
            {
                "hand_id": [1, 1],
                "saw_flop": [0, 0],
                "sequence": [1, 2],
                "is_hero": [0, 1],
                "street": ["PREFLOP", "PREFLOP"],
                "action_type": ["CALL", "RAISE"],
            }
        )
        assert three_bet_pct(df) == 0.0

    def test_three_bet_pct_one_of_two(self):
        """Hand 1: opportunity, no 3-bet. Hand 2: opportunity, 3-bet → 0.5."""
        from pokerhero.analysis.stats import three_bet_pct

        assert three_bet_pct(self._make_preflop_df()) == pytest.approx(0.5)

    def test_three_bet_pct_all_three_bet(self):
        """All opportunities result in a 3-bet → 1.0."""
        from pokerhero.analysis.stats import three_bet_pct

        df = pd.DataFrame(
            {
                "hand_id": [1, 1, 1],
                "saw_flop": [0, 0, 0],
                "sequence": [1, 2, 3],
                "is_hero": [0, 0, 1],
                "street": ["PREFLOP", "PREFLOP", "PREFLOP"],
                "action_type": ["CALL", "RAISE", "RAISE"],
            }
        )
        assert three_bet_pct(df) == pytest.approx(1.0)

    def test_three_bet_pct_bb_blind_post_skipped(self):
        """Regression: POST_BLIND must not count as hero's first voluntary action.

        Hero posts BB (seq 2), BTN raises (seq 3), SB folds (seq 4), hero
        3-bets from BB (seq 5) → 1 opportunity, 1 made → 1.0.

        Without the fix hero_first_seq=2 (blind post), the pre-hero window is
        empty (only SB's blind post before it), so zero opportunities are
        counted and the result is incorrectly 0.0.
        """
        from pokerhero.analysis.stats import three_bet_pct

        df = pd.DataFrame(
            {
                "hand_id": [1, 1, 1, 1, 1],
                "sequence": [1, 2, 3, 4, 5],
                "is_hero": [0, 1, 0, 0, 1],
                "street": ["PREFLOP"] * 5,
                "action_type": [
                    "POST_BLIND",  # SB posts
                    "POST_BLIND",  # BB posts (hero) — must be skipped
                    "RAISE",  # BTN open-raises
                    "FOLD",  # SB folds
                    "RAISE",  # BB 3-bets (hero)
                ],
            }
        )
        assert three_bet_pct(df) == pytest.approx(1.0)

    def test_three_bet_pct_excludes_4bet_opportunity(self):
        """Pot already 3-bet before hero acts → NOT a 3-bet opportunity.

        Villain A opens (RAISE seq 3), Villain B 3-bets (RAISE seq 4),
        Hero 4-bets (RAISE seq 5). Two raises before hero → 4-bet opp,
        not 3-bet opp → 0 opportunities, result 0.0.
        """
        from pokerhero.analysis.stats import three_bet_pct

        df = pd.DataFrame(
            {
                "hand_id": [1, 1, 1, 1, 1, 1, 1],
                "saw_flop": [0, 0, 0, 0, 0, 0, 0],
                "sequence": [1, 2, 3, 4, 5, 6, 7],
                "is_hero": [0, 1, 0, 0, 1, 0, 0],
                "street": ["PREFLOP"] * 7,
                "action_type": [
                    "POST_BLIND",  # SB
                    "POST_BLIND",  # BB (hero)
                    "RAISE",  # UTG opens (2-bet)
                    "RAISE",  # CO 3-bets
                    "RAISE",  # Hero 4-bets
                    "FOLD",  # UTG folds
                    "FOLD",  # CO folds
                ],
            }
        )
        assert three_bet_pct(df) == 0.0

    def test_three_bet_pct_mixed_3bet_and_4bet_opportunities(self):
        """Hand 1: one raise before hero → 3-bet opportunity (hero folds).
        Hand 2: two raises before hero → 4-bet opportunity (not counted).
        Result: 1 opportunity, 0 made → 0.0 (not 0.5 from counting both).
        """
        from pokerhero.analysis.stats import three_bet_pct

        df = pd.DataFrame(
            {
                "hand_id": [1, 1, 1, 2, 2, 2, 2, 2],
                "saw_flop": [0, 0, 0, 0, 0, 0, 0, 0],
                "sequence": [1, 2, 3, 4, 5, 6, 7, 8],
                "is_hero": [0, 0, 1, 0, 1, 0, 0, 1],
                "street": ["PREFLOP"] * 8,
                "action_type": [
                    "CALL",  # H1: limper
                    "RAISE",  # H1: open raise
                    "FOLD",  # H1: hero folds → opportunity, not made
                    "POST_BLIND",  # H2: SB
                    "POST_BLIND",  # H2: BB (hero)
                    "RAISE",  # H2: UTG opens
                    "RAISE",  # H2: CO 3-bets
                    "RAISE",  # H2: hero 4-bets → NOT a 3-bet opp
                ],
            }
        )
        assert three_bet_pct(df) == pytest.approx(0.0)
        from pokerhero.analysis.stats import cbet_pct

        df = pd.DataFrame(
            columns=[
                "hand_id",
                "saw_flop",
                "sequence",
                "is_hero",
                "street",
                "action_type",
            ]
        )
        assert cbet_pct(df) == 0.0

    def test_cbet_pct_no_opportunity_returns_zero(self):
        """Hero not preflop last-raiser → no c-bet opportunity."""
        from pokerhero.analysis.stats import cbet_pct

        df = pd.DataFrame(
            {
                "hand_id": [1, 1, 1, 1],
                "saw_flop": [1, 1, 1, 1],
                "sequence": [1, 2, 3, 4],
                "is_hero": [0, 0, 1, 1],
                "street": ["PREFLOP", "PREFLOP", "FLOP", "FLOP"],
                "action_type": ["RAISE", "CALL", "CHECK", "BET"],
            }
        )
        # Non-hero raised preflop last → hero is not last raiser → 0 opportunities
        assert cbet_pct(df) == 0.0

    def test_cbet_pct_one_of_two(self):
        """Hand 1: c-bet made. Hand 2: opportunity but checks → 0.5."""
        from pokerhero.analysis.stats import cbet_pct

        assert cbet_pct(self._make_cbet_df()) == pytest.approx(0.5)

    def test_cbet_pct_all_cbet(self):
        """Single hand: hero is PF raiser, bets flop → 1.0."""
        from pokerhero.analysis.stats import cbet_pct

        df = pd.DataFrame(
            {
                "hand_id": [1, 1, 1],
                "saw_flop": [1, 1, 1],
                "sequence": [1, 2, 3],
                "is_hero": [0, 1, 1],
                "street": ["PREFLOP", "PREFLOP", "FLOP"],
                "action_type": ["CALL", "RAISE", "BET"],
            }
        )
        assert cbet_pct(df) == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# TestEV — compute_ev using PokerKit equity
# ---------------------------------------------------------------------------
class TestEV:
    def test_returns_none_when_villain_is_none(self):
        """When villain cards are unknown, EV cannot be computed."""
        from pokerhero.analysis.stats import compute_ev

        assert compute_ev("Ah Kh", None, "Qh Jh Th", 100.0, 300.0) is None

    def test_returns_none_when_villain_is_empty(self):
        """Empty villain string also returns None."""
        from pokerhero.analysis.stats import compute_ev

        assert compute_ev("Ah Kh", "", "Qh Jh Th", 100.0, 300.0) is None

    def test_winning_hand_is_positive_ev(self):
        """Hero has royal flush vs trash on complete board → positive EV."""
        from pokerhero.analysis.stats import compute_ev

        # Hero: Ah Kh, Board: Qh Jh Th 9d 2s (A-K-Q-J-T royal flush for hero)
        # Villain: 2c 3d (no hand)
        result = compute_ev("Ah Kh", "2c 3d", "Qh Jh Th 9d 2s", 100.0, 300.0)
        assert result is not None
        assert result[0] > 0

    def test_losing_hand_is_negative_ev(self):
        """Hero has trash vs royal flush on complete board → negative EV."""
        from pokerhero.analysis.stats import compute_ev

        # Hero: 2c 3d, Villain: Ah Kh, Board: Qh Jh Th 9d 2s
        result = compute_ev("2c 3d", "Ah Kh", "Qh Jh Th 9d 2s", 100.0, 300.0)
        assert result is not None
        assert result[0] < 0

    def test_ev_formula_at_river(self):
        """Complete board → exact equity; EV = equity*pot_to_win - wager."""
        from pokerhero.analysis.stats import compute_ev

        # Hero: Ah Kh vs 2c 3d on complete board → equity=1.0
        # EV = 1.0 * 300 - 100 = 200 (net profit, not gross pot)
        result = compute_ev("Ah Kh", "2c 3d", "Qh Jh Th 9d 2s", 100.0, 300.0)
        assert result is not None
        assert result[0] == pytest.approx(200.0, abs=5.0)

    def test_ev_partial_board_in_range(self):
        """Partial board (flop only) → equity between 0 and 1 for non-trivial hand."""
        from pokerhero.analysis.stats import compute_ev

        # Hero: Ah Kh (nut flush draw), Villain: 2c 2d (pair of 2s), Board: Qh Jh 2s
        # Villain has set of 2s, hero has many outs (flush + straight outs)
        result = compute_ev("Ah Kh", "2c 2d", "Qh Jh 2s", 100.0, 300.0)
        assert result is not None
        # Result is a 2-tuple of finite floats
        assert isinstance(result, tuple)


# ---------------------------------------------------------------------------
# TestEVTuple — compute_ev must return (ev, equity) tuple (not bare float)
# ---------------------------------------------------------------------------
class TestEVTuple:
    """Failing tests: compute_ev must return tuple[float, float] | None.

    These tests drive the A1 sub-task of the EV redesign.
    """

    def test_returns_none_when_villain_unknown(self):
        """None is still returned when villain cards are absent."""
        from pokerhero.analysis.stats import compute_ev

        assert compute_ev("Ah Kh", None, "Qh Jh Th", 100.0, 300.0) is None

    def test_returns_tuple_not_bare_float(self):
        """Result must be a 2-tuple, not a bare float."""
        from pokerhero.analysis.stats import compute_ev

        result = compute_ev("Ah Kh", "2c 3d", "Qh Jh Th 9d 2s", 100.0, 300.0)
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_first_element_is_ev(self):
        """result[0] is EV — positive when hero has royal flush vs trash."""
        from pokerhero.analysis.stats import compute_ev

        ev, _ = compute_ev("Ah Kh", "2c 3d", "Qh Jh Th 9d 2s", 100.0, 300.0)
        assert ev > 0

    def test_second_element_is_equity(self):
        """result[1] is equity — a float in [0, 1]."""
        from pokerhero.analysis.stats import compute_ev

        _, equity = compute_ev("Ah Kh", "2c 3d", "Qh Jh Th 9d 2s", 100.0, 300.0)
        assert 0.0 <= equity <= 1.0

    def test_equity_near_one_for_dominating_hand(self):
        """Hero royal flush on complete board → equity ≈ 1.0."""
        from pokerhero.analysis.stats import compute_ev

        _, equity = compute_ev("Ah Kh", "2c 3d", "Qh Jh Th 9d 2s", 100.0, 300.0)
        assert equity == pytest.approx(1.0, abs=0.01)

    def test_ev_formula_consistent_with_equity(self):
        """EV should equal equity*pot_to_win - amount_risked."""
        from pokerhero.analysis.stats import compute_ev

        amount_risked, pot_to_win = 100.0, 300.0
        ev, equity = compute_ev(
            "Ah Kh", "2c 3d", "Qh Jh Th 9d 2s", amount_risked, pot_to_win
        )
        expected_ev = equity * pot_to_win - amount_risked
        assert ev == pytest.approx(expected_ev, abs=0.01)


# ---------------------------------------------------------------------------
class TestComputeEquity:
    def setup_method(self):
        """Clear the equity cache before each test for isolation."""
        from pokerhero.analysis.stats import compute_equity

        compute_equity.cache_clear()

    def test_complete_board_winner_equity_is_one(self):
        """Hero royal flush vs trash on complete 5-card board → equity ≈ 1.0."""
        from pokerhero.analysis.stats import compute_equity

        equity = compute_equity("Ah Kh", "2c 3d", "Qh Jh Th 9d 2s", 5000)
        assert equity == pytest.approx(1.0, abs=0.01)

    def test_complete_board_loser_equity_is_zero(self):
        """Hero trash vs royal flush on complete 5-card board → equity ≈ 0.0."""
        from pokerhero.analysis.stats import compute_equity

        equity = compute_equity("2c 3d", "Ah Kh", "Qh Jh Th 9d 2s", 5000)
        assert equity == pytest.approx(0.0, abs=0.01)

    def test_partial_board_equity_in_unit_interval(self):
        """Non-trivial flop: equity must be strictly between 0 and 1."""
        from pokerhero.analysis.stats import compute_equity

        # Hero: Ah Kh (royal flush draw), Villain: 2c 2d (set of 2s), Board: Qh Jh 2s
        equity = compute_equity("Ah Kh", "2c 2d", "Qh Jh 2s", 200)
        assert 0.0 < equity < 1.0

    def test_result_is_cached(self):
        """Second call with identical args must be a cache hit, not a recompute."""
        from pokerhero.analysis.stats import compute_equity

        equity1 = compute_equity("Ah Kh", "2c 3d", "Qh Jh Th 9d 2s", 5000)
        hits_before = compute_equity.cache_info().hits
        equity2 = compute_equity("Ah Kh", "2c 3d", "Qh Jh Th 9d 2s", 5000)
        assert compute_equity.cache_info().hits == hits_before + 1
        assert equity1 == equity2


# ---------------------------------------------------------------------------
# TestDateFilter — since_date parameter on query functions
# ---------------------------------------------------------------------------
class TestDateFilter:
    """since_date filters rows older than the cutoff; None returns everything."""

    def test_get_sessions_since_far_future_returns_empty(
        self, db_with_data, hero_player_id
    ):
        from pokerhero.analysis.queries import get_sessions

        df = get_sessions(db_with_data, hero_player_id, since_date="2099-01-01")
        assert df.empty

    def test_get_sessions_since_past_returns_all(self, db_with_data, hero_player_id):
        from pokerhero.analysis.queries import get_sessions

        all_df = get_sessions(db_with_data, hero_player_id)
        filtered = get_sessions(db_with_data, hero_player_id, since_date="2000-01-01")
        assert len(filtered) == len(all_df)

    def test_get_sessions_since_none_returns_all(self, db_with_data, hero_player_id):
        from pokerhero.analysis.queries import get_sessions

        all_df = get_sessions(db_with_data, hero_player_id)
        filtered = get_sessions(db_with_data, hero_player_id, since_date=None)
        assert len(filtered) == len(all_df)

    def test_get_hero_hand_players_since_far_future_returns_empty(
        self, db_with_data, hero_player_id
    ):
        from pokerhero.analysis.queries import get_hero_hand_players

        df = get_hero_hand_players(
            db_with_data, hero_player_id, since_date="2099-01-01"
        )
        assert df.empty

    def test_get_hero_timeline_since_far_future_returns_empty(
        self, db_with_data, hero_player_id
    ):
        from pokerhero.analysis.queries import get_hero_timeline

        df = get_hero_timeline(db_with_data, hero_player_id, since_date="2099-01-01")
        assert df.empty

    def test_get_hero_actions_since_far_future_returns_empty(
        self, db_with_data, hero_player_id
    ):
        from pokerhero.analysis.queries import get_hero_actions

        df = get_hero_actions(db_with_data, hero_player_id, since_date="2099-01-01")
        assert df.empty

    def test_get_hero_opportunity_actions_since_far_future_returns_empty(
        self, db_with_data, hero_player_id
    ):
        from pokerhero.analysis.queries import get_hero_opportunity_actions

        df = get_hero_opportunity_actions(
            db_with_data, hero_player_id, since_date="2099-01-01"
        )
        assert df.empty


# ---------------------------------------------------------------------------
# TestCurrencyFilter
# ---------------------------------------------------------------------------


class TestCurrencyFilter:
    """currency_type filter on query functions; uses a self-contained in-memory DB."""

    @pytest.fixture
    def cdb(self, tmp_path):
        """In-memory DB with two sessions: one PLAY, one EUR (two hands each)."""
        from pokerhero.database.db import init_db, upsert_player

        conn = init_db(tmp_path / "cur.db")
        pid = upsert_player(conn, "hero")

        # Two sessions: one play-money, one EUR real-money
        conn.execute(
            "INSERT INTO sessions (game_type, limit_type, max_seats, small_blind,"
            " big_blind, ante, start_time, currency) VALUES"
            " ('NLHE','NL',9,100,200,0,'2026-01-01T10:00:00','PLAY')"
        )
        play_sid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        conn.execute(
            "INSERT INTO sessions (game_type, limit_type, max_seats, small_blind,"
            " big_blind, ante, start_time, currency) VALUES"
            " ('NLHE','NL',6,0.02,0.05,0,'2026-02-01T10:00:00','EUR')"
        )
        eur_sid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        # One hand per session; hero participates in both
        for sid, ts in [
            (play_sid, "2026-01-01T10:05:00"),
            (eur_sid, "2026-02-01T10:05:00"),
        ]:
            conn.execute(
                "INSERT INTO hands"
                " (source_hand_id, session_id, total_pot, rake, timestamp)"
                " VALUES (?, ?, 200, 5, ?)",
                (f"H{sid}", sid, ts),
            )
            hid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            conn.execute(
                "INSERT INTO hand_players (hand_id, player_id, position,"
                " starting_stack, net_result) VALUES (?, ?, 'BTN', 10000, 100)",
                (hid, pid),
            )
            conn.execute(
                "INSERT INTO actions (hand_id, player_id, is_hero, street,"
                " action_type, amount, amount_to_call, pot_before, sequence)"
                " VALUES (?, ?, 1, 'FLOP', 'BET', 50, 0, 100, 1)",
                (hid, pid),
            )

        conn.commit()
        yield conn, pid
        conn.close()

    # --- get_sessions ---

    def test_get_sessions_includes_currency_column(self, cdb):
        """get_sessions must return a 'currency' column."""
        from pokerhero.analysis.queries import get_sessions

        conn, pid = cdb
        df = get_sessions(conn, pid)
        assert "currency" in df.columns

    def test_get_sessions_currency_type_real_returns_only_real(self, cdb):
        """currency_type='real' returns only EUR/USD sessions."""
        from pokerhero.analysis.queries import get_sessions

        conn, pid = cdb
        df = get_sessions(conn, pid, currency_type="real")
        assert len(df) == 1
        assert df["currency"].iloc[0] == "EUR"

    def test_get_sessions_currency_type_play_returns_only_play(self, cdb):
        """currency_type='play' returns only PLAY sessions."""
        from pokerhero.analysis.queries import get_sessions

        conn, pid = cdb
        df = get_sessions(conn, pid, currency_type="play")
        assert len(df) == 1
        assert df["currency"].iloc[0] == "PLAY"

    def test_get_sessions_currency_type_none_returns_all(self, cdb):
        """currency_type=None (default) returns all sessions."""
        from pokerhero.analysis.queries import get_sessions

        conn, pid = cdb
        df = get_sessions(conn, pid)
        assert len(df) == 2

    # --- get_hero_hand_players ---

    def test_get_hero_hand_players_currency_real_filters(self, cdb):
        """currency_type='real' returns only hands from EUR/USD sessions."""
        from pokerhero.analysis.queries import get_hero_hand_players

        conn, pid = cdb
        df = get_hero_hand_players(conn, pid, currency_type="real")
        assert len(df) == 1

    def test_get_hero_hand_players_currency_play_filters(self, cdb):
        """currency_type='play' returns only hands from PLAY sessions."""
        from pokerhero.analysis.queries import get_hero_hand_players

        conn, pid = cdb
        df = get_hero_hand_players(conn, pid, currency_type="play")
        assert len(df) == 1

    # --- get_hero_timeline ---

    def test_get_hero_timeline_currency_real_filters(self, cdb):
        """currency_type='real' returns only hands from real-money sessions."""
        from pokerhero.analysis.queries import get_hero_timeline

        conn, pid = cdb
        df = get_hero_timeline(conn, pid, currency_type="real")
        assert len(df) == 1

    def test_get_hero_timeline_currency_play_filters(self, cdb):
        """currency_type='play' returns only hands from play-money sessions."""
        from pokerhero.analysis.queries import get_hero_timeline

        conn, pid = cdb
        df = get_hero_timeline(conn, pid, currency_type="play")
        assert len(df) == 1

    # --- get_hero_actions ---

    def test_get_hero_actions_currency_real_filters(self, cdb):
        """currency_type='real' returns only post-flop actions from real sessions."""
        from pokerhero.analysis.queries import get_hero_actions

        conn, pid = cdb
        df = get_hero_actions(conn, pid, currency_type="real")
        assert len(df) == 1

    def test_get_hero_actions_currency_play_filters(self, cdb):
        """currency_type='play' returns only post-flop actions from play sessions."""
        from pokerhero.analysis.queries import get_hero_actions

        conn, pid = cdb
        df = get_hero_actions(conn, pid, currency_type="play")
        assert len(df) == 1

    # --- get_hero_opportunity_actions ---

    def test_get_hero_opportunity_actions_currency_real_filters(self, cdb):
        """currency_type='real' filters opportunity actions to real sessions."""
        from pokerhero.analysis.queries import get_hero_opportunity_actions

        conn, pid = cdb
        df = get_hero_opportunity_actions(conn, pid, currency_type="real")
        assert len(df) == 1

    def test_get_hero_opportunity_actions_currency_play_filters(self, cdb):
        """currency_type='play' filters opportunity actions to play sessions."""
        from pokerhero.analysis.queries import get_hero_opportunity_actions

        conn, pid = cdb
        df = get_hero_opportunity_actions(conn, pid, currency_type="play")
        assert len(df) == 1


# ---------------------------------------------------------------------------
# TestClassifyPlayer
# ---------------------------------------------------------------------------


class TestClassifyPlayer:
    """Tests for the classify_player pure function."""

    def test_tag_tight_aggressive(self):
        """VPIP < 25% and PFR/VPIP >= 0.5 → TAG."""
        from pokerhero.analysis.stats import classify_player

        assert classify_player(vpip_pct=20.0, pfr_pct=15.0, hands_played=20) == "TAG"

    def test_lag_loose_aggressive(self):
        """VPIP >= 25% and PFR/VPIP >= 0.5 → LAG."""
        from pokerhero.analysis.stats import classify_player

        assert classify_player(vpip_pct=35.0, pfr_pct=25.0, hands_played=20) == "LAG"

    def test_nit_tight_passive(self):
        """VPIP < 25% and PFR/VPIP < 0.5 → Nit."""
        from pokerhero.analysis.stats import classify_player

        assert classify_player(vpip_pct=15.0, pfr_pct=5.0, hands_played=20) == "Nit"

    def test_fish_loose_passive(self):
        """VPIP >= 25% and PFR/VPIP < 0.5 → Fish."""
        from pokerhero.analysis.stats import classify_player

        assert classify_player(vpip_pct=40.0, pfr_pct=10.0, hands_played=20) == "Fish"

    def test_below_min_hands_returns_none(self):
        """Fewer than 15 hands returns None (insufficient sample)."""
        from pokerhero.analysis.stats import classify_player

        assert classify_player(vpip_pct=30.0, pfr_pct=20.0, hands_played=14) is None

    def test_exactly_min_hands_classifies(self):
        """Exactly 15 hands is sufficient — returns a label, not None."""
        from pokerhero.analysis.stats import classify_player

        assert classify_player(vpip_pct=30.0, pfr_pct=20.0, hands_played=15) is not None

    def test_zero_vpip_is_nit(self):
        """VPIP of 0% (never entered pot) → Nit."""
        from pokerhero.analysis.stats import classify_player

        assert classify_player(vpip_pct=0.0, pfr_pct=0.0, hands_played=20) == "Nit"

    def test_boundary_vpip_25_is_loose(self):
        """VPIP exactly 25% is classified as Loose (≥ threshold)."""
        from pokerhero.analysis.stats import classify_player

        # 25% VPIP with high aggression → LAG
        result = classify_player(vpip_pct=25.0, pfr_pct=20.0, hands_played=20)
        assert result in ("LAG", "Fish")

    def test_min_hands_kwarg_raises_threshold(self):
        """Passing min_hands=20 causes hands_played=18 to return None."""
        from pokerhero.analysis.stats import classify_player

        assert (
            classify_player(vpip_pct=30.0, pfr_pct=20.0, hands_played=18, min_hands=20)
            is None
        )

    def test_min_hands_kwarg_allows_classification(self):
        """Passing min_hands=10 causes hands_played=12 to return an archetype."""
        from pokerhero.analysis.stats import classify_player

        result = classify_player(
            vpip_pct=30.0, pfr_pct=20.0, hands_played=12, min_hands=10
        )
        assert result is not None


# ---------------------------------------------------------------------------
# TestConfidenceTier
# ---------------------------------------------------------------------------


class TestConfidenceTier:
    """Tests for confidence_tier() in stats.py."""

    def test_below_50_is_preliminary(self):
        """Hands below 50 → 'preliminary' tier."""
        from pokerhero.analysis.stats import confidence_tier

        assert confidence_tier(1) == "preliminary"
        assert confidence_tier(49) == "preliminary"

    def test_50_to_99_is_standard(self):
        """50–99 hands → 'standard' tier."""
        from pokerhero.analysis.stats import confidence_tier

        assert confidence_tier(50) == "standard"
        assert confidence_tier(99) == "standard"

    def test_100_and_above_is_confirmed(self):
        """100+ hands → 'confirmed' tier."""
        from pokerhero.analysis.stats import confidence_tier

        assert confidence_tier(100) == "confirmed"
        assert confidence_tier(500) == "confirmed"


# ---------------------------------------------------------------------------
# TestSessionPlayerStats
# ---------------------------------------------------------------------------


class TestSessionPlayerStats:
    """Tests for get_session_player_stats — per-opponent aggregation for a session."""

    @pytest.fixture
    def sdb(self, tmp_path):
        """In-memory DB with one session, hero + two villains across 3 hands.

        hand 1: hero(vpip=1,pfr=1), alice(vpip=1,pfr=1), bob(vpip=0,pfr=0)
        hand 2: hero(vpip=1,pfr=0), alice(vpip=1,pfr=0), bob(vpip=1,pfr=0)
        hand 3: hero(vpip=0,pfr=0), alice(vpip=1,pfr=1), bob(vpip=1,pfr=1)

        Expected per-villain totals (excluding hero):
          alice: hands=3, vpip_count=3, pfr_count=2
          bob:   hands=3, vpip_count=2, pfr_count=1
        """
        from pokerhero.database.db import init_db, upsert_player

        conn = init_db(tmp_path / "sp.db")
        hero_pid = upsert_player(conn, "hero")
        alice_pid = upsert_player(conn, "alice")
        bob_pid = upsert_player(conn, "bob")

        conn.execute(
            "INSERT INTO sessions (game_type, limit_type, max_seats, small_blind,"
            " big_blind, ante, start_time, currency)"
            " VALUES ('NLHE','NL',9,100,200,0,'2026-01-01T10:00:00','PLAY')"
        )
        sid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        hand_data = [
            # (vpip_hero, pfr_hero, vpip_alice, pfr_alice, vpip_bob, pfr_bob)
            (1, 1, 1, 1, 0, 0),
            (1, 0, 1, 0, 1, 0),
            (0, 0, 1, 1, 1, 1),
        ]
        for i, (vh, ph, va, pa, vb, pb) in enumerate(hand_data):
            conn.execute(
                "INSERT INTO hands (source_hand_id, session_id, total_pot, rake,"
                " timestamp) VALUES (?, ?, 200, 5, ?)",
                (f"H{i}", sid, f"2026-01-01T10:0{i}:00"),
            )
            hid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            for pid, vpip, pfr in [
                (hero_pid, vh, ph),
                (alice_pid, va, pa),
                (bob_pid, vb, pb),
            ]:
                conn.execute(
                    "INSERT INTO hand_players (hand_id, player_id, position,"
                    " starting_stack, vpip, pfr, went_to_showdown, net_result)"
                    " VALUES (?, ?, 'BTN', 10000, ?, ?, 0, 0)",
                    (hid, pid, vpip, pfr),
                )
        conn.commit()
        return conn, int(hero_pid), int(sid)

    def test_returns_dataframe(self, sdb):
        """get_session_player_stats returns a DataFrame."""
        from pokerhero.analysis.queries import get_session_player_stats

        conn, hero_pid, sid = sdb
        result = get_session_player_stats(conn, sid, hero_pid)
        assert hasattr(result, "columns")

    def test_excludes_hero(self, sdb):
        """Hero is not included in the returned player stats."""
        from pokerhero.analysis.queries import get_session_player_stats

        conn, hero_pid, sid = sdb
        result = get_session_player_stats(conn, sid, hero_pid)
        assert "hero" not in result["username"].values

    def test_includes_both_villains(self, sdb):
        """Both alice and bob are present in the results."""
        from pokerhero.analysis.queries import get_session_player_stats

        conn, hero_pid, sid = sdb
        result = get_session_player_stats(conn, sid, hero_pid)
        usernames = set(result["username"])
        assert {"alice", "bob"} == usernames

    def test_hands_played_count(self, sdb):
        """hands_played is the correct count of hands for each villain."""
        from pokerhero.analysis.queries import get_session_player_stats

        conn, hero_pid, sid = sdb
        result = get_session_player_stats(conn, sid, hero_pid)
        alice = result[result["username"] == "alice"].iloc[0]
        assert int(alice["hands_played"]) == 3

    def test_vpip_count(self, sdb):
        """vpip_count matches the number of hands each villain voluntarily entered."""
        from pokerhero.analysis.queries import get_session_player_stats

        conn, hero_pid, sid = sdb
        result = get_session_player_stats(conn, sid, hero_pid)
        alice = result[result["username"] == "alice"].iloc[0]
        bob = result[result["username"] == "bob"].iloc[0]
        assert int(alice["vpip_count"]) == 3
        assert int(bob["vpip_count"]) == 2

    def test_pfr_count(self, sdb):
        """pfr_count matches the number of hands each villain raised preflop."""
        from pokerhero.analysis.queries import get_session_player_stats

        conn, hero_pid, sid = sdb
        result = get_session_player_stats(conn, sid, hero_pid)
        alice = result[result["username"] == "alice"].iloc[0]
        bob = result[result["username"] == "bob"].iloc[0]
        assert int(alice["pfr_count"]) == 2
        assert int(bob["pfr_count"]) == 1

    def test_required_columns_present(self, sdb):
        """Result DataFrame has the required columns."""
        from pokerhero.analysis.queries import get_session_player_stats

        conn, hero_pid, sid = sdb
        result = get_session_player_stats(conn, sid, hero_pid)
        assert {"username", "hands_played", "vpip_count", "pfr_count"}.issubset(
            result.columns
        )


# ---------------------------------------------------------------------------
# TestSessionAnalysisQueries — session-scoped queries for the Session Report
# ---------------------------------------------------------------------------


class TestSessionAnalysisQueries:
    """Tests for get_session_kpis, get_session_hero_actions, get_session_showdown_hands.

    Uses the shared db_with_data + hero_player_id + session_id module fixtures
    which ingest the two-hand play_money_two_hand_session fixture:
      Hand 1 — jsalinas96 BB, folds preflop (vpip=0, saw_flop=0, wts=0, net=-200)
      Hand 2 — jsalinas96 SB, calls/sees flop/loses showdown (vpip=1, saw_flop=1,
                wts=1, net=-2800). Bob shows [Kh Qd], hero shows [Tc Jd].
                Board: Jc 8h 3d Ks 2c.
    """

    # --- get_session_kpis ---

    def test_get_session_kpis_returns_dataframe(
        self, db_with_data, hero_player_id, session_id
    ):
        """get_session_kpis returns a DataFrame."""
        from pokerhero.analysis.queries import get_session_kpis

        result = get_session_kpis(db_with_data, session_id, hero_player_id)
        assert isinstance(result, pd.DataFrame)

    def test_get_session_kpis_has_expected_columns(
        self, db_with_data, hero_player_id, session_id
    ):
        """get_session_kpis returns columns compatible with existing stats functions."""
        from pokerhero.analysis.queries import get_session_kpis

        df = get_session_kpis(db_with_data, session_id, hero_player_id)
        assert {
            "vpip",
            "pfr",
            "went_to_showdown",
            "net_result",
            "big_blind",
            "saw_flop",
            "position",
        } <= set(df.columns)

    def test_get_session_kpis_row_count(self, db_with_data, hero_player_id, session_id):
        """One row per hand hero participated in (2 hands in fixture)."""
        from pokerhero.analysis.queries import get_session_kpis

        df = get_session_kpis(db_with_data, session_id, hero_player_id)
        assert len(df) == 2

    def test_get_session_kpis_vpip_sum(self, db_with_data, hero_player_id, session_id):
        """Only hand 2 is a VPIP hand → sum(vpip) == 1."""
        from pokerhero.analysis.queries import get_session_kpis

        df = get_session_kpis(db_with_data, session_id, hero_player_id)
        assert int(df["vpip"].sum()) == 1

    def test_get_session_kpis_saw_flop_sum(
        self, db_with_data, hero_player_id, session_id
    ):
        """Only hand 2 reaches the flop → sum(saw_flop) == 1."""
        from pokerhero.analysis.queries import get_session_kpis

        df = get_session_kpis(db_with_data, session_id, hero_player_id)
        assert int(df["saw_flop"].sum()) == 1

    def test_get_session_kpis_went_to_showdown_sum(
        self, db_with_data, hero_player_id, session_id
    ):
        """Only hand 2 reaches showdown → sum(went_to_showdown) == 1."""
        from pokerhero.analysis.queries import get_session_kpis

        df = get_session_kpis(db_with_data, session_id, hero_player_id)
        assert int(df["went_to_showdown"].sum()) == 1

    # --- get_session_hero_actions ---

    def test_get_session_hero_actions_returns_dataframe(
        self, db_with_data, hero_player_id, session_id
    ):
        """get_session_hero_actions returns a DataFrame."""
        from pokerhero.analysis.queries import get_session_hero_actions

        result = get_session_hero_actions(db_with_data, session_id, hero_player_id)
        assert isinstance(result, pd.DataFrame)

    def test_get_session_hero_actions_has_expected_columns(
        self, db_with_data, hero_player_id, session_id
    ):
        """get_session_hero_actions has columns compatible with aggression_factor."""
        from pokerhero.analysis.queries import get_session_hero_actions

        df = get_session_hero_actions(db_with_data, session_id, hero_player_id)
        assert {"hand_id", "street", "action_type", "position"} <= set(df.columns)

    def test_get_session_hero_actions_only_postflop_streets(
        self, db_with_data, hero_player_id, session_id
    ):
        """No PREFLOP rows — only FLOP, TURN, RIVER."""
        from pokerhero.analysis.queries import get_session_hero_actions

        df = get_session_hero_actions(db_with_data, session_id, hero_player_id)
        assert "PREFLOP" not in df["street"].values

    def test_get_session_hero_actions_row_count(
        self, db_with_data, hero_player_id, session_id
    ):
        """Hand 2: CHECK+CALL on FLOP, CHECK on TURN, CHECK+CALL on RIVER → 5 rows."""
        from pokerhero.analysis.queries import get_session_hero_actions

        df = get_session_hero_actions(db_with_data, session_id, hero_player_id)
        assert len(df) == 5

    # --- get_session_showdown_hands ---

    def test_get_session_showdown_hands_returns_dataframe(
        self, db_with_data, hero_player_id, session_id
    ):
        """get_session_showdown_hands returns a DataFrame."""
        from pokerhero.analysis.queries import get_session_showdown_hands

        result = get_session_showdown_hands(db_with_data, session_id, hero_player_id)
        assert isinstance(result, pd.DataFrame)

    def test_get_session_showdown_hands_has_expected_columns(
        self, db_with_data, hero_player_id, session_id
    ):
        """Result has all columns needed for EV computation."""
        from pokerhero.analysis.queries import get_session_showdown_hands

        df = get_session_showdown_hands(db_with_data, session_id, hero_player_id)
        assert {
            "hand_id",
            "source_hand_id",
            "hero_cards",
            "villain_username",
            "villain_cards",
            "board",
            "net_result",
            "total_pot",
        } <= set(df.columns)


# ===========================================================================
# TestHandRanking — HAND_RANKING list in ranges.py
# ===========================================================================


class TestHandRanking:
    """HAND_RANKING must be a well-formed 169-hand descending-strength list."""

    def test_length_is_169(self):
        from pokerhero.analysis.ranges import HAND_RANKING

        assert len(HAND_RANKING) == 169

    def test_no_duplicates(self):
        from pokerhero.analysis.ranges import HAND_RANKING

        assert len(set(HAND_RANKING)) == 169

    def test_aa_is_first(self):
        from pokerhero.analysis.ranges import HAND_RANKING

        assert HAND_RANKING[0] == "AA"

    def test_32o_is_last(self):
        from pokerhero.analysis.ranges import HAND_RANKING

        assert HAND_RANKING[-1] == "32o"

    def test_aks_in_top_10(self):
        from pokerhero.analysis.ranges import HAND_RANKING

        assert HAND_RANKING.index("AKs") < 10

    def test_all_pairs_present(self):
        from pokerhero.analysis.ranges import HAND_RANKING

        pairs = {
            "AA",
            "KK",
            "QQ",
            "JJ",
            "TT",
            "99",
            "88",
            "77",
            "66",
            "55",
            "44",
            "33",
            "22",
        }
        assert pairs <= set(HAND_RANKING)

    def test_suited_beats_offsuit_same_cards(self):
        """AKs must be ranked higher (earlier) than AKo."""
        from pokerhero.analysis.ranges import HAND_RANKING

        assert HAND_RANKING.index("AKs") < HAND_RANKING.index("AKo")

    def test_high_pair_beats_low_pair(self):
        """AA must be ranked higher than 22."""
        from pokerhero.analysis.ranges import HAND_RANKING

        assert HAND_RANKING.index("AA") < HAND_RANKING.index("22")

    def test_total_suited_count(self):
        """Must contain exactly 78 suited hands."""
        from pokerhero.analysis.ranges import HAND_RANKING

        assert sum(1 for h in HAND_RANKING if h.endswith("s")) == 78

    def test_total_offsuit_count(self):
        """Must contain exactly 78 offsuit (non-pair) hands."""
        from pokerhero.analysis.ranges import HAND_RANKING

        assert sum(1 for h in HAND_RANKING if h.endswith("o")) == 78

    def test_total_pair_count(self):
        """Must contain exactly 13 pocket pairs."""
        from pokerhero.analysis.ranges import HAND_RANKING

        assert sum(1 for h in HAND_RANKING if len(h) == 2) == 13


# ===========================================================================
# TestBuildRange — build_range returns correct hand slices
# ===========================================================================


class TestBuildRange:
    """build_range must return the right slice of HAND_RANKING per action type."""

    def test_2bet_returns_top_pfr_pct(self):
        """villain_preflop_action='2bet' → top pfr_pct% of HAND_RANKING."""
        from pokerhero.analysis.ranges import HAND_RANKING, build_range

        result = build_range(
            vpip_pct=26.0,
            pfr_pct=14.0,
            three_bet_pct=6.0,
            villain_preflop_action="2bet",
        )
        expected_n = round(169 * 14.0 / 100)
        assert result == HAND_RANKING[:expected_n]

    def test_3bet_returns_top_3bet_pct(self):
        """villain_preflop_action='3bet' → top three_bet_pct% of HAND_RANKING."""
        from pokerhero.analysis.ranges import HAND_RANKING, build_range

        result = build_range(
            vpip_pct=26.0,
            pfr_pct=14.0,
            three_bet_pct=6.0,
            villain_preflop_action="3bet",
        )
        expected_n = round(169 * 6.0 / 100)
        assert result == HAND_RANKING[:expected_n]

    def test_3bet_range_tighter_than_2bet_range(self):
        """3-bet range must be strictly smaller than 2-bet range."""
        from pokerhero.analysis.ranges import build_range

        r2 = build_range(26.0, 14.0, 6.0, "2bet")
        r3 = build_range(26.0, 14.0, 6.0, "3bet")
        assert len(r3) < len(r2)

    def test_4bet_uses_fixed_prior_ignores_pfr(self):
        """villain_preflop_action='4bet+' → top four_bet_prior% regardless of pfr."""
        from pokerhero.analysis.ranges import HAND_RANKING, build_range

        result = build_range(
            vpip_pct=26.0,
            pfr_pct=14.0,
            three_bet_pct=6.0,
            villain_preflop_action="4bet+",
            four_bet_prior=3.0,
        )
        expected_n = round(169 * 3.0 / 100)
        assert result == HAND_RANKING[:expected_n]

    def test_4bet_range_tighter_than_3bet_range(self):
        """4-bet range must be strictly smaller than 3-bet range."""
        from pokerhero.analysis.ranges import build_range

        r3 = build_range(26.0, 14.0, 6.0, "3bet")
        r4 = build_range(26.0, 14.0, 6.0, "4bet+", four_bet_prior=3.0)
        assert len(r4) < len(r3)

    def test_call_returns_flatting_slice(self):
        """villain_preflop_action='call' → hands between pfr% and vpip% cutoffs."""
        from pokerhero.analysis.ranges import HAND_RANKING, build_range

        result = build_range(
            vpip_pct=26.0,
            pfr_pct=14.0,
            three_bet_pct=6.0,
            villain_preflop_action="call",
        )
        lo = round(169 * 14.0 / 100)
        hi = round(169 * 26.0 / 100)
        assert result == HAND_RANKING[lo:hi]

    def test_call_range_does_not_overlap_2bet_range(self):
        """Flatting range must be disjoint from open-raise range."""
        from pokerhero.analysis.ranges import build_range

        r_call = set(build_range(26.0, 14.0, 6.0, "call"))
        r_2bet = set(build_range(26.0, 14.0, 6.0, "2bet"))
        assert r_call.isdisjoint(r_2bet)

    def test_unknown_action_raises_value_error(self):
        from pokerhero.analysis.ranges import build_range

        with pytest.raises(ValueError):
            build_range(26.0, 14.0, 6.0, "shove")

    def test_2bet_with_custom_hand_ranking(self):
        """build_range respects a custom hand_ranking list passed as argument."""
        from pokerhero.analysis.ranges import build_range

        custom = ["KK", "AA", "QQ", "JJ", "TT"]
        result = build_range(
            vpip_pct=26.0,
            pfr_pct=14.0,
            three_bet_pct=6.0,
            villain_preflop_action="2bet",
            hand_ranking=custom,
        )
        n = max(1, round(len(custom) * 14.0 / 100))
        assert result == custom[:n]

    def test_call_with_custom_hand_ranking(self):
        """build_range call-slice uses custom hand_ranking when provided."""
        from pokerhero.analysis.ranges import build_range

        custom = ["AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55"]
        result = build_range(
            vpip_pct=40.0,
            pfr_pct=20.0,
            three_bet_pct=6.0,
            villain_preflop_action="call",
            hand_ranking=custom,
        )
        lo = round(len(custom) * 20.0 / 100)
        hi = round(len(custom) * 40.0 / 100)
        assert result == custom[lo:hi]


# ===========================================================================
# TestBlendFunctions — Bayesian blend helpers
# ===========================================================================


class TestBlendFunctions:
    """blend_vpip, blend_pfr, blend_3bet must apply the Bayesian blend formula."""

    def test_blend_vpip_with_zero_hands_returns_prior(self):
        from pokerhero.analysis.ranges import blend_vpip

        assert blend_vpip(observed=None, n_hands=0) == pytest.approx(26.0)

    def test_blend_vpip_observed_none_returns_prior(self):
        from pokerhero.analysis.ranges import blend_vpip

        assert blend_vpip(observed=None, n_hands=50) == pytest.approx(26.0)

    def test_blend_vpip_large_sample_approaches_observed(self):
        """With n >> k, blended value should be very close to observed."""
        from pokerhero.analysis.ranges import blend_vpip

        result = blend_vpip(observed=40.0, n_hands=3000, prior=26.0, k=30)
        assert result == pytest.approx(40.0, abs=0.5)

    def test_blend_vpip_formula(self):
        """(n * obs + k * prior) / (n + k)."""
        from pokerhero.analysis.ranges import blend_vpip

        # n=30, k=30: equal weight → (30*40 + 30*26)/(30+30) = (1200+780)/60 = 33
        result = blend_vpip(observed=40.0, n_hands=30, prior=26.0, k=30)
        assert result == pytest.approx(33.0)

    def test_blend_pfr_default_prior_is_14(self):
        from pokerhero.analysis.ranges import blend_pfr

        assert blend_pfr(observed=None, n_hands=0) == pytest.approx(14.0)

    def test_blend_pfr_formula(self):
        from pokerhero.analysis.ranges import blend_pfr

        result = blend_pfr(observed=20.0, n_hands=30, prior=14.0, k=30)
        # (30*20 + 30*14) / 60 = (600+420)/60 = 17
        assert result == pytest.approx(17.0)

    def test_blend_3bet_default_prior_is_6(self):
        from pokerhero.analysis.ranges import blend_3bet

        assert blend_3bet(observed=None, n_hands=0) == pytest.approx(6.0)

    def test_blend_3bet_falls_back_to_prior_when_n_zero(self):
        """n_hands=0 with any observed value → prior returned."""
        from pokerhero.analysis.ranges import blend_3bet

        assert blend_3bet(observed=10.0, n_hands=0) == pytest.approx(6.0)

    def test_blend_3bet_formula(self):
        from pokerhero.analysis.ranges import blend_3bet

        result = blend_3bet(observed=12.0, n_hands=30, prior=6.0, k=30)
        # (30*12 + 30*6) / 60 = (360+180)/60 = 9
        assert result == pytest.approx(9.0)


class TestSessionAnalysisQueriesShowdown:
    """Continuation of TestSessionAnalysisQueries — showdown hand query tests."""

    def test_get_session_showdown_hands_row_count(
        self, db_with_data, hero_player_id, session_id
    ):
        """Hand 1 is a preflop fold (no cards known) — only hand 2 returned."""
        from pokerhero.analysis.queries import get_session_showdown_hands

        df = get_session_showdown_hands(db_with_data, session_id, hero_player_id)
        assert len(df) == 1

    def test_get_session_showdown_hands_hero_cards(
        self, db_with_data, hero_player_id, session_id
    ):
        """Hero hole cards in hand 2 are Tc Jd."""
        from pokerhero.analysis.queries import get_session_showdown_hands

        df = get_session_showdown_hands(db_with_data, session_id, hero_player_id)
        assert df.iloc[0]["hero_cards"] == "Tc Jd"

    def test_get_session_showdown_hands_villain_cards(
        self, db_with_data, hero_player_id, session_id
    ):
        """Villain (Bob) hole cards in hand 2 are Kh Qd."""
        from pokerhero.analysis.queries import get_session_showdown_hands

        df = get_session_showdown_hands(db_with_data, session_id, hero_player_id)
        assert df.iloc[0]["villain_cards"] == "Kh Qd"

    def test_get_session_showdown_hands_villain_username(
        self, db_with_data, hero_player_id, session_id
    ):
        """Villain username is Bob."""
        from pokerhero.analysis.queries import get_session_showdown_hands

        df = get_session_showdown_hands(db_with_data, session_id, hero_player_id)
        assert df.iloc[0]["villain_username"] == "Bob"

    def test_get_session_showdown_hands_board_not_empty(
        self, db_with_data, hero_player_id, session_id
    ):
        """Board string is non-empty for hand 2 (full 5-card board)."""
        from pokerhero.analysis.queries import get_session_showdown_hands

        df = get_session_showdown_hands(db_with_data, session_id, hero_player_id)
        assert df.iloc[0]["board"].strip() != ""

    def test_get_session_showdown_hands_net_result_negative(
        self, db_with_data, hero_player_id, session_id
    ):
        """Hero lost hand 2 → net_result < 0."""
        from pokerhero.analysis.queries import get_session_showdown_hands

        df = get_session_showdown_hands(db_with_data, session_id, hero_player_id)
        assert df.iloc[0]["net_result"] < 0


# ---------------------------------------------------------------------------
# TestComputeEquityMultiway
# ---------------------------------------------------------------------------


class TestComputeEquityMultiway:
    """Tests for compute_equity_multiway in stats.py."""

    def test_returns_float(self):
        """compute_equity_multiway returns a float."""
        from pokerhero.analysis.stats import compute_equity_multiway

        result = compute_equity_multiway("Ah Kh", "2c 3d", "Qh Jh Th 9d 2s", 500)
        assert isinstance(result, float)

    def test_high_equity_hand_near_one(self):
        """Royal flush (Ah Kh on QhJhTh9d2s) vs trash → equity near 1.0."""
        from pokerhero.analysis.stats import compute_equity_multiway

        result = compute_equity_multiway("Ah Kh", "2c 3d", "Qh Jh Th 9d 2s", 1000)
        assert result > 0.95

    def test_two_villains_reduces_equity(self):
        """Adding a second villain lowers hero equity vs heads-up."""
        from pokerhero.analysis.stats import compute_equity, compute_equity_multiway

        # Use a board where hero has a mediocre hand to amplify the difference
        heads_up = compute_equity("7s 8s", "2c 3d", "Ah Kd Qc", 2000)
        multiway = compute_equity_multiway("7s 8s", "2c 3d|Jc Tc", "Ah Kd Qc", 2000)
        assert multiway <= heads_up

    def test_single_villain_close_to_compute_equity(self):
        """Single villain produces equity within MC noise of compute_equity."""
        from pokerhero.analysis.stats import compute_equity, compute_equity_multiway

        # Use a large sample count to reduce Monte Carlo variance
        eq1 = compute_equity("Ah Kh", "2c 3d", "Qh Jh Th", 5000)
        eq2 = compute_equity_multiway("Ah Kh", "2c 3d", "Qh Jh Th", 5000)
        assert abs(eq1 - eq2) < 0.05


# ---------------------------------------------------------------------------
# TestGetSessionShowdownHandsMultiway
# ---------------------------------------------------------------------------


class TestGetSessionShowdownHandsMultiway:
    """get_session_showdown_hands: pipe-separated villain_cards for multiway pots."""

    @pytest.fixture()
    def multiway_db(self):
        """In-memory DB: one session, one multiway showdown hand (hero + 2 villains)."""

        from pokerhero.database.db import init_db, upsert_player

        conn = init_db(":memory:")

        hero_id = upsert_player(conn, "jsalinas96")
        v1_id = upsert_player(conn, "Alice")
        v2_id = upsert_player(conn, "Bob")

        conn.execute(
            """INSERT INTO sessions
               (game_type, limit_type, max_seats, small_blind, big_blind, ante,
                start_time, hero_buy_in, hero_cash_out, currency)
               VALUES (
                   'NLHE', 'No Limit', 6, 50, 100, 0,
                   '2026-01-01T00:00:00', 10000, 8000, 'PLAY'
               )"""
        )
        sid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        conn.execute(
            """INSERT INTO hands
               (session_id, source_hand_id, board_flop, board_turn, board_river,
                total_pot, rake, uncalled_bet_returned, timestamp)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (
                sid,
                "MULTI#1",
                "Ah Kh Qh",
                "Jh",
                "Th",
                9000,
                0,
                0,
                "2026-01-01T00:01:00",
            ),
        )
        hid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        # Hero — went to showdown, has cards, net result negative
        conn.execute(
            """INSERT INTO hand_players
               (hand_id, player_id, position, starting_stack, hole_cards,
                vpip, pfr, went_to_showdown, net_result)
               VALUES (?,?,'BTN',5000,'2c 3d',1,0,1,-3000)""",
            (hid, hero_id),
        )
        # Villain 1 — went to showdown, has cards
        conn.execute(
            """INSERT INTO hand_players
               (hand_id, player_id, position, starting_stack, hole_cards,
                vpip, pfr, went_to_showdown, net_result)
               VALUES (?,?,'SB',5000,'9c 8c',1,0,1,1500)""",
            (hid, v1_id),
        )
        # Villain 2 — went to showdown, has cards
        conn.execute(
            """INSERT INTO hand_players
               (hand_id, player_id, position, starting_stack, hole_cards,
                vpip, pfr, went_to_showdown, net_result)
               VALUES (?,?,'BB',5000,'7s 6s',1,0,1,1500)""",
            (hid, v2_id),
        )
        conn.commit()
        return conn, sid, hero_id

    def test_villain_cards_pipe_separated_for_multiway(self, multiway_db):
        """Two villains → villain_cards contains a pipe separator."""
        from pokerhero.analysis.queries import get_session_showdown_hands

        conn, sid, hero_id = multiway_db
        df = get_session_showdown_hands(conn, sid, hero_id)
        assert len(df) == 1
        assert "|" in str(df.iloc[0]["villain_cards"])

    def test_villain_username_comma_separated_for_multiway(self, multiway_db):
        """Two villains → villain_username contains both names."""
        from pokerhero.analysis.queries import get_session_showdown_hands

        conn, sid, hero_id = multiway_db
        df = get_session_showdown_hands(conn, sid, hero_id)
        username_field = str(df.iloc[0]["villain_username"])
        assert "Alice" in username_field
        assert "Bob" in username_field


# ---------------------------------------------------------------------------
# TestTrafficLight
# ---------------------------------------------------------------------------


class TestTrafficLight:
    """Tests for traffic_light() in targets.py."""

    def test_value_within_green_range_is_green(self):
        """Value between green_min and green_max → 'green'."""
        from pokerhero.analysis.targets import traffic_light

        assert traffic_light(15.0, 12.0, 18.0, 9.0, 21.0) == "green"

    def test_value_at_green_min_boundary_is_green(self):
        """Value exactly at green_min → 'green'."""
        from pokerhero.analysis.targets import traffic_light

        assert traffic_light(12.0, 12.0, 18.0, 9.0, 21.0) == "green"

    def test_value_at_green_max_boundary_is_green(self):
        """Value exactly at green_max → 'green'."""
        from pokerhero.analysis.targets import traffic_light

        assert traffic_light(18.0, 12.0, 18.0, 9.0, 21.0) == "green"

    def test_value_in_yellow_below_green_is_yellow(self):
        """Value below green_min but within yellow_min → 'yellow'."""
        from pokerhero.analysis.targets import traffic_light

        assert traffic_light(10.0, 12.0, 18.0, 9.0, 21.0) == "yellow"

    def test_value_in_yellow_above_green_is_yellow(self):
        """Value above green_max but within yellow_max → 'yellow'."""
        from pokerhero.analysis.targets import traffic_light

        assert traffic_light(20.0, 12.0, 18.0, 9.0, 21.0) == "yellow"

    def test_value_at_yellow_min_boundary_is_yellow(self):
        """Value exactly at yellow_min → 'yellow'."""
        from pokerhero.analysis.targets import traffic_light

        assert traffic_light(9.0, 12.0, 18.0, 9.0, 21.0) == "yellow"

    def test_value_at_yellow_max_boundary_is_yellow(self):
        """Value exactly at yellow_max → 'yellow'."""
        from pokerhero.analysis.targets import traffic_light

        assert traffic_light(21.0, 12.0, 18.0, 9.0, 21.0) == "yellow"

    def test_value_below_yellow_min_is_red(self):
        """Value below yellow_min → 'red'."""
        from pokerhero.analysis.targets import traffic_light

        assert traffic_light(5.0, 12.0, 18.0, 9.0, 21.0) == "red"

    def test_value_above_yellow_max_is_red(self):
        """Value above yellow_max → 'red'."""
        from pokerhero.analysis.targets import traffic_light

        assert traffic_light(25.0, 12.0, 18.0, 9.0, 21.0) == "red"

    def test_asymmetric_yellow_zone_below(self):
        """Asymmetric zones: wider yellow below than above → correctly classifies."""
        from pokerhero.analysis.targets import traffic_light

        # green 15-20, yellow 5-22 (wider below)
        assert traffic_light(8.0, 15.0, 20.0, 5.0, 22.0) == "yellow"
        assert traffic_light(4.0, 15.0, 20.0, 5.0, 22.0) == "red"
        assert traffic_light(21.0, 15.0, 20.0, 5.0, 22.0) == "yellow"
        assert traffic_light(23.0, 15.0, 20.0, 5.0, 22.0) == "red"


# ---------------------------------------------------------------------------
# TestReadTargetSettings
# ---------------------------------------------------------------------------


class TestReadTargetSettings:
    """Tests for read_target_settings() in targets.py."""

    def test_memory_db_returns_all_positions(self):
        """read_target_settings on :memory: conn returns entries for all 6 positions."""
        import sqlite3

        from pokerhero.analysis.targets import POSITIONS, read_target_settings

        conn = sqlite3.connect(":memory:")
        result = read_target_settings(conn)
        for stat in ("vpip", "pfr", "3bet"):
            for pos in POSITIONS:
                assert (stat, pos) in result, f"Missing ({stat!r}, {pos!r})"

    def test_memory_db_returns_target_bounds_typeddict(self):
        """Each value in the result has green_min/max and yellow_min/max keys."""
        import sqlite3

        from pokerhero.analysis.targets import read_target_settings

        conn = sqlite3.connect(":memory:")
        result = read_target_settings(conn)
        bounds = result[("vpip", "btn")]
        assert all(
            k in bounds for k in ("green_min", "green_max", "yellow_min", "yellow_max")
        )

    def test_memory_db_uses_defaults(self):
        """Values returned for :memory: match TARGET_DEFAULTS."""
        import sqlite3

        from pokerhero.analysis.targets import TARGET_DEFAULTS, read_target_settings

        conn = sqlite3.connect(":memory:")
        result = read_target_settings(conn)
        for key, expected in TARGET_DEFAULTS.items():
            assert result[key] == expected

    def test_persisted_values_override_defaults(self):
        """After upsert, read_target_settings returns the new values."""
        import sqlite3

        from pokerhero.analysis.targets import (
            ensure_target_settings_table,
            read_target_settings,
        )

        conn = sqlite3.connect(":memory:")
        ensure_target_settings_table(conn)
        conn.execute(
            "INSERT OR REPLACE INTO target_settings "
            "(stat, position, green_min, green_max, yellow_min, yellow_max) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            ("vpip", "btn", 30.0, 45.0, 24.0, 52.0),
        )
        conn.commit()
        result = read_target_settings(conn)
        assert result[("vpip", "btn")]["green_min"] == 30.0
        assert result[("vpip", "btn")]["green_max"] == 45.0


# ---------------------------------------------------------------------------
# TestSeedTargetDefaults — seed_target_defaults writes defaults to DB
# ---------------------------------------------------------------------------
class TestSeedTargetDefaults:
    """seed_target_defaults must INSERT OR IGNORE all 18 default rows."""

    def _empty_conn(self):
        import sqlite3

        from pokerhero.analysis.targets import ensure_target_settings_table

        conn = sqlite3.connect(":memory:")
        ensure_target_settings_table(conn)
        # Wipe any rows that ensure_target_settings_table may have seeded
        conn.execute("DELETE FROM target_settings")
        conn.commit()
        return conn

    def test_seed_populates_all_18_rows(self):
        """seed_target_defaults must write exactly 18 rows (3 stats × 6 positions)."""
        from pokerhero.analysis.targets import seed_target_defaults

        conn = self._empty_conn()
        seed_target_defaults(conn)
        count = conn.execute("SELECT COUNT(*) FROM target_settings").fetchone()[0]
        assert count == 18

    def test_seed_is_idempotent(self):
        """Calling seed_target_defaults twice must not duplicate rows."""
        from pokerhero.analysis.targets import seed_target_defaults

        conn = self._empty_conn()
        seed_target_defaults(conn)
        seed_target_defaults(conn)
        count = conn.execute("SELECT COUNT(*) FROM target_settings").fetchone()[0]
        assert count == 18

    def test_seed_does_not_overwrite_custom_values(self):
        """seed_target_defaults must not overwrite rows already in the table."""
        from pokerhero.analysis.targets import seed_target_defaults

        conn = self._empty_conn()
        conn.execute(
            "INSERT INTO target_settings"
            " (stat, position, green_min, green_max, yellow_min, yellow_max)"
            " VALUES ('vpip', 'btn', 99.0, 99.0, 99.0, 99.0)"
        )
        conn.commit()
        seed_target_defaults(conn)
        row = conn.execute(
            "SELECT green_min FROM target_settings WHERE stat='vpip' AND position='btn'"
        ).fetchone()
        assert row[0] == 99.0  # custom value must survive


# ===========================================================================
# TestExpandCombos — expand_combos expands hand strings to specific combos
# ===========================================================================


class TestExpandCombos:
    """expand_combos must expand shorthand hands to concrete card combos and
    filter out any combo containing a dead card."""

    def test_pair_expands_to_six_combos(self):
        """AA with no dead cards yields all 6 suit combinations."""
        from pokerhero.analysis.ranges import expand_combos

        result = expand_combos(["AA"], set())
        assert len(result) == 6

    def test_suited_hand_expands_to_four_combos(self):
        """AKs with no dead cards yields 4 combos (one per suit)."""
        from pokerhero.analysis.ranges import expand_combos

        result = expand_combos(["AKs"], set())
        assert len(result) == 4

    def test_offsuit_hand_expands_to_twelve_combos(self):
        """AKo with no dead cards yields 12 combos (4×3, same-suit excluded)."""
        from pokerhero.analysis.ranges import expand_combos

        result = expand_combos(["AKo"], set())
        assert len(result) == 12

    def test_pair_dead_card_removes_three_combos(self):
        """One dead card in a pair removes 3 of the 6 combos."""
        from pokerhero.analysis.ranges import expand_combos

        result = expand_combos(["AA"], {"Ah"})
        assert len(result) == 3
        assert all("Ah" not in combo for combo in result)

    def test_suited_dead_card_removes_one_combo(self):
        """Killing one card removes the one suited combo that uses it."""
        from pokerhero.analysis.ranges import expand_combos

        result = expand_combos(["AKs"], {"Ah"})
        assert len(result) == 3
        assert all("Ah" not in combo for combo in result)

    def test_offsuit_dead_card_removes_combos(self):
        """Dead Ah removes 3 combos from AKo (Ah Kc, Ah Kd, Ah Ks)."""
        from pokerhero.analysis.ranges import expand_combos

        result = expand_combos(["AKo"], {"Ah"})
        assert len(result) == 9
        assert all("Ah" not in combo for combo in result)

    def test_two_dead_cards_filter_correctly(self):
        """Two dead cards each from a different rank filter combined combos."""
        from pokerhero.analysis.ranges import expand_combos

        # Ah and Kh dead: removes AhKx and AxKh from AKo
        result = expand_combos(["AKo"], {"Ah", "Kh"})
        assert all("Ah" not in combo and "Kh" not in combo for combo in result)

    def test_all_combos_dead_returns_empty_for_that_hand(self):
        """If every combo of a hand is dead, it contributes nothing."""
        from pokerhero.analysis.ranges import expand_combos

        # Kill all four aces — no AA combos possible
        result = expand_combos(["AA"], {"Ac", "Ad", "Ah", "As"})
        assert result == []

    def test_empty_range_returns_empty_list(self):
        from pokerhero.analysis.ranges import expand_combos

        assert expand_combos([], set()) == []

    def test_combos_are_space_separated_card_strings(self):
        """Each combo in the output is a 'Xr Xs' space-separated string."""
        from pokerhero.analysis.ranges import expand_combos

        result = expand_combos(["AKs"], set())
        for combo in result:
            parts = combo.split()
            assert len(parts) == 2
            assert len(parts[0]) == 2
            assert len(parts[1]) == 2

    def test_mixed_range_total_combo_count(self):
        """AA(6) + AKs(4) + AKo(12) = 22 combos with no dead cards."""
        from pokerhero.analysis.ranges import expand_combos

        result = expand_combos(["AA", "AKs", "AKo"], set())
        assert len(result) == 22

    def test_no_duplicate_combos(self):
        """No combo appears twice in the output."""
        from pokerhero.analysis.ranges import expand_combos

        result = expand_combos(["AA", "KK", "QQ"], set())
        assert len(result) == len(set(result))


# ===========================================================================
# TestScoreComboVsBoard — equity-aware scoring with draw bonuses
# ===========================================================================


class TestScoreComboVsBoard:
    """score_combo_vs_board must rank draws favourably vs weak made hands."""

    def test_flush_draw_scores_lower_than_bottom_pair(self):
        """KhQh on Ah8h2c (flush draw) must score lower than 5s2d (bottom pair)."""
        from pokerhero.analysis.ranges import score_combo_vs_board

        flush_draw = score_combo_vs_board("Kh Qh", "Ah 8h 2c")
        bottom_pair = score_combo_vs_board("5s 2d", "Ah 8h 2c")
        assert flush_draw < bottom_pair

    def test_naked_ace_monotone_scores_lower_than_missed_offsuit(self):
        """AhQs on Kh8h2h (naked nut-flush card) beats pure air (Td4c)."""
        from pokerhero.analysis.ranges import score_combo_vs_board

        naked_ace = score_combo_vs_board("Ah Qs", "Kh 8h 2h")
        pure_air = score_combo_vs_board("Td 4c", "Kh 8h 2h")
        assert naked_ace < pure_air

    def test_oesd_scores_lower_than_pure_air(self):
        """JsTs on Qh9h2c (OESD) must score lower than 3d2c (pure air)."""
        from pokerhero.analysis.ranges import score_combo_vs_board

        oesd = score_combo_vs_board("Js Ts", "Qh 9h 2c")
        pure_air = score_combo_vs_board("3d 2c", "Qh 9h 2c")
        assert oesd < pure_air

    def test_gutshot_scores_lower_than_pure_air(self):
        """Js9d on Qh8h2c (gutshot needing T) scores below 3d2c."""
        from pokerhero.analysis.ranges import score_combo_vs_board

        gutshot = score_combo_vs_board("Js 9d", "Qh 8h 2c")
        pure_air = score_combo_vs_board("3d 2c", "Qh 8h 2c")
        assert gutshot < pure_air

    def test_two_overcards_score_lower_than_trash(self):
        """AhKd on Js7d2c (two overcards) must score lower than Qd9c (trash)."""
        from pokerhero.analysis.ranges import score_combo_vs_board

        overcards = score_combo_vs_board("Ah Kd", "Js 7d 2c")
        trash = score_combo_vs_board("Qd 9c", "Js 7d 2c")
        assert overcards < trash

    def test_flush_draw_plus_oesd_cumulative(self):
        """JhTh on Qh9h3d (flush draw AND OESD) scores lower than Kh7h (flush only)."""
        from pokerhero.analysis.ranges import score_combo_vs_board

        combo = score_combo_vs_board("Jh Th", "Qh 9h 3d")
        flush_only = score_combo_vs_board("Kh 7h", "Qh 9h 3d")
        assert combo < flush_only

    def test_made_hand_scores_lower_than_flush_draw(self):
        """Top set (AhAd on Ah8h2c) scores lower than flush draw (KhQh)."""
        from pokerhero.analysis.ranges import score_combo_vs_board

        top_set = score_combo_vs_board("Ah Ad", "Ah 8h 2c")
        flush_draw = score_combo_vs_board("Kh Qh", "Ah 8h 2c")
        assert top_set < flush_draw


# ===========================================================================
# TestContractRange — range contraction based on board + villain action
# ===========================================================================


class TestContractRange:
    """contract_range must keep stronger/drawing combos and honour passive vs
    aggressive thresholds."""

    def _all_combos(self) -> list[str]:
        """Return all combos for HAND_RANKING with no dead cards."""
        from pokerhero.analysis.ranges import HAND_RANKING, expand_combos

        return expand_combos(HAND_RANKING, set())

    def test_aggressive_action_keeps_fewer_combos_than_passive(self):
        """Bet/raise should keep fewer combos than check/call at same %."""
        from pokerhero.analysis.ranges import contract_range

        combos = self._all_combos()
        passive = contract_range(combos, "Ah 8h 2c", "check")
        aggressive = contract_range(combos, "Ah 8h 2c", "bet")
        assert len(aggressive) < len(passive)

    def test_passive_retains_continue_pct_passive_fraction(self):
        """Check action retains ~65% of combos by default."""
        from pokerhero.analysis.ranges import contract_range

        combos = self._all_combos()
        result = contract_range(combos, "Ah 8h 2c", "check")
        expected = round(len(combos) * 65.0 / 100)
        assert len(result) == expected

    def test_aggressive_retains_continue_pct_aggressive_fraction(self):
        """Bet action retains ~40% of combos by default."""
        from pokerhero.analysis.ranges import contract_range

        combos = self._all_combos()
        result = contract_range(combos, "Ah 8h 2c", "bet")
        expected = round(len(combos) * 40.0 / 100)
        assert len(result) == expected

    def test_returns_empty_when_zero_pct(self):
        """contract_range returns [] when continue_pct forces 0 combos."""
        from pokerhero.analysis.ranges import contract_range

        combos = self._all_combos()
        result = contract_range(
            combos,
            "Ah 8h 2c",
            "bet",
            continue_pct_aggressive=0.0,
        )
        assert result == []

    def test_raise_treated_as_aggressive(self):
        """'raise' action uses continue_pct_aggressive, same as 'bet'."""
        from pokerhero.analysis.ranges import contract_range

        combos = self._all_combos()
        bet_result = contract_range(combos, "Ah 8h 2c", "bet")
        raise_result = contract_range(combos, "Ah 8h 2c", "raise")
        assert len(raise_result) == len(bet_result)

    def test_call_treated_as_passive(self):
        """'call' action uses continue_pct_passive, same as 'check'."""
        from pokerhero.analysis.ranges import contract_range

        combos = self._all_combos()
        check_result = contract_range(combos, "Ah 8h 2c", "check")
        call_result = contract_range(combos, "Ah 8h 2c", "call")
        assert len(call_result) == len(check_result)

    def test_flush_draw_survives_aggressive_contraction(self):
        """KhQh (nut flush draw on Ah8h2c) must survive a 40% contraction."""
        from pokerhero.analysis.ranges import contract_range

        combos = ["Kh Qh", "5s 2d", "3c 2c", "Td 4c", "9s 6d"]
        result = contract_range(
            combos,
            "Ah 8h 2c",
            "bet",
            continue_pct_aggressive=40.0,
        )
        assert "Kh Qh" in result


class TestComputeEquityVsRange:
    """Integration tests for compute_equity_vs_range in stats.py."""

    def _fn(self, **kwargs):
        from pokerhero.analysis.stats import compute_equity_vs_range

        defaults = dict(
            hero_cards="Th Td",
            board="Ah Kh Qh",
            vpip_pct=25.0,
            pfr_pct=18.0,
            three_bet_pct=5.0,
            villain_preflop_action="2bet",
            villain_street_history=[],
            sample_count=80,
        )
        defaults.update(kwargs)
        return compute_equity_vs_range(**defaults)

    def test_flop_2bet_returns_valid_equity_and_positive_size(self):
        """FLOP 2-bet: equity in [0, 1] and contracted_size > 0."""
        equity, size = self._fn()
        assert 0.0 <= equity <= 1.0
        assert size > 0

    def test_3bet_range_smaller_than_2bet(self):
        """3-bet range is tighter: contracted_size(3bet) < contracted_size(2bet)."""
        _, size_2bet = self._fn(villain_preflop_action="2bet", pfr_pct=18.0)
        _, size_3bet = self._fn(villain_preflop_action="3bet", three_bet_pct=5.0)
        assert size_3bet < size_2bet

    def test_river_two_street_history_contracts_range(self):
        """2-street history produces smaller range than no history (same board)."""
        board_river = "Ah Kh Qh 2c 3d"
        _, size_no_history = self._fn(board=board_river)
        _, size_with_history = self._fn(
            board=board_river,
            villain_street_history=[
                ("Ah Kh Qh", "bet"),
                ("Ah Kh Qh 2c", "call"),
            ],
        )
        assert size_with_history < size_no_history

    def test_range_collapse_returns_zero(self):
        """Contraction leaving < 5 combos returns (0.0, 0)."""
        equity, size = self._fn(
            hero_cards="2c 3d",
            board="5s 6h 7c",
            villain_preflop_action="4bet+",
            four_bet_prior=0.8,  # top 0.8% → 1 hand (AA = 6 combos) → 40% = 2
            villain_street_history=[("5s 6h 7c", "bet")],
        )
        assert equity == 0.0
        assert size == 0

    def test_4bet_smaller_range_than_2bet(self):
        """4bet+ uses fixed prior (3%), not villain's pfr (40%)."""
        _, size_4bet = self._fn(
            villain_preflop_action="4bet+",
            pfr_pct=40.0,
            four_bet_prior=3.0,
        )
        _, size_2bet = self._fn(
            villain_preflop_action="2bet",
            pfr_pct=40.0,
        )
        assert size_4bet < size_2bet
