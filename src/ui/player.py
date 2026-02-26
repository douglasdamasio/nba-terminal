"""Player page: season stats, recent games, and profile (opened from box score or team roster)."""
import curses
import re
from datetime import timezone
from dateutil import parser

import config
from .helpers import safe_addstr, wait_key
from . import colors


def _height_ft_in_to_meters(height_str):
    """Convert NBA API height string (e.g. '6-8' or '6-8.5') to meters. Returns None if invalid."""
    if not height_str or not isinstance(height_str, str):
        return None
    match = re.match(r"^(\d+)-(\d+(?:\.\d+)?)$", height_str.strip())
    if not match:
        return None
    try:
        feet = int(match.group(1))
        inches = float(match.group(2))
        total_inches = feet * 12 + inches
        return round(total_inches * 0.0254, 2)
    except (ValueError, TypeError):
        return None


def _weight_lbs_to_kg(weight_val):
    """Convert weight in pounds to kg. weight_val can be int, float or numeric string. Returns None if invalid."""
    if weight_val is None:
        return None
    try:
        lbs = float(weight_val)
        return round(lbs / 2.205, 1)
    except (ValueError, TypeError):
        return None


def show_player_page(stdscr, player_id, player_name, tricode, cfg, color_ctx, api_client):
    """Show full player page: profile, season stats, recent games. player_id is int or str (personId)."""
    try:
        pid = int(player_id)
    except (TypeError, ValueError):
        pid = None
    if not pid:
        return

    height, width = stdscr.getmaxyx()
    stdscr.clear()
    safe_addstr(stdscr, 0, 0, config.get_text(cfg, "player_page") + f" {player_name} ", curses.A_BOLD | curses.A_REVERSE, max_width=width)
    stdscr.attron(curses.color_pair(color_ctx.get_team_highlight_pair(tricode or "")))
    safe_addstr(stdscr, 1, 0, f" {tricode or '-'} ", max_width=width)
    stdscr.attroff(curses.color_pair(color_ctx.get_team_highlight_pair(tricode or "")))

    info = api_client.fetch_player_info(pid)
    game_log = api_client.fetch_player_game_log(pid, limit=10)

    row = 3
    if info:
        disp_name = info.get("DISPLAY_FIRST_LAST") or info.get("FIRST_NAME", "") + " " + info.get("LAST_NAME", "") or player_name
        safe_addstr(stdscr, row, 0, f"  {disp_name}", curses.A_BOLD, max_width=width)
        row += 1
        height_m = _height_ft_in_to_meters(info.get("HEIGHT"))
        if height_m is not None:
            safe_addstr(stdscr, row, 0, f"  {config.get_text(cfg, 'player_height')}: {height_m} m", max_width=width)
            row += 1
        weight_kg = _weight_lbs_to_kg(info.get("WEIGHT"))
        if weight_kg is not None:
            safe_addstr(stdscr, row, 0, f"  {config.get_text(cfg, 'player_weight')}: {weight_kg} kg", max_width=width)
            row += 1
        for key, label_key in (("SCHOOL", "player_school"), ("COUNTRY", "player_country"), ("BIRTHDATE", "player_birthdate")):
            val = info.get(key)
            if val is not None and str(val).strip():
                label = config.get_text(cfg, label_key)
                safe_addstr(stdscr, row, 0, f"  {label}: {val}", max_width=width)
        row += 1
    row += 1

    safe_addstr(stdscr, row, 0, config.get_text(cfg, "player_season_stats"), curses.A_BOLD | curses.A_REVERSE, max_width=width)
    row += 1
    if info and any(info.get(k) is not None for k in ("PTS", "REB", "AST")):
        pts = info.get("PTS", info.get("pts", "-"))
        reb = info.get("REB", info.get("rebounds", "-"))
        ast = info.get("AST", info.get("assists", "-"))
        safe_addstr(stdscr, row, 0, f"  PTS: {pts}  REB: {reb}  AST: {ast}", max_width=width)
        row += 1
    else:
        safe_addstr(stdscr, row, 0, "  (Season averages from profile)", curses.A_DIM, max_width=width)
        row += 1
    row += 1

    safe_addstr(stdscr, row, 0, config.get_text(cfg, "player_recent_games"), curses.A_BOLD | curses.A_REVERSE, max_width=width)
    row += 1
    if not game_log:
        safe_addstr(stdscr, row, 0, "  No recent games", curses.A_DIM, max_width=width)
        row += 1
    else:
        for g in game_log[:8]:
            if row >= height - 3:
                break
            date_str = g.get("GAME_DATE", "")
            matchup = g.get("MATCHUP", "-")
            wl = g.get("WL", "")
            pts = g.get("PTS", "")
            line = f"  {date_str}  {matchup}  {wl}  {pts} pts"
            safe_addstr(stdscr, row, 0, line[: width - 1], max_width=width)
            row += 1
    row += 1

    safe_addstr(stdscr, height - 1, 0, " Press any key to go back ", curses.A_DIM, max_width=width)
    stdscr.refresh()
    wait_key(stdscr)
