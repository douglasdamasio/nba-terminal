"""Tests for pure functions used by the NBA Terminal App."""
import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from core import categorize_games, format_live_clock, game_index_label
from ui.screens import parse_date_string
import constants
import api


class TestCategorizeGames(unittest.TestCase):
    def test_empty(self):
        em, nao, fin = categorize_games([])
        self.assertEqual(em, [])
        self.assertEqual(nao, [])
        self.assertEqual(fin, [])

    def test_final(self):
        g = {"gameStatusText": "Final", "awayTeam": {"score": 100}, "homeTeam": {"score": 98}}
        em, nao, fin = categorize_games([g])
        self.assertEqual(len(fin), 1)
        self.assertEqual(len(em), 0)
        self.assertEqual(len(nao), 0)

    def test_final_ot(self):
        g = {"gameStatusText": "Final/OT", "awayTeam": {"score": 110}, "homeTeam": {"score": 108}}
        em, nao, fin = categorize_games([g])
        self.assertEqual(len(fin), 1)
        self.assertEqual(len(em), 0)
        self.assertEqual(len(nao), 0)

    def test_in_progress(self):
        g = {"gameStatusText": "Q3", "awayTeam": {"score": 75}, "homeTeam": {"score": 70}}
        em, nao, fin = categorize_games([g])
        self.assertEqual(len(em), 1)
        self.assertEqual(len(nao), 0)
        self.assertEqual(len(fin), 0)

    def test_not_started(self):
        g = {"gameStatusText": "7:00 PM", "awayTeam": {}, "homeTeam": {}}
        em, nao, fin = categorize_games([g])
        self.assertEqual(len(nao), 1)
        self.assertEqual(len(em), 0)
        self.assertEqual(len(fin), 0)

    def test_mixed(self):
        games = [
            {"gameStatusText": "Final", "awayTeam": {"score": 90}, "homeTeam": {"score": 85}},
            {"gameStatusText": "Q2", "awayTeam": {"score": 45}, "homeTeam": {"score": 40}},
            {"gameStatusText": "8:00 PM", "awayTeam": {}, "homeTeam": {}},
        ]
        em, nao, fin = categorize_games(games)
        self.assertEqual(len(em), 1)
        self.assertEqual(len(nao), 1)
        self.assertEqual(len(fin), 1)


class TestFormatLiveClock(unittest.TestCase):
    def test_status_text(self):
        self.assertEqual(format_live_clock({"gameStatusText": "Q4 1:04"}), "Q4 1:04")
        self.assertEqual(format_live_clock({"gameStatusText": "Halftime"}), "Halftime")

    def test_from_period_clock(self):
        g = {"gameStatusText": "", "period": 3, "gameClock": "PT5M30S"}
        self.assertEqual(format_live_clock(g), "Q3 5:30")

    def test_empty(self):
        self.assertEqual(format_live_clock({}), "-")
        self.assertEqual(format_live_clock({"gameStatusText": ""}), "-")


class TestGetTricodeFromTeam(unittest.TestCase):
    def test_known_teams(self):
        self.assertEqual(constants.get_tricode_from_team("Los Angeles Lakers"), "LAL")
        self.assertEqual(constants.get_tricode_from_team("Boston Celtics"), "BOS")
        self.assertEqual(constants.get_tricode_from_team("  LA Lakers  "), "LAL")

    def test_unknown(self):
        self.assertEqual(constants.get_tricode_from_team("Unknown Team"), "")


class TestGameIndexLabel(unittest.TestCase):
    def test_labels(self):
        self.assertEqual(game_index_label(0), " [1] ")
        self.assertEqual(game_index_label(8), " [9] ")
        self.assertEqual(game_index_label(9), " [0] ")
        self.assertEqual(game_index_label(10), " [a] ")
        self.assertEqual(game_index_label(11), " [b] ")


class TestParseDateString(unittest.TestCase):
    def test_iso(self):
        self.assertEqual(parse_date_string("2025-02-13"), date(2025, 2, 13))

    def test_ddmmyyyy(self):
        self.assertEqual(parse_date_string("13/02/2025"), date(2025, 2, 13))
        self.assertEqual(parse_date_string("13-02-2025"), date(2025, 2, 13))

    def test_invalid(self):
        self.assertIsNone(parse_date_string(""))
        self.assertIsNone(parse_date_string("  "))
        self.assertIsNone(parse_date_string("invalid"))
        self.assertIsNone(parse_date_string("02/13/2025"))


class TestBuildQuarterScores(unittest.TestCase):
    def test_empty(self):
        self.assertIsNone(api.build_quarter_scores({}, {}))

    def test_from_periods(self):
        away = {"periods": [{"period": 1, "score": 25}, {"period": 2, "score": 22}], "score": 47}
        home = {"periods": [{"period": 1, "score": 20}, {"period": 2, "score": 28}], "score": 48}
        out = api.build_quarter_scores(away, home)
        self.assertIsNotNone(out)
        self.assertEqual(out["headers"], ["Q1", "Q2", "Q3", "Q4", "Total"])
        self.assertEqual(out["away"], [25, 22, 0, 0, 47])
        self.assertEqual(out["home"], [20, 28, 0, 0, 48])


if __name__ == "__main__":
    unittest.main()
