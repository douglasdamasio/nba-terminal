"""Box score screen: score by quarter, team and player statistics."""
import curses

import config
import api
import constants
from . import teams
from . import player as player_ui
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


def _is_starter(p):
    return p.get("starter") in ("1", 1, True)


def _build_all_players(view_mode, away, home):
    """Build player list with starters first, then bench, per team. Separator "---" between teams; "starters"/"bench" labels."""
    teams_to_show = []
    if view_mode in ("both", "away"):
        teams_to_show.append((away, away.get("teamTricode", "")))
    if view_mode in ("both", "home"):
        teams_to_show.append((home, home.get("teamTricode", "")))
    out = []
    for team_idx, (team_data, tricode) in enumerate(teams_to_show):
        if view_mode == "both" and team_idx == 1:
            out.append(("---", None, None))
        players = team_data.get("players", [])
        starters = [p for p in players if _is_starter(p)]
        bench = [p for p in players if not _is_starter(p)]
        starters.sort(key=lambda p: p.get("statistics", {}).get("points", 0), reverse=True)
        bench.sort(key=lambda p: p.get("statistics", {}).get("points", 0), reverse=True)
        if starters:
            out.append(("STARTERS", None, tricode))
            for p in starters:
                out.append((p, team_data, tricode))
        if bench:
            out.append(("BENCH", None, tricode))
            for p in bench:
                out.append((p, team_data, tricode))
    return out


def _draw_head_to_head_line(stdscr, row, width, h2h, away_tricode, home_tricode, cfg):
    """Draw one line: Last meeting + Season series if available."""
    if not h2h or not h2h.get("last_meeting") and not h2h.get("season_series", {}).get("games"):
        return
    last = h2h.get("last_meeting") or {}
    ss = h2h.get("season_series") or {}
    parts = []
    if last.get("date"):
        pts_a, pts_b = last.get("pts_a"), last.get("pts_b")
        if pts_a is not None and pts_b is not None:
            parts.append(f"{config.get_text(cfg, 'last_meeting')}: {last['date']} {away_tricode} {pts_a}-{pts_b} {home_tricode}")
        else:
            parts.append(f"{config.get_text(cfg, 'last_meeting')}: {last['date']} {last.get('matchup', '')}")
    wins_a = ss.get("wins_a", 0)
    wins_b = ss.get("wins_b", 0)
    if wins_a is not None and wins_b is not None and (wins_a or wins_b):
        parts.append(f"  |  {config.get_text(cfg, 'season_series')}: {away_tricode} {wins_a}-{wins_b} {home_tricode}")
    line = "  ".join(parts)
    try:
        stdscr.addstr(row, 0, line[: width - 1], curses.A_DIM)
    except curses.error:
        pass


def _draw_box_header_row(stdscr, game_data, away, home, away_name, home_name, away_tricode, home_tricode, color_ctx, h2h=None, cfg=None):
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
    row += 1
    if h2h and cfg is not None and (h2h.get("last_meeting") or (h2h.get("season_series") or {}).get("games")):
        _draw_head_to_head_line(stdscr, row, stdscr.getmaxyx()[1], h2h, away_tricode, home_tricode, cfg)
        row += 1
    return row


def _draw_quarter_scores(stdscr, row, quarter_scores, cfg, away_tricode, home_tricode, color_ctx, width, start_col=0):
    if not quarter_scores:
        return row
    try:
        stdscr.addstr(row, start_col, (config.get_text(cfg, "score_by_quarter") + " ")[: width - 1], curses.A_BOLD | curses.A_REVERSE)
        row += 1
        hdr = " " * 6 + "  ".join(f"{h:>5}" for h in quarter_scores["headers"])
        stdscr.addstr(row, start_col, hdr[: width - 1])
        row += 1
        a_vals = "  ".join(f"{s:>5}" for s in quarter_scores["away"])
        stdscr.attron(curses.color_pair(color_ctx.get_team_highlight_pair(away_tricode)))
        stdscr.addstr(row, start_col, (f"  {away_tricode}  {a_vals}")[: width - 1])
        stdscr.attroff(curses.color_pair(color_ctx.get_team_highlight_pair(away_tricode)))
        row += 1
        h_vals = "  ".join(f"{s:>5}" for s in quarter_scores["home"])
        stdscr.attron(curses.color_pair(color_ctx.get_team_highlight_pair(home_tricode)))
        stdscr.addstr(row, start_col, (f"  {home_tricode}  {h_vals}")[: width - 1])
        stdscr.attroff(curses.color_pair(color_ctx.get_team_highlight_pair(home_tricode)))
        row += 2
    except curses.error:
        pass
    return row


