"""Help screen with keyboard shortcut list and full explanations."""

import curses

import config


def show_help(stdscr, cfg):
    """Display the help screen with all shortcuts. [U][D] or PgUp/PgDn to scroll. Any other key closes."""
    height, width = stdscr.getmaxyx()
    stdscr.clear()

    title = config.get_text(cfg, "help_title")
    press_key = config.get_text(cfg, "help_press_key")

    lines = [
        "",
        config.get_text(cfg, "help_intro"),
        "",
        config.get_text(cfg, "help_section_games"),
        config.get_text(cfg, "help_games_select"),
        config.get_text(cfg, "help_games_nav"),
        config.get_text(cfg, "help_games_today"),
        config.get_text(cfg, "help_games_date"),
        config.get_text(cfg, "help_games_filter"),
        "",
        config.get_text(cfg, "help_section_team"),
        config.get_text(cfg, "help_team_scroll"),
        config.get_text(cfg, "help_team_player"),
        config.get_text(cfg, "help_team_enter"),
        "",
        config.get_text(cfg, "help_section_global"),
        config.get_text(cfg, "help_global_teams"),
        config.get_text(cfg, "help_global_fav"),
        config.get_text(cfg, "help_global_refresh"),
        config.get_text(cfg, "help_global_config"),
        config.get_text(cfg, "help_global_help"),
        config.get_text(cfg, "help_global_quit"),
        "",
    ]

    content_start = 2
    view_height = max(1, height - content_start - 2)
    total_lines = len(lines)
    scroll_offset = 0

    while True:
        stdscr.clear()
        try:
            stdscr.addstr(0, 0, title, curses.A_BOLD | curses.A_REVERSE)
            for i in range(view_height):
                idx = scroll_offset + i
                if idx < total_lines:
                    line = lines[idx][: width - 1]
                    stdscr.addstr(content_start + i, 0, line)
            footer = f" {press_key} "
            if total_lines > view_height:
                footer = config.get_text(cfg, "team_page_scroll_hint") + "  " + footer
            stdscr.addstr(height - 1, 0, footer[: width - 1], curses.A_DIM)
        except curses.error:
            pass
        stdscr.refresh()
        stdscr.nodelay(False)
        key = stdscr.getch()
        stdscr.nodelay(True)

        new_offset = apply_page_scroll_key(key, scroll_offset, view_height, total_lines)
        if new_offset is not None:
            scroll_offset = new_offset
        else:
            break
