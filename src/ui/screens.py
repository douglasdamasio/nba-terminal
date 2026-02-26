"""Configuration screens, date selection, and favorite team selection."""
import curses
from datetime import datetime

from dateutil import parser as dateutil_parser

import config
import constants


def parse_date_string(s: str):
    """Parse date string in various formats (YYYY-MM-DD, DD/MM/YYYY, etc.)."""
    if not s or not s.strip():
        return None
    try:
        return dateutil_parser.parse(s.strip()).date()
    except (ValueError, TypeError):
        return None


def _pick_favorite_team(stdscr, cfg):
    all_teams = [(t, constants.TRICODE_TO_TEAM_NAME.get(t, t)) for t in constants.TRICODE_TO_TEAM_ID]
    all_teams.sort(key=lambda x: x[1])
    height, width = stdscr.getmaxyx()
    visible = max(1, height - 4)
    selected = 0
    offset = 0
    while True:
        if selected < offset:
            offset = selected
        elif selected >= offset + visible:
            offset = selected - visible + 1
        stdscr.clear()
        try:
            stdscr.addstr(0, 0, " " + config.get_text(cfg, "favorite_team") + " ", curses.A_BOLD | curses.A_REVERSE)
            stdscr.addstr(1, 0, " ↑↓ select  Enter confirm  [Q] cancel "[: width - 1], curses.A_DIM)
        except curses.error:
            pass
        for i in range(visible):
            idx = offset + i
            if idx >= len(all_teams):
                break
            tr, name = all_teams[idx]
            line = f"  {tr}  {name}"[: width - 1]
            try:
                if idx == selected:
                    stdscr.addstr(3 + i, 0, line, curses.A_BOLD | curses.A_REVERSE)
                else:
                    stdscr.addstr(3 + i, 0, line)
            except curses.error:
                pass
        stdscr.refresh()
        stdscr.nodelay(False)
        key = stdscr.getch()
        if key == ord("q") or key == ord("Q"):
            return None
        if key == ord("\n") or key == ord("\r"):
            return all_teams[selected][0]
        if key == curses.KEY_UP:
            selected = max(0, selected - 1)
        elif key == curses.KEY_DOWN:
            selected = min(len(all_teams) - 1, selected + 1)


TIMEZONE_OPTIONS = ["localtime", "America/Sao_Paulo", "America/New_York", "Europe/London"]


def _cycle_timezone(cfg):
    current = cfg.get("timezone", "localtime")
    try:
        idx = TIMEZONE_OPTIONS.index(current)
    except ValueError:
        idx = 0
    cfg["timezone"] = TIMEZONE_OPTIONS[(idx + 1) % len(TIMEZONE_OPTIONS)]