# Triple-double indicator (ASCII so it works in all terminals)
TRIPLE_DOUBLE_MARK = "[TD]"

# Group box score stats for clearer layout (label, keys).
_STAT_GROUPS = [
    ("SCORING", ["points"]),
    ("SHOOTING", ["fieldGoalsMade", "fieldGoalsAttempted", "fieldGoalsPercentage", "threePointersMade", "threePointersAttempted", "threePointersPercentage", "freeThrowsMade", "freeThrowsAttempted", "freeThrowsPercentage"]),
    ("REBOUNDS", ["reboundsOffensive", "reboundsDefensive", "reboundsTotal"]),
    ("OTHER", ["assists", "steals", "blocks", "turnovers", "foulsPersonal", "plusMinusPoints"]),
]
_LOWER_BETTER_KEYS = {"turnovers", "foulsPersonal"}


def _fmt_stat_val(val):
    if val is None:
        return "-"
    if isinstance(val, float):
        return f"{val:.2%}" if 0 < val < 1 else f"{val:.2f}"
    return str(val)


def _draw_team_stats_table(stdscr, row, away, home, away_tricode, home_tricode, width, color_ctx, start_col=0):
    try:
        away_stats = away.get("statistics", {})
        home_stats = home.get("statistics", {})
        col_label = 14
        col_away = 10
        col_home = 10
        x_away = start_col + col_label
        x_home = start_col + col_label + col_away

        stdscr.addstr(row, start_col, (" TEAM STATISTICS ")[: width - 1], curses.A_BOLD | curses.A_REVERSE)
        row += 1
        stdscr.addstr(row, start_col, " " * col_label, curses.A_DIM)
        stdscr.attron(curses.color_pair(color_ctx.get_team_highlight_pair(away_tricode)))
        stdscr.addstr(row, x_away, f" {away_tricode:^{col_away - 2}} ", curses.A_BOLD)
        stdscr.attroff(curses.color_pair(color_ctx.get_team_highlight_pair(away_tricode)))
        stdscr.attron(curses.color_pair(color_ctx.get_team_highlight_pair(home_tricode)))
        stdscr.addstr(row, x_home, f" {home_tricode:^{col_home - 2}} ", curses.A_BOLD)
        stdscr.attroff(curses.color_pair(color_ctx.get_team_highlight_pair(home_tricode)))
        row += 1
        stdscr.addstr(row, start_col, " " + "-" * (col_label + col_away + col_home - 1), curses.A_DIM)
        row += 1

        for group_label, keys in _STAT_GROUPS:
            has_any = False
            group_rows = []
            for key in keys:
                a_val, h_val = away_stats.get(key), home_stats.get(key)
                if a_val is None and h_val is None:
                    continue
                has_any = True
                label = constants.STAT_NAMES.get(key, key)
                a_str = _fmt_stat_val(a_val)
                h_str = _fmt_stat_val(h_val)
                lower_better = key in _LOWER_BETTER_KEYS
                try:
                    an, hn = float(a_val) if a_val is not None else None, float(h_val) if h_val is not None else None
                except (TypeError, ValueError):
                    an, hn = None, None
                if an is not None and hn is not None and an != hn:
                    if lower_better:
                        better_a, better_h = an < hn, hn < an
                    else:
                        better_a, better_h = an > hn, hn > an
                else:
                    better_a = better_h = False
                group_rows.append((label, a_str, h_str, better_a, better_h))
            if not has_any:
                continue
            stdscr.addstr(row, start_col, f" {group_label} ", curses.A_BOLD | curses.A_DIM)
            row += 1
            for label, a_str, h_str, better_a, better_h in group_rows:
                try:
                    stdscr.addstr(row, start_col, f"  {label:<{col_label - 2}}")
                    if better_a:
                        stdscr.attron(curses.A_BOLD)
                    stdscr.attron(curses.color_pair(color_ctx.get_team_highlight_pair(away_tricode)))
                    stdscr.addstr(row, x_away, a_str.rjust(col_away))
                    stdscr.attroff(curses.color_pair(color_ctx.get_team_highlight_pair(away_tricode)))
                    if better_a:
                        stdscr.attroff(curses.A_BOLD)
                    if better_h:
                        stdscr.attron(curses.A_BOLD)
                    stdscr.attron(curses.color_pair(color_ctx.get_team_highlight_pair(home_tricode)))
                    stdscr.addstr(row, x_home, h_str.rjust(col_home))
                    stdscr.attroff(curses.color_pair(color_ctx.get_team_highlight_pair(home_tricode)))
                    if better_h:
                        stdscr.attroff(curses.A_BOLD)
                except curses.error:
                    pass
                row += 1
            stdscr.addstr(row, start_col, " " * min(col_label + col_away + col_home, width), curses.A_DIM)
            row += 1
    except (NameError, AttributeError):
        pass
    return row + 1


