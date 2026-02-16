"""Helpers de UI: safe_addstr, wait_key e formatação de nome de time."""
import curses


def safe_addstr(stdscr, row, col, text, attr=0, max_width=None):
    try:
        if max_width is not None and len(text) > max_width:
            text = text[: max_width - 1]
        stdscr.addstr(row, col, text, attr)
        return True
    except curses.error:
        return False


def wait_key(stdscr):
    stdscr.nodelay(False)
    stdscr.getch()
    stdscr.nodelay(True)


def format_team_name(team_dict):
    if not team_dict:
        return ""
    return f"{team_dict.get('teamCity', '')} {team_dict.get('teamName', '')}".strip()
