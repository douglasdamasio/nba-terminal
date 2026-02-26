"""Tests for key_handlers: get_action mapping."""
import sys
import unittest
from pathlib import Path

# Avoid importing curses on headless CI if needed; get_action only uses ord() and curses.KEY_*
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

try:
    import curses
    from key_handlers import get_action
    _curses_ok = True
except ImportError:
    _curses_ok = False


@unittest.skipIf(not _curses_ok, "curses not available")
class TestGetAction(unittest.TestCase):
    def test_timeout_returns_none(self):
        self.assertIsNone(get_action(-1, 10))

    def test_quit(self):
        self.assertEqual(get_action(ord("q"), 5), "quit")
        self.assertEqual(get_action(ord("Q"), 5), "quit")

    def test_refresh(self):
        self.assertEqual(get_action(ord("r"), 5), "refresh")
        self.assertEqual(get_action(ord("R"), 5), "refresh")

    def test_config(self):
        self.assertEqual(get_action(ord("c"), 5), "config")
        self.assertEqual(get_action(ord("C"), 5), "config")

    def test_help(self):
        self.assertEqual(get_action(ord("?"), 5), "help")
        self.assertEqual(get_action(ord("h"), 5), "help")
        self.assertEqual(get_action(ord("H"), 5), "help")

    def test_filter(self):
        self.assertEqual(get_action(ord("f"), 5), "filter")
        self.assertEqual(get_action(ord("F"), 5), "filter")

    def test_teams(self):
        self.assertEqual(get_action(ord("t"), 5), "teams")
        self.assertEqual(get_action(ord("T"), 5), "teams")

    def test_date(self):
        self.assertEqual(get_action(ord("g"), 5), "date")
        self.assertEqual(get_action(ord("G"), 5), "date")

    def test_favorite_team(self):
        self.assertEqual(get_action(ord("l"), 5), "favorite_team")
        self.assertEqual(get_action(ord("L"), 5), "favorite_team")

    def test_today(self):
        self.assertEqual(get_action(ord("d"), 5), "today")
        self.assertEqual(get_action(ord("D"), 5), "today")

    def test_prev_day(self):
        self.assertEqual(get_action(ord(","), 5), "prev_day")
        self.assertEqual(get_action(ord("["), 5), "prev_day")
        self.assertEqual(get_action(curses.KEY_LEFT, 5), "prev_day")

    def test_next_day(self):
        self.assertEqual(get_action(ord("."), 5), "next_day")
        self.assertEqual(get_action(ord("]"), 5), "next_day")
        self.assertEqual(get_action(curses.KEY_RIGHT, 5), "next_day")

    def test_scroll_up_down(self):
        self.assertEqual(get_action(curses.KEY_UP, 5), "scroll_up")
        self.assertEqual(get_action(curses.KEY_DOWN, 5), "scroll_down")

    def test_game_index_1_to_9(self):
        self.assertEqual(get_action(ord("1"), 5), "game:0")
        self.assertEqual(get_action(ord("5"), 5), "game:4")
        self.assertEqual(get_action(ord("9"), 9), "game:8")
        self.assertIsNone(get_action(ord("9"), 5))  # only 5 games: index 8 out of range
        self.assertIsNone(get_action(ord("1"), 0))

    def test_game_index_0_is_ninth_game(self):
        self.assertEqual(get_action(ord("0"), 10), "game:9")
        self.assertIsNone(get_action(ord("0"), 9))

    def test_game_index_a_to_j(self):
        self.assertEqual(get_action(ord("a"), 11), "game:10")
        self.assertEqual(get_action(ord("j"), 20), "game:19")
        self.assertIsNone(get_action(ord("a"), 10))
        self.assertIsNone(get_action(ord("k"), 20))

    def test_unknown_key_returns_none(self):
        self.assertIsNone(get_action(ord("x"), 10))
        self.assertIsNone(get_action(ord(" "), 10))


if __name__ == "__main__":
    unittest.main()