def _draw_players_list(stdscr, start_row, height, start_col, pane_width, view_mode, away_tricode, home_tricode, all_players, player_offset, selected_player_idx, color_ctx):
    if view_mode == "away":
        section = f" {away_tricode} "
    elif view_mode == "home":
        section = f" {home_tricode} "
    else:
        section = " ALL PLAYERS "
    section = (section + " ")[: pane_width - 1]
    try:
        stdscr.addstr(start_row, start_col, section, curses.A_BOLD | curses.A_REVERSE)
    except curses.error:
        pass
    start_row += 1
    hdr = f"{'#':<4} {'Player':<20} {'PTS':>4} {'REB':>4} {'AST':>4}"
    stdscr.addstr(start_row, start_col, hdr[: pane_width - 1])
    start_row += 1
    stdscr.addstr(start_row, start_col, "-" * min(pane_width, 50))
    start_row += 1
    list_start_row = start_row + 1
    pad_height = max(1, height - list_start_row - 2)
    visible = all_players[player_offset:player_offset + pad_height]
    for idx, (p, team_data, tricode) in enumerate(visible):
        r = list_start_row + idx
        if r >= height - 2:
            break
        if p == "---":
            try:
                stdscr.addstr(r, start_col, (" " + "-" * (pane_width - 2))[: pane_width - 1], curses.A_DIM)
            except curses.error:
                pass
            continue
        if p in ("STARTERS", "BENCH"):
            try:
                label = "  -- Starters -- " if p == "STARTERS" else "  -- Bench -- "
                stdscr.attron(curses.A_BOLD | curses.A_DIM)
                stdscr.addstr(r, start_col, label[: pane_width - 1])
                stdscr.attroff(curses.A_BOLD | curses.A_DIM)
            except curses.error:
                pass
            continue
        stats = p.get("statistics", {})
        pts = stats.get("points", 0)
        reb = stats.get("reboundsTotal", 0)
        ast = stats.get("assists", 0)
        fg = stats.get("fieldGoalsPercentage")
        fg_str = f"{fg:.1%}" if fg is not None else "-"
        jersey = str(p.get("jerseyNum", "-"))
        name = p.get("name", "-")
        if constants.is_triple_double(stats):
            name = f"{TRIPLE_DOUBLE_MARK} {name}"
        is_selected = (player_offset + idx == selected_player_idx) and all_players
        line = f"{jersey:<4} {name[:22]:<24} {pts:>4} {reb:>4} {ast:>4}"
        try:
            if is_selected:
                stdscr.attron(curses.A_REVERSE)
            stdscr.attron(curses.color_pair(color_ctx.get_team_highlight_pair(tricode)))
            stdscr.addstr(r, start_col, line[: pane_width - 1])
            stdscr.attroff(curses.color_pair(color_ctx.get_team_highlight_pair(tricode)))
            if is_selected:
                stdscr.attroff(curses.A_REVERSE)
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


