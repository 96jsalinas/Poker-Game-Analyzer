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

    def test_cbet_pct_empty_returns_zero(self):
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
        assert result > 0

    def test_losing_hand_is_negative_ev(self):
        """Hero has trash vs royal flush on complete board → negative EV."""
        from pokerhero.analysis.stats import compute_ev

        # Hero: 2c 3d, Villain: Ah Kh, Board: Qh Jh Th 9d 2s
        result = compute_ev("2c 3d", "Ah Kh", "Qh Jh Th 9d 2s", 100.0, 300.0)
        assert result is not None
        assert result < 0

    def test_ev_formula_at_river(self):
        """Complete board → exact equity; EV ≈ equity*pot - (1-equity)*risked."""
        from pokerhero.analysis.stats import compute_ev

        # Hero: Ah Kh vs 2c 3d on complete board → equity=1.0
        # EV = 1.0 * 300 - 0 * 100 = 300
        result = compute_ev("Ah Kh", "2c 3d", "Qh Jh Th 9d 2s", 100.0, 300.0)
        assert result is not None
        assert result == pytest.approx(300.0, abs=5.0)

    def test_ev_partial_board_in_range(self):
        """Partial board (flop only) → equity between 0 and 1 for non-trivial hand."""
        from pokerhero.analysis.stats import compute_ev

        # Hero: Ah Kh (nut flush draw), Villain: 2c 2d (pair of 2s), Board: Qh Jh 2s
        # Villain has set of 2s, hero has many outs (flush + straight outs)
        result = compute_ev("Ah Kh", "2c 2d", "Qh Jh 2s", 100.0, 300.0)
        assert result is not None
        # Result is some finite float (not trivially 300 or -100)
        assert isinstance(result, float)


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
        """EV should equal equity*pot_to_win - (1-equity)*amount_risked."""
        from pokerhero.analysis.stats import compute_ev

        amount_risked, pot_to_win = 100.0, 300.0
        ev, equity = compute_ev(
            "Ah Kh", "2c 3d", "Qh Jh Th 9d 2s", amount_risked, pot_to_win
        )
        expected_ev = equity * pot_to_win - (1.0 - equity) * amount_risked
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
