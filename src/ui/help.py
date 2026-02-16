"""Tela de ajuda com lista de atalhos do teclado."""

import curses

import config
from .helpers import wait_key


def show_help(stdscr, cfg):
    """Exibe a tela de ajuda com todos os atalhos. Qualquer tecla fecha."""
    height, width = stdscr.getmaxyx()
    stdscr.clear()

    title = config.get_text(cfg, "help_title")
    press_key = config.get_text(cfg, "help_press_key")

    lines = [
        "",
        " [1-9] [0] [a-j]  " + config.get_text(cfg, "footer_games"),
        " [T]               " + config.get_text(cfg, "footer_teams"),
        " [L]               " + config.get_text(cfg, "footer_lakers"),
        " [G]               " + config.get_text(cfg, "footer_date"),
        " [,] [.]  [←] [→]  " + config.get_text(cfg, "help_nav_date"),
        " [D]                " + config.get_text(cfg, "footer_today"),
        " [R]                " + config.get_text(cfg, "footer_refresh"),
        " [F]                " + config.get_text(cfg, "help_filter"),
        " [C]                " + config.get_text(cfg, "footer_config"),
        " [?] [H]            " + config.get_text(cfg, "help_help"),
        " [Q]                " + config.get_text(cfg, "footer_quit"),
        "",
    ]

    try:
        stdscr.addstr(0, 0, title, curses.A_BOLD | curses.A_REVERSE)
        for i, line in enumerate(lines):
            if 2 + i < height - 2:
                stdscr.addstr(2 + i, 0, line[: width - 1])
        stdscr.addstr(height - 1, 0, f" {press_key} "[: width - 1], curses.A_DIM)
    except curses.error:
        pass
    stdscr.refresh()
    wait_key(stdscr)