def show_player_compare(stdscr, player_id_a, name_a, tricode_a, player_id_b, name_b, tricode_b, cfg, color_ctx, api_client):
    """Show side-by-side comparison: season stats and recent games for two players."""
    height, width = stdscr.getmaxyx()
    stdscr.clear()
    try:
        info_a = api_client.fetch_player_info(int(player_id_a)) if player_id_a else None
        info_b = api_client.fetch_player_info(int(player_id_b)) if player_id_b else None
        log_a = api_client.fetch_player_game_log(int(player_id_a), limit=5) if player_id_a else []
        log_b = api_client.fetch_player_game_log(int(player_id_b), limit=5) if player_id_b else []
    except (TypeError, ValueError):
        info_a = info_b = None
        log_a = log_b = []

    col_w = max(20, (width - 4) // 2)
    safe_addstr(stdscr, 0, 0, " COMPARE PLAYERS ", curses.A_BOLD | curses.A_REVERSE, max_width=width)
    stdscr.attron(curses.color_pair(color_ctx.get_team_highlight_pair(tricode_a or "")))
    safe_addstr(stdscr, 1, 1, f" {name_a[: col_w - 2]} ", max_width=col_w)
    stdscr.attroff(curses.color_pair(color_ctx.get_team_highlight_pair(tricode_a or "")))
    stdscr.attron(curses.color_pair(color_ctx.get_team_highlight_pair(tricode_b or "")))
    safe_addstr(stdscr, 1, col_w + 2, f" {name_b[: col_w - 2]} ", max_width=col_w)
    stdscr.attroff(curses.color_pair(color_ctx.get_team_highlight_pair(tricode_b or "")))

    row = 3
    safe_addstr(stdscr, row, 0, config.get_text(cfg, "player_season_stats"), curses.A_BOLD | curses.A_REVERSE, max_width=width)
    row += 1
    pts_a = info_a.get("PTS", info_a.get("pts", "-")) if info_a else "-"
    reb_a = info_a.get("REB", info_a.get("rebounds", "-")) if info_a else "-"
    ast_a = info_a.get("AST", info_a.get("assists", "-")) if info_a else "-"
    pts_b = info_b.get("PTS", info_b.get("pts", "-")) if info_b else "-"
    reb_b = info_b.get("REB", info_b.get("rebounds", "-")) if info_b else "-"
    ast_b = info_b.get("AST", info_b.get("assists", "-")) if info_b else "-"
    safe_addstr(stdscr, row, 1, f"PTS: {pts_a}  REB: {reb_a}  AST: {ast_a}", max_width=col_w)
    safe_addstr(stdscr, row, col_w + 2, f"PTS: {pts_b}  REB: {reb_b}  AST: {ast_b}", max_width=col_w)
    row += 2

    safe_addstr(stdscr, row, 0, config.get_text(cfg, "player_recent_games"), curses.A_BOLD | curses.A_REVERSE, max_width=width)
    row += 1
    for i in range(max(len(log_a), len(log_b))):
        if row >= height - 2:
            break
        line_a = ""
        if i < len(log_a):
            g = log_a[i]
            line_a = f"  {g.get('GAME_DATE','')} {g.get('MATCHUP','')} {g.get('PTS','')} pts"
        line_b = ""
        if i < len(log_b):
            g = log_b[i]
            line_b = f"  {g.get('GAME_DATE','')} {g.get('MATCHUP','')} {g.get('PTS','')} pts"
        safe_addstr(stdscr, row, 1, line_a[: col_w - 1], max_width=col_w)
        safe_addstr(stdscr, row, col_w + 2, line_b[: col_w - 1], max_width=col_w)
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
    away_team_id = away.get("teamId") or constants.TRICODE_TO_TEAM_ID.get(away_tricode.upper())
    home_team_id = home.get("teamId") or constants.TRICODE_TO_TEAM_ID.get(home_tricode.upper())
    h2h = {}
    if away_team_id and home_team_id:
        try:
            h2h = api_client.fetch_head_to_head(int(away_team_id), int(home_team_id))
        except (TypeError, ValueError):
            pass

    view_mode = "both"
    player_offset = 0
    selected_player_idx = 0
    compare_first = None  # None or (person_id, name, tricode)

    # Horizontal split: left = game stats (quarters + team stats), right = all players
    left_width = min(48, max(34, (width - 2) // 2))
    right_col = left_width + 2
    right_width = width - right_col - 1
    content_start_row = 2

    while True:
        stdscr.clear()
        try:
            header_end_row = _draw_box_header_row(stdscr, game_data, away, home, away_name, home_name, away_tricode, home_tricode, color_ctx, h2h=h2h, cfg=cfg)
            content_start_row = header_end_row

            # Left pane: quarter scores + team statistics
            row = _draw_quarter_scores(stdscr, content_start_row, quarter_scores, cfg, away_tricode, home_tricode, color_ctx, left_width, start_col=0)
            row = _draw_team_stats_table(stdscr, row, away, home, away_tricode, home_tricode, left_width, color_ctx, start_col=0)

            # Vertical separator
            for r in range(content_start_row, height - 1):
                try:
                    stdscr.addstr(r, left_width + 1, "|", curses.A_DIM)
                except curses.error:
                    pass

            # Right pane: all players list
            all_players = _build_all_players(view_mode, away, home)
            list_start_row = content_start_row + 4
            pad_height = max(1, height - list_start_row - 2)
            if not all_players:
                selected_player_idx = -1
            elif selected_player_idx >= len(all_players):
                selected_player_idx = len(all_players) - 1
            # Ensure selection is on a player, not a separator or section label
            while 0 <= selected_player_idx < len(all_players) and all_players[selected_player_idx][0] in ("---", "STARTERS", "BENCH"):
                selected_player_idx += 1
            if selected_player_idx >= len(all_players):
                selected_player_idx = len(all_players) - 1
                while selected_player_idx >= 0 and all_players[selected_player_idx][0] in ("---", "STARTERS", "BENCH"):
                    selected_player_idx -= 1
            if selected_player_idx >= 0 and player_offset > selected_player_idx:
                player_offset = selected_player_idx
            if selected_player_idx >= player_offset + pad_height:
                player_offset = selected_player_idx - pad_height + 1

            _draw_players_list(stdscr, content_start_row, height, right_col, right_width, view_mode, away_tricode, home_tricode, all_players, player_offset, selected_player_idx, color_ctx)
            hint = " [A][H][B] Teams  [1][2] Team  [↑][↓] [Enter] Stats  [Q] Back "
            if all_players and 0 <= selected_player_idx < len(all_players) and all_players[selected_player_idx][0] not in ("---", "STARTERS", "BENCH"):
                hint += config.get_text(cfg, "boxscore_hint_player")
            hint += " " + config.get_text(cfg, "boxscore_hint_compare")
            try:
                stdscr.addstr(height - 1, 0, hint[: width - 1], curses.A_DIM)
            except curses.error:
                pass
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
            while selected_player_idx > 0 and all_players[selected_player_idx][0] in ("---", "STARTERS", "BENCH"):
                selected_player_idx -= 1
            if player_offset > selected_player_idx:
                player_offset = selected_player_idx
        elif key == curses.KEY_DOWN and all_players:
            selected_player_idx = min(len(all_players) - 1, selected_player_idx + 1)
            while selected_player_idx < len(all_players) - 1 and all_players[selected_player_idx][0] in ("---", "STARTERS", "BENCH"):
                selected_player_idx += 1
            if selected_player_idx >= player_offset + pad_height - 1:
                player_offset = selected_player_idx - pad_height + 1
        elif key in (ord("\n"), ord("\r")):
            if all_players and 0 <= selected_player_idx < len(all_players):
                p, team_data, tricode = all_players[selected_player_idx]
                if p not in ("---", "STARTERS", "BENCH"):
                    show_player_stats(stdscr, p, team_data, tricode, color_ctx)
        elif key in (ord("p"), ord("P")):
            if all_players and 0 <= selected_player_idx < len(all_players):
                p, team_data, tricode = all_players[selected_player_idx]
                if p not in ("---", "STARTERS", "BENCH"):
                    person_id = p.get("personId") or p.get("playerId")
                    if person_id is not None:
                        player_ui.show_player_page(stdscr, person_id, p.get("name", "-"), tricode, cfg, color_ctx, api_client)
                    else:
                        show_player_stats(stdscr, p, team_data, tricode, color_ctx)
        elif key == ord("1"):
            tid = away.get("teamId") or constants.TRICODE_TO_TEAM_ID.get(away_tricode.upper())
            teams.show_team_page(stdscr, away_tricode, away_name, cfg, color_ctx, api_client, tid)
        elif key == ord("2"):
            tid = home.get("teamId") or constants.TRICODE_TO_TEAM_ID.get(home_tricode.upper())
            teams.show_team_page(stdscr, home_tricode, home_name, cfg, color_ctx, api_client, tid)
        elif key in (ord("c"), ord("C")):
            if not all_players or selected_player_idx < 0 or selected_player_idx >= len(all_players):
                continue
            p, team_data, tricode = all_players[selected_player_idx]
            if p in ("---", "STARTERS", "BENCH"):
                continue
            person_id = p.get("personId") or p.get("playerId")
            name = p.get("name", "-")
            if person_id is None:
                continue
            if compare_first is None:
                compare_first = (person_id, name, tricode)
            else:
                other_id, other_name, other_tricode = compare_first
                if other_id != person_id:
                    show_player_compare(stdscr, other_id, other_name, other_tricode, person_id, name, tricode, cfg, color_ctx, api_client)
                compare_first = None
