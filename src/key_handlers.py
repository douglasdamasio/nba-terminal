"""Key-to-action mapping for the app (dashboard). Avoids a large switch in main."""
from __future__ import annotations

import curses
from typing import Optional


def get_action(key: int, game_count: int = 0) -> Optional[str]:
    """
    Convert curses key code to action string.
    Returns None if the key is not a known action or key == -1 (timeout).

    Actions: quit, refresh, config, help, filter, teams, date, today,
             prev_day, next_day, game:0 .. game:N (N = min(19, game_count-1)).
    """
    if key == -1:
        return None
    if key in (ord("q"), ord("Q")):
        return "quit"
    if key in (ord("r"), ord("R")):
        return "refresh"
    if key in (ord("c"), ord("C")):
        return "config"
    if key in (ord("?"), ord("h"), ord("H")):
        return "help"
    if key in (ord("f"), ord("F")):
        return "filter"
    if key in (ord("t"), ord("T")):
        return "teams"
    if key in (ord("g"), ord("G")):
        return "date"
    if key in (ord("l"), ord("L")):
        return "favorite_team"
    if key in (ord("d"), ord("D")):
        return "today"
    if key in (ord(","), ord("["), curses.KEY_LEFT):
        return "prev_day"
    if key in (ord("."), ord("]"), curses.KEY_RIGHT):
        return "next_day"
    if key == curses.KEY_UP:
        return "scroll_up"
    if key == curses.KEY_DOWN:
        return "scroll_down"
    if ord("1") <= key <= ord("9"):
        idx = key - ord("1")
        if 0 <= idx < game_count:
            return f"game:{idx}"
        return None
    if key == ord("0"):
        idx = 9
        if idx < game_count:
            return f"game:{idx}"
        return None
    if ord("a") <= key <= ord("j"):
        idx = 10 + (key - ord("a"))
        if idx < game_count:
            return f"game:{idx}"
        return None
    return None