def show_config_screen(stdscr, cfg):
    height, width = stdscr.getmaxyx()
    selected = 0
    while True:
        stdscr.clear()
        try:
            stdscr.addstr(0, 0, config.get_text(cfg, "config_title"), curses.A_BOLD | curses.A_REVERSE)
            stdscr.addstr(1, 0, " ↑↓ move  Enter change/select  [Q] back "[: width - 1], curses.A_DIM)
        except curses.error:
            pass
        lang_label = "EN" if cfg["language"] == "en" else "PT"
        ref_val = cfg.get("refresh_interval_seconds", 30)
        ref_display = str(ref_val) + "s" if ref_val else "off"
        mode_val = cfg.get("refresh_mode", "fixed")
        mode_label = config.get_text(cfg, "refresh_mode_auto") if mode_val == "auto" else config.get_text(cfg, "refresh_mode_fixed")
        fav = cfg["favorite_team"]
        fav_name = constants.TRICODE_TO_TEAM_NAME.get(fav, fav)
        sort_val = cfg.get("game_sort", "time")
        sort_label = config.get_text(cfg, "game_sort_favorite") if sort_val == "favorite_first" else config.get_text(cfg, "game_sort_time")
        tz_val = cfg.get("timezone", "localtime")
        tz_display = "Local" if tz_val == "localtime" else tz_val.split("/")[-1].replace("_", " ")
        theme_val = cfg.get("theme", "default")
        if theme_val == "high_contrast":
            theme_label = config.get_text(cfg, "theme_high_contrast")
        elif theme_val == "light":
            theme_label = config.get_text(cfg, "theme_light")
        else:
            theme_label = config.get_text(cfg, "theme_default")
        layout_val = cfg.get("layout_mode", "auto")
        if layout_val == "compact":
            layout_label = config.get_text(cfg, "layout_compact")
        elif layout_val == "wide":
            layout_label = config.get_text(cfg, "layout_wide")
        else:
            layout_label = config.get_text(cfg, "layout_auto")
        # Selectable indices: 0-7 = options, 12 = back (8-11 = separator and About subsection)
        selectable_rows = [0, 1, 2, 3, 4, 5, 6, 7, 12]
        lines = [
            config.get_text(cfg, "language") + ": " + lang_label,
            config.get_text(cfg, "refresh") + ": " + ref_display,
            config.get_text(cfg, "refresh_mode") + ": " + mode_label,
            config.get_text(cfg, "favorite_team") + ": " + fav + " - " + fav_name,
            config.get_text(cfg, "game_sort") + ": " + sort_label,
            config.get_text(cfg, "timezone") + ": " + tz_display,
            config.get_text(cfg, "theme") + ": " + theme_label,
            config.get_text(cfg, "layout_mode") + ": " + layout_label,
            "",
            config.get_text(cfg, "about_title"),
            config.get_text(cfg, "developer") + ": " + config.DEVELOPER_NAME + " - " + config.DEVELOPER_GITHUB,
            config.get_text(cfg, "version") + ": " + config.__version__,
            "[Q] " + config.get_text(cfg, "back"),
        ]
        for i, line in enumerate(lines):
            try:
                if i == 9:
                    attr = curses.A_BOLD | curses.A_REVERSE
                elif i in (10, 11):
                    attr = curses.A_DIM
                elif i == selectable_rows[selected]:
                    attr = curses.A_BOLD | curses.A_REVERSE
                else:
                    attr = 0
                stdscr.addstr(3 + i, 0, (line or " ")[: width - 1], attr)
            except curses.error:
                pass
        stdscr.refresh()
        stdscr.nodelay(False)
        key = stdscr.getch()
        if key == ord("q") or key == ord("Q"):
            config.save_config(cfg)
            return
        if key == curses.KEY_UP:
            selected = max(0, selected - 1)
        elif key == curses.KEY_DOWN:
            selected = min(len(selectable_rows) - 1, selected + 1)
        elif key == ord("\n") or key == ord("\r"):
            row = selectable_rows[selected]
            if row == 0:
                cfg["language"] = "pt" if cfg["language"] == "en" else "en"
            elif row == 1:
                choices = constants.REFRESH_INTERVAL_CHOICES
                try:
                    idx = choices.index(ref_val) if ref_val in choices else 0
                except (ValueError, TypeError):
                    idx = 0
                cfg["refresh_interval_seconds"] = choices[(idx + 1) % len(choices)]
            elif row == 2:
                cfg["refresh_mode"] = "auto" if cfg.get("refresh_mode", "fixed") == "fixed" else "fixed"
            elif row == 3:
                tr = _pick_favorite_team(stdscr, cfg)
                if tr is not None:
                    cfg["favorite_team"] = tr
            elif row == 4:
                cfg["game_sort"] = "favorite_first" if cfg.get("game_sort", "time") == "time" else "time"
            elif row == 5:
                _cycle_timezone(cfg)
            elif row == 6:
                themes = ["default", "high_contrast", "light"]
                try:
                    idx = themes.index(theme_val) if theme_val in themes else 0
                except (ValueError, TypeError):
                    idx = 0
                cfg["theme"] = themes[(idx + 1) % len(themes)]
            elif row == 7:
                layouts = ["auto", "compact", "wide"]
                try:
                    idx = layouts.index(layout_val) if layout_val in layouts else 0
                except (ValueError, TypeError):
                    idx = 0
                cfg["layout_mode"] = layouts[(idx + 1) % len(layouts)]
            elif row == 12:
                config.save_config(cfg)
                return


def prompt_date(stdscr, current_date):
    height, width = stdscr.getmaxyx()
    prompt = "Enter date (YYYY-MM-DD or DD/MM/YYYY): "
    input_str = current_date.strftime("%Y-%m-%d")
    cursor_pos = len(input_str)

    while True:
        stdscr.clear()
        try:
            stdscr.addstr(height // 2 - 1, 0, " GO TO DATE ", curses.A_BOLD | curses.A_REVERSE)
            stdscr.addstr(height // 2, 0, prompt)
            stdscr.addstr(height // 2, len(prompt), input_str)
            stdscr.addstr(height // 2 + 1, 0, " Enter confirm | Esc cancel ", curses.A_DIM)
            stdscr.move(height // 2, len(prompt) + cursor_pos)
        except curses.error:
            pass
        stdscr.refresh()
        stdscr.nodelay(False)
        key = stdscr.getch()

        if key == ord("\n") or key == ord("\r"):
            return parse_date_string(input_str)
        elif key == 27:
            return None
        elif key == curses.KEY_BACKSPACE or key == 127:
            if cursor_pos > 0:
                input_str = input_str[: cursor_pos - 1] + input_str[cursor_pos:]
                cursor_pos -= 1
        elif key == curses.KEY_LEFT:
            cursor_pos = max(0, cursor_pos - 1)
        elif key == curses.KEY_RIGHT:
            cursor_pos = min(len(input_str), cursor_pos + 1)
        elif 32 <= key < 127:
            input_str = input_str[:cursor_pos] + chr(key) + input_str[cursor_pos:]
            cursor_pos += 1
