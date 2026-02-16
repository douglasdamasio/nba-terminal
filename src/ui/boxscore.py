"""Tela de box score: placar por quarto, estatísticas de time e jogadores."""
import curses

import config
import api
import constants
from . import teams
from .helpers import safe_addstr, wait_key, format_team_name


def show_stats_unavailable(stdscr):
    height, width = stdscr.getmaxyx()
    stdscr.clear()
    msg = " Stats for this game are not available yet. "
    msg2 = " The game may not have started or data is not yet available. "
    safe_addstr(stdscr, height // 2 - 1, max(0, (width - len(msg)) // 2), msg, curses.A_BOLD | curses.A_REVERSE)
    safe_addstr(stdscr, height // 2, max(0, (width - len(msg2)) // 2), msg2, curses.A_DIM)
    safe_addstr(stdscr, height - 1, 0, " Press any key to go back ", curses.A_DIM, max_width=width)
    stdscr.refresh()
    wait_key(stdscr)


def _format_stat_value(val):
    if isinstance(val, float):
        return f"{val:.2%}" if 0 < val < 1 else f"{val:.2f}"
    return str(val)


def _build_all_players(view_mode, away, home):
    teams_to_show = []
    if view_mode in ("both", "away"):
        teams_to_show.append((away, away.get("teamTricode", "")))
    if view_mode in ("both", "home"):
        teams_to_show.append((home, home.get("teamTricode", "")))
    out = []
    for team_idx, (team_data, tricode) in enumerate(teams_to_show):
        if view_mode == "both" and team_idx == 1:
            out.append(("---", None, None))
        players = sorted(
            team_data.get("players", []),
            key=lambda p: p.get("statistics", {}).get("points", 0),
            reverse=True,
        )
        for p in players:
            out.append((p, team_data, tricode))
    return out


def _draw_box_header_row(stdscr, game_data, away, home, away_name, home_name, away_tricode, home_tricode, color_ctx):
    stdscr.addstr(0, 0, f" BOX SCORE - {game_data.get('gameStatusText', '')} ", curses.A_BOLD | curses.A_REVERSE)
    row, x = 1, 0
    stdscr.attron(curses.color_pair(color_ctx.get_team_highlight_pair(away_tricode)))
    stdscr.addstr(row, x, f" {away_name} ")
    stdscr.attroff(curses.color_pair(color_ctx.get_team_highlight_pair(away_tricode)))
    x += len(away_name) + 2
    stdscr.attron(curses.A_BOLD | curses.A_REVERSE)
    stdscr.addstr(row, x, f" {away.get('score', 0)} x {home.get('score', 0)} ")
    stdscr.attroff(curses.A_BOLD | curses.A_REVERSE)
    x += len(f" {away.get('score', 0)} x {home.get('score', 0)} ") + 1
    stdscr.attron(curses.color_pair(color_ctx.get_team_highlight_pair(home_tricode)))
    stdscr.addstr(row, x, f" {home_name} ")
    stdscr.attroff(curses.color_pair(color_ctx.get_team_highlight_pair(home_tricode)))


def _draw_quarter_scores(stdscr, row, quarter_scores, cfg, away_tricode, home_tricode, color_ctx, width):
    if not quarter_scores:
        return row
    try:
        stdscr.addstr(row, 0, config.get_text(cfg, "score_by_quarter"), curses.A_BOLD | curses.A_REVERSE)
        row += 1
        hdr = " " * 6 + "  ".join(f"{h:>5}" for h in quarter_scores["headers"])
        stdscr.addstr(row, 0, hdr[: width - 1])
        row += 1
        a_vals = "  ".join(f"{s:>5}" for s in quarter_scores["away"])
        stdscr.attron(curses.color_pair(color_ctx.get_team_highlight_pair(away_tricode)))
        stdscr.addstr(row, 0, f"  {away_tricode}  {a_vals}"[: width - 1])
        stdscr.attroff(curses.color_pair(color_ctx.get_team_highlight_pair(away_tricode)))
        row += 1
        h_vals = "  ".join(f"{s:>5}" for s in quarter_scores["home"])
        stdscr.attron(curses.color_pair(color_ctx.get_team_highlight_pair(home_tricode)))
        stdscr.addstr(row, 0, f"  {home_tricode}  {h_vals}"[: width - 1])
        stdscr.attroff(curses.color_pair(color_ctx.get_team_highlight_pair(home_tricode)))
        row += 2
    except curses.error:
        pass
    return row


def _draw_team_stats_table(stdscr, row, away, home, away_tricode, home_tricode, width):
    stdscr.addstr(row, 0, " TEAM STATS ", curses.A_BOLD | curses.A_REVERSE)
    row += 1
    stdscr.addstr(row, 0, f"{'Stat':<12} {away_tricode:>8} {home_tricode:>8}")
    row += 1
    stdscr.addstr(row, 0, "-" * min(35, width))
    row += 1
    away_stats = away.get("statistics", {})
    home_stats = home.get("statistics", {})
    for key in constants.BOX_SCORE_STAT_KEYS:
        a_val, h_val = away_stats.get(key), home_stats.get(key)
        if a_val is None and h_val is None:
            continue
        label = constants.STAT_NAMES.get(key, key)
        if isinstance(a_val, float):
            a_val = f"{a_val:.2%}" if 0 < a_val < 1 else f"{a_val:.2f}"
        if isinstance(h_val, float):
            h_val = f"{h_val:.2%}" if 0 < h_val < 1 else f"{h_val:.2f}"
        a_str = str(a_val) if a_val is not None else "-"
        h_str = str(h_val) if h_val is not None else "-"
        stdscr.addstr(row, 0, f"{label:<12} {a_str:>8} {h_str:>8}")
        row += 1
    return row + 1


def _draw_players_list(stdscr, row, height, width, view_mode, away_tricode, home_tricode, all_players, player_offset, selected_player_idx, color_ctx):
    if view_mode == "away":
        section = f" {away_tricode} - TODOS OS JOGADORES "
    elif view_mode == "home":
        section = f" {home_tricode} - TODOS OS JOGADORES "
    else:
        section = " ALL PLAYERS (Both teams) "
    stdscr.addstr(row, 0, section, curses.A_BOLD | curses.A_REVERSE)
    row += 1
    stdscr.addstr(row, 0, f"{'#':<5} {'Player':<24} {'PTS':>5} {'REB':>5} {'AST':>5} {'FG%':>6} {'3PM':>4}")
    row += 1
    stdscr.addstr(row, 0, "-" * min(65, width))
    row += 1
    stdscr.addstr(row, 0, " (ST) = Starter  |  \U0001f3c0 = Triple-double")
    row += 1
    pad_height = max(1, height - row - 2)
    visible = all_players[player_offset:player_offset + pad_height]
    for idx, (p, team_data, tricode) in enumerate(visible):
        r = row + idx
        if r >= height - 2:
            break
        if p == "---":
            try:
                stdscr.addstr(r, 0, " " + "-" * min(60, width - 2) + " ", curses.A_DIM)
            except curses.error:
                pass
            continue
        stats = p.get("statistics", {})
        pts = stats.get("points", 0)
        reb = stats.get("reboundsTotal", 0)
        ast = stats.get("assists", 0)
        fg = stats.get("fieldGoalsPercentage")
        fg_str = f"{fg:.2%}" if fg is not None else "-"
        tpm = stats.get("threePointersMade", 0)
        jersey = str(p.get("jerseyNum", "-"))
        name = p.get("name", "-")
        if p.get("starter") in ("1", 1, True):
            name = f"{name} (ST)"
        if constants.is_triple_double(stats):
            name = f"\U0001f3c0 {name}"
        is_selected = (player_offset + idx == selected_player_idx) and all_players
        try:
            stdscr.addstr(r, 0, f"{jersey:<5}")
            if is_selected:
                stdscr.attron(curses.A_REVERSE)
            stdscr.attron(curses.color_pair(color_ctx.get_team_highlight_pair(tricode)))
            stdscr.addstr(r, 5, f"{name[:23]:<24}")
            stdscr.attroff(curses.color_pair(color_ctx.get_team_highlight_pair(tricode)))
            if is_selected:
                stdscr.attroff(curses.A_REVERSE)
            stdscr.addstr(r, 29, f"{pts:>5} {reb:>5} {ast:>5} {fg_str:>6} {tpm:>4}")
        except curses.error:
            pass


def show_player_stats(stdscr, player, team_data, tricode, color_ctx):
    height, width = stdscr.getmaxyx()
    stdscr.clear()
    stats = player.get("statistics", {})
    jersey = str(player.get("jerseyNum", "-"))
    name = player.get("name", "-")
    team_name = format_team_name(team_data)

    safe_addstr(stdscr, 0, 0, f" STATS - #{jersey} {name} ", curses.A_BOLD | curses.A_REVERSE, max_width=width)
    stdscr.attron(curses.color_pair(color_ctx.get_team_highlight_pair(tricode)))
    safe_addstr(stdscr, 1, 0, f" {team_name} ", max_width=width)
    stdscr.attroff(curses.color_pair(color_ctx.get_team_highlight_pair(tricode)))

    row = 3
    safe_addstr(stdscr, row, 0, " GAME STATS ", curses.A_BOLD | curses.A_REVERSE, max_width=width)
    row += 2
    for key in constants.STAT_NAMES:
        val = stats.get(key)
        if val is None:
            continue
        label = constants.STAT_NAMES[key]
        safe_addstr(stdscr, row, 0, f"{label:<20} {_format_stat_value(val)}", max_width=width)
        row += 1

    safe_addstr(stdscr, height - 1, 0, " Press any key to go back ", curses.A_DIM, max_width=width)
    stdscr.refresh()
    wait_key(stdscr)


def show_game_stats(stdscr, game, cfg, color_ctx, api_client):
    game_id = game.get("gameId")
    if not game_id:
        show_stats_unavailable(stdscr)
        return

    game_data = api_client.get_box_score(game_id)
    if game_data is None:
        show_stats_unavailable(stdscr)
        return

    away = game_data.get("awayTeam", {})
    home = game_data.get("homeTeam", {})
    if not away.get("players") and not home.get("players"):
        show_stats_unavailable(stdscr)
        return

    quarter_scores = api.build_quarter_scores(away, home)

    height, width = stdscr.getmaxyx()
    away_name = format_team_name(away)
    home_name = format_team_name(home)
    away_tricode = away.get("teamTricode", "")
    home_tricode = home.get("teamTricode", "")

    view_mode = "both"
    player_offset = 0
    selected_player_idx = 0

    while True:
        stdscr.clear()
        try:
            _draw_box_header_row(stdscr, game_data, away, home, away_name, home_name, away_tricode, home_tricode, color_ctx)
            row = _draw_quarter_scores(stdscr, 3, quarter_scores, cfg, away_tricode, home_tricode, color_ctx, width)
            row = _draw_team_stats_table(stdscr, row, away, home, away_tricode, home_tricode, width)

            all_players = _build_all_players(view_mode, away, home)
            pad_height = max(1, height - row - 2)
            if not all_players:
                selected_player_idx = -1
            elif selected_player_idx >= len(all_players):
                selected_player_idx = len(all_players) - 1
            if selected_player_idx >= 0 and player_offset > selected_player_idx:
                player_offset = selected_player_idx
            if selected_player_idx >= player_offset + pad_height:
                player_offset = selected_player_idx - pad_height + 1

            _draw_players_list(stdscr, row, height, width, view_mode, away_tricode, home_tricode, all_players, player_offset, selected_player_idx, color_ctx)
            hint = " [A] Away  [H] Home  [B] Both  [1] Away page  [2] Home page  [↑][↓] [Enter] Player  [Q] Back "
            stdscr.addstr(height - 1, 0, hint[: width - 1], curses.A_DIM)
        except curses.error:
            pass

        stdscr.refresh()
        stdscr.nodelay(False)
        key = stdscr.getch()
        stdscr.nodelay(True)

        if key == ord("q") or key == ord("Q"):
            break
        if key == ord("a") or key == ord("A"):
            view_mode, player_offset, selected_player_idx = "away", 0, 0
        elif key == ord("h") or key == ord("H"):
            view_mode, player_offset, selected_player_idx = "home", 0, 0
        elif key == ord("b") or key == ord("B"):
            view_mode, player_offset, selected_player_idx = "both", 0, 0
        elif key == curses.KEY_UP and all_players:
            selected_player_idx = max(0, selected_player_idx - 1)
            while selected_player_idx > 0 and all_players[selected_player_idx][0] == "---":
                selected_player_idx -= 1
            if player_offset > selected_player_idx:
                player_offset = selected_player_idx
        elif key == curses.KEY_DOWN and all_players:
            selected_player_idx = min(len(all_players) - 1, selected_player_idx + 1)
            while selected_player_idx < len(all_players) - 1 and all_players[selected_player_idx][0] == "---":
                selected_player_idx += 1
            if selected_player_idx >= player_offset + pad_height - 1:
                player_offset = selected_player_idx - pad_height + 1
        elif key in (ord("\n"), ord("\r")):
            if all_players and 0 <= selected_player_idx < len(all_players):
                p, team_data, tricode = all_players[selected_player_idx]
                if p != "---":
                    show_player_stats(stdscr, p, team_data, tricode, color_ctx)
        elif key == ord("1"):
            tid = away.get("teamId") or constants.TRICODE_TO_TEAM_ID.get(away_tricode.upper())
            teams.show_team_page(stdscr, away_tricode, away_name, cfg, color_ctx, api_client, tid)
        elif key == ord("2"):
            tid = home.get("teamId") or constants.TRICODE_TO_TEAM_ID.get(home_tricode.upper())
            teams.show_team_page(stdscr, home_tricode, home_name, cfg, color_ctx, api_client, tid)
