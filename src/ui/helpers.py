"""UI helpers: safe_addstr, wait_key, team name formatting, loading bar, and scroll keys."""
import curses

# Keys that trigger page scroll (up/down). Use U/D so keyboards without PgUp/PgDn work.
PAGE_SCROLL_UP_KEYS = (curses.KEY_PPAGE, ord("u"), ord("U"))
PAGE_SCROLL_DOWN_KEYS = (curses.KEY_NPAGE, ord("d"), ord("D"))


def apply_page_scroll_key(key, scroll_offset, view_height, content_height):
    """
    If key is page-scroll up or down, return new scroll offset. Otherwise return None.
    Reusable for any scrollable screen (help, team page, etc.).
    """
    if view_height <= 0 or content_height <= 0:
        return None
    page_size = max(1, view_height // 2)
    max_offset = max(0, content_height - view_height)
    if key in PAGE_SCROLL_UP_KEYS:
        return max(0, scroll_offset - page_size)
    if key in PAGE_SCROLL_DOWN_KEYS:
        return min(max_offset, scroll_offset + page_size)
    return None


def clamp_scroll_offset(scroll_offset, view_height, content_height):
    """Clamp scroll offset so the visible window stays within content. Reusable for any scrollable view."""
    if view_height <= 0 or content_height <= view_height:
        return 0
    max_offset = content_height - view_height
    return max(0, min(scroll_offset, max_offset))


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
