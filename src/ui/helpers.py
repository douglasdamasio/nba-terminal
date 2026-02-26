"""UI helpers: safe_addstr, wait_key, team name formatting, and loading bar."""
import curses


def draw_loading_bar(stdscr, row, width, progress=0.0):
    """Draw a horizontal loading bar. progress in 0.0..1.0; if > 1 use as indeterminate (cycling)."""
    try:
        bar_width = max(10, width - 4)
        if 0 <= progress <= 1:
            filled = int(bar_width * progress)
        else:
            # Indeterminate: use progress as phase (e.g. (time * 2) % 1.0)
            phase = (progress % 1.0) if progress > 1 else (progress % 1.0)
            filled = int(bar_width * 0.3) + int((bar_width * 0.4) * phase)
            filled = min(filled, bar_width)
        bar_border = "[" + " " * bar_width + "]"
        bar_inner = " " * bar_width
        try:
            stdscr.addstr(row, 0, " " + bar_border[: width - 1], curses.A_DIM)
            if filled > 0:
                block = "=" * filled + " " * (bar_width - filled)
                stdscr.addstr(row, 2, block[: bar_width], curses.A_BOLD)
        except curses.error:
            pass
    except curses.error:
        pass


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
