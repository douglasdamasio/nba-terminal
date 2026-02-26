"""Integration tests for API client with mocked nba_api endpoints."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

try:
    import pandas as pd
except ImportError:
    pd = None

try:
    import api
except ImportError as e:
    api = None
    _api_import_error = e
else:
    _api_import_error = None


@unittest.skipIf(api is None or pd is None, "api or pandas not available (install project deps)")
class TestApiClientFetchGames(unittest.TestCase):
    """Test fetch_games with mocked scoreboard."""

    @patch("api._with_retry")
    def test_fetch_games_returns_list_and_date(self, mock_retry):
        mock_retry.side_effect = lambda thunk: thunk()
        mock_board = MagicMock()
        mock_board.games.get_dict.return_value = [
            {
                "gameId": "001",
                "gameStatusText": "Final",
                "awayTeam": {"teamTricode": "LAL", "score": 100},
                "homeTeam": {"teamTricode": "BOS", "score": 98},
                "gameTimeUTC": "2025-02-16T00:00:00Z",
            }
        ]
        mock_board.score_board_date = "2025-02-16"

        with patch("api.scoreboard.ScoreBoard", return_value=mock_board):
            client = api.ApiClient()
            client._cache_games.clear()
            games, date_str = client.fetch_games(None)
        self.assertIsInstance(games, list)
        self.assertIsInstance(date_str, str)
        if games:
            self.assertIn("awayTeam", games[0])
            self.assertIn("homeTeam", games[0])


@unittest.skipIf(api is None or pd is None, "api or pandas not available")
class TestApiClientFetchStandings(unittest.TestCase):
    """Test fetch_standings with mocked LeagueStandingsV3."""

    @patch("api._disk_cache_set")
    @patch("api._disk_cache_get", return_value=None)
    @patch("api._with_retry")
    def test_fetch_standings_returns_east_west(self, mock_retry, mock_disk_get, mock_disk_set):
        mock_retry.side_effect = lambda thunk: thunk()
        df = pd.DataFrame({
            "Conference": ["East", "East", "West", "West"],
            "PlayoffRank": [1, 2, 1, 2],
            "TeamCity": ["Boston", "New York", "LA", "Golden State"],
            "TeamName": ["Celtics", "Knicks", "Lakers", "Warriors"],
            "WINS": [40, 35, 38, 36],
            "LOSSES": [10, 15, 12, 14],
            "WinPCT": [0.8, 0.7, 0.76, 0.72],
        })
        mock_standings = MagicMock()
        mock_standings.get_data_frames.return_value = [df]

        with patch("api.leaguestandingsv3.LeagueStandingsV3", return_value=mock_standings):
            client = api.ApiClient()
            client._cache_standings.clear()
            east, west = client.fetch_standings()
        self.assertIsNotNone(east)
        self.assertIsNotNone(west)
        self.assertFalse(east.empty)
        self.assertFalse(west.empty)
        self.assertEqual(list(east["Conference"].unique()), ["East"])
        self.assertEqual(list(west["Conference"].unique()), ["West"])


@unittest.skipIf(api is None or pd is None, "api or pandas not available")
class TestApiClientHeadToHead(unittest.TestCase):
    """Test fetch_head_to_head with mocked TeamGameLog."""

    @patch("api._with_retry")
    def test_fetch_head_to_head_structure(self, mock_retry):
        df_a = pd.DataFrame([
            {"GAME_DATE": "2025-02-01", "MATCHUP": "LAL vs. BOS", "WL": "W", "PTS": 110},
            {"GAME_DATE": "2024-12-15", "MATCHUP": "LAL @ BOS", "WL": "L", "PTS": 98},
        ])
        df_b = pd.DataFrame([
            {"GAME_DATE": "2025-02-01", "MATCHUP": "BOS vs. LAL", "WL": "L", "PTS": 108},
            {"GAME_DATE": "2024-12-15", "MATCHUP": "BOS @ LAL", "WL": "W", "PTS": 105},
        ])
        mock_retry.side_effect = lambda f: f()

        mock_a = MagicMock()
        mock_a.get_data_frames.return_value = [df_a]
        mock_b = MagicMock()
        mock_b.get_data_frames.return_value = [df_b]

        with patch("api.teamgamelog.TeamGameLog", side_effect=[mock_a, mock_b]):
            client = api.ApiClient()
            with patch.object(client, "_rate_limit"):
                h2h = client.fetch_head_to_head(1610612747, 1610612738)

        self.assertIn("last_meeting", h2h)
        self.assertIn("season_series", h2h)
        self.assertIn("wins_a", h2h["season_series"])
        self.assertIn("wins_b", h2h["season_series"])
        self.assertIn("games", h2h["season_series"])
        self.assertEqual(len(h2h["season_series"]["games"]), 2)
        self.assertIsNotNone(h2h["last_meeting"])
        self.assertEqual(h2h["last_meeting"]["date"], "2025-02-01")
        self.assertEqual(h2h["season_series"]["wins_a"], 1)
        self.assertEqual(h2h["season_series"]["wins_b"], 1)


@unittest.skipIf(api is None, "api not available")
class TestUserFacingError(unittest.TestCase):
    """Test _user_facing_error maps exceptions to short messages."""

    def test_timeout(self):
        msg = api._user_facing_error(ConnectionError("Connection timed out"), "Error")
        self.assertIn("timeout", msg.lower())

    def test_connection(self):
        msg = api._user_facing_error(OSError("Network unreachable"), "Error")
        self.assertIn("connection", msg.lower())

    def test_rate_limit(self):
        msg = api._user_facing_error(Exception("429 Too Many Requests"), "Error")
        self.assertIn("Too many", msg)

    def test_not_found(self):
        msg = api._user_facing_error(Exception("404 not found"), "Error")
        self.assertIn("not found", msg.lower())

    def test_long_message_truncated(self):
        long_msg = "x" * 80
        msg = api._user_facing_error(ValueError(long_msg), "Fail")
        self.assertIn("...", msg)
        self.assertLess(len(msg), 80)


@unittest.skipIf(api is None, "api not available")
class TestBuildQuarterScores(unittest.TestCase):
    """Test pure helper build_quarter_scores (already in test_pure, keep for api integration)."""

    def test_build_quarter_scores_ot(self):
        away = {"periods": [{"period": 1, "score": 25}, {"period": 2, "score": 25}, {"period": 3, "score": 25}, {"period": 4, "score": 25}, {"period": 5, "score": 10}], "score": 110}
        home = {"periods": [{"period": 1, "score": 20}, {"period": 2, "score": 28}, {"period": 3, "score": 22}, {"period": 4, "score": 25}, {"period": 5, "score": 12}], "score": 112}
        out = api.build_quarter_scores(away, home)
        self.assertIsNotNone(out)
        self.assertIn("OT", out["headers"])
        self.assertEqual(out["away"][-2], 10)
        self.assertEqual(out["home"][-2], 12)


if __name__ == "__main__":
    unittest.main()
