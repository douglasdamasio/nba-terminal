"""Dashboard: game list (in progress, not started, final), standings, and league leaders."""
import curses
from datetime import datetime, timezone
from dateutil import parser

import config
import constants
from core import categorize_games, format_live_clock, game_index_label
from .helpers import format_team_name

_format_live_clock = format_live_clock
_game_index_label = game_index_label


def _standings_row_attr(rank):
    if rank <= 6:
        return curses.A_BOLD | curses.color_pair(2)
    if rank <= 10:
        return curses.A_BOLD | curses.color_pair(3)
    return curses.A_DIM


def draw_game_row(stdscr, row, game, i, width, cfg, color_ctx, tz_info=None, layout_mode=None):
    away = game.get("awayTeam") or {}
    home = game.get("homeTeam") or {}
    away_tricode = away.get("teamTricode", "")
    home_tricode = home.get("teamTricode", "")
    away_name = format_team_name(away)
    home_name = format_team_name(home)
    away_score = away.get("score") or 0
    home_score = home.get("score") or 0
    is_live = away_score or home_score
    status = _format_live_clock(game) if is_live else game.get("gameStatusText", "")
    placar = f"{away_score} x {home_score}" if is_live else "vs"
    try:
        game_time_utc = game.get("gameTimeUTC")
        if game_time_utc:
            game_time = parser.parse(game_time_utc).replace(tzinfo=timezone.utc)
            game_time = game_time.astimezone(tz_info) if tz_info else game_time.astimezone(tz=None)
            time_str = game_time.strftime("%H:%M")
        else:
            time_str = "-"
    except Exception:
        time_str = "-"
    if layout_mode == "compact":
        compact = True
    elif layout_mode == "wide":
        compact = False
    else:
        compact = width < 90
    away_display = away_tricode if compact else away_name
    home_display = home_tricode if compact else home_name
    idx_label = _game_index_label(i)
    fav = config.favorite_team(cfg)
    is_lakers_game = fav in (away_tricode, home_tricode)
    try:
        x = 0
        stdscr.addstr(row, x, idx_label)
        x += len(idx_label)
        if is_lakers_game:
            stdscr.attron(curses.A_BOLD | curses.A_REVERSE)
        stdscr.attron(curses.color_pair(color_ctx.get_team_highlight_pair(away_tricode)))
        stdscr.addstr(row, x, away_display)
        stdscr.attroff(curses.color_pair(color_ctx.get_team_highlight_pair(away_tricode)))
        if is_lakers_game:
            stdscr.attroff(curses.A_BOLD | curses.A_REVERSE)
        x += len(away_display)
        stdscr.addstr(row, x, " @ ")
        x += 3
        if is_lakers_game:
            stdscr.attron(curses.A_BOLD | curses.A_REVERSE)
        stdscr.attron(curses.color_pair(color_ctx.get_team_highlight_pair(home_tricode)))
        stdscr.addstr(row, x, home_display)
        stdscr.attroff(curses.color_pair(color_ctx.get_team_highlight_pair(home_tricode)))
        if is_lakers_game:
            stdscr.attroff(curses.A_BOLD | curses.A_REVERSE)
        stdscr.addstr(row, x + len(home_display), f"  {placar}  [{status}]  {time_str}")
        if is_lakers_game:
            my_team_label = " " + config.get_text(cfg, "my_team_label") + " "
            stdscr.attron(curses.A_BOLD | curses.A_REVERSE)
            stdscr.addstr(row, x + len(home_display) + len(f"  {placar}  [{status}]  {time_str}"), my_team_label)
            stdscr.attroff(curses.A_BOLD | curses.A_REVERSE)
    except curses.error:
        try:
            stdscr.addstr(row, 0, f"{idx_label}{away_display} @ {home_display}  {placar}"[: width - 1])
        except curses.error:
            pass


def draw_splash(stdscr, message="Loading...", progress=0.0):
    height, width = stdscr.getmaxyx()
    stdscr.clear()
    try:
        title = " NBA Terminal App "
        stdscr.addstr(height // 2 - 2, max(0, (width - len(title)) // 2), title, curses.A_BOLD | curses.A_REVERSE)
        stdscr.addstr(height // 2, max(0, (width - len(message) - 4) // 2), f" {message} ", curses.A_DIM)
        stdscr.addstr(height // 2 + 1, max(0, (width - 20) // 2), constants.SPLASH_PLEASE_WAIT, curses.A_DIM)
        from .helpers import draw_loading_bar
        draw_loading_bar(stdscr, height // 2 + 3, width, progress)
        stdscr.refresh()
    except curses.error:
        pass


def _draw_dashboard_header(stdscr, width, game_date_str, live_str, em_andamento, err, cfg=None, refreshing_msg=None, favorite_notification=None):
    row = 0
    try:
        header_left = f" NBA Terminal App - {datetime.now().strftime('%H:%M:%S')} "
        date_info = f"| Data: {game_date_str} "
        stdscr.addstr(row, 0, header_left[: width - 1], curses.A_BOLD)
        pos = len(header_left)
        if pos + len(date_info) <= width - 1:
            stdscr.addstr(row, pos, date_info, curses.A_BOLD)
            pos += len(date_info)
        if refreshing_msg and pos + len(refreshing_msg) <= width - 1:
            stdscr.addstr(row, pos, refreshing_msg[: width - pos - 1], curses.A_BOLD | curses.color_pair(3))
            pos += len(refreshing_msg)
        elif live_str and pos + len(live_str) <= width - 1:
            attr = curses.A_BOLD | curses.color_pair(2) if em_andamento else curses.A_DIM
            stdscr.addstr(row, pos, live_str[: width - pos - 1], attr)
            pos += len(live_str)
        if favorite_notification and pos + len(favorite_notification) <= width - 1:
            stdscr.addstr(row, pos, (" " + favorite_notification)[: width - pos - 1], curses.A_BOLD | curses.color_pair(2))
        row += 1
        if err:
            retry_msg = config.get_text(cfg or {}, "error_retry").format(err=err)
            stdscr.addstr(row, 0, (" " + retry_msg + " ")[: width - 1], curses.A_BOLD | curses.color_pair(1))
            row += 1
    except curses.error:
        row = 2 if err else 1
    return max(row, 2)


def _draw_games_section(stdscr, row, games, game_idx, width, cfg, color_ctx, title, tz_info=None, layout_mode=None):
    try:
        stdscr.addstr(row, 0, title, curses.A_BOLD | curses.A_REVERSE)
    except curses.error:
        pass
    row += 1
    for game in games:
        draw_game_row(stdscr, row, game, game_idx, width, cfg, color_ctx, tz_info=tz_info, layout_mode=layout_mode)
        row += 1
        game_idx += 1
    return row + 1, game_idx


def _draw_league_leaders(stdscr, sep_row, width, height, league_leaders):
    table_start = sep_row + 2
    if not league_leaders or width < 75 or (sep_row + 8) >= height - 2:
        return table_start
    try:
        blk = sep_row + 1
        stdscr.addstr(blk, 0, " SEASON STATS - TOP 3 ", curses.A_BOLD | curses.A_REVERSE)
        blk += 1
        has_tdbl = bool(league_leaders.get("TDBL"))
        ncols = 4 if has_tdbl else 3
        cw = max(18, width // ncols)
        stdscr.addstr(blk, 0, " POINTS "[: cw - 1].ljust(cw), curses.A_BOLD)
        stdscr.addstr(blk, cw, " REBOUNDS "[: cw - 1].ljust(cw), curses.A_BOLD)
        stdscr.addstr(blk, cw * 2, " ASSISTS "[: cw - 1].ljust(cw), curses.A_BOLD)
        if has_tdbl:
            stdscr.addstr(blk, cw * 3, " TRIPLE-DBL "[: cw - 1].ljust(cw), curses.A_BOLD)
        blk += 1
        for i in range(3):
            pts_line = reb_line = ast_line = tdbl_line = ""
            if i < len(league_leaders.get("PTS", [])):
                nome, tm, val = league_leaders["PTS"][i]
                pts_line = f"{i+1}. {nome} ({val:.1f}) - {tm}"[: cw - 1]
            if i < len(league_leaders.get("REB", [])):
                nome, tm, val = league_leaders["REB"][i]
                reb_line = f"{i+1}. {nome} ({val:.1f}) - {tm}"[: cw - 1]
            if i < len(league_leaders.get("AST", [])):
                nome, tm, val = league_leaders["AST"][i]
                ast_line = f"{i+1}. {nome} ({val:.1f}) - {tm}"[: cw - 1]
            if has_tdbl and i < len(league_leaders.get("TDBL", [])):
                nome, tm, val = league_leaders["TDBL"][i]
                tdbl_line = f"{i+1}. {nome} ({int(val)}) - {tm}"[: cw - 1]
            try:
                stdscr.addstr(blk + i, 0, pts_line.ljust(cw))
                stdscr.addstr(blk + i, cw, reb_line.ljust(cw))
                stdscr.addstr(blk + i, cw * 2, ast_line.ljust(cw))
                if has_tdbl:
                    stdscr.addstr(blk + i, cw * 3, tdbl_line.ljust(cw))
            except curses.error:
                pass
        return sep_row + 2 + 5
    except curses.error:
        return table_start


def _draw_standings_wide(stdscr, table_start, height, east, west, col_width, color_ctx):
    try:
        stdscr.addstr(table_start, 0, " EAST (1-6 Playoff | 7-10 Play-in) ", curses.A_BOLD | curses.A_REVERSE)
        stdscr.addstr(table_start, col_width + 2, " WEST (1-6 Playoff | 7-10 Play-in) ", curses.A_BOLD | curses.A_REVERSE)
        stdscr.addstr(table_start + 1, 0, f"{'#':<2} {'Team':<22} {'W':<3} {'L':<3} {'PCT':<6}")
        stdscr.addstr(table_start + 1, col_width + 2, f"{'#':<2} {'Team':<22} {'W':<3} {'L':<3} {'PCT':<6}")
    except curses.error:
        pass
    if east is None or west is None:
        return
    for i in range(min(15, len(east), len(west))):
        r = table_start + 2 + i
        if r >= height - 2:
            break
        re = east.iloc[i] if i < len(east) else None
        rw = west.iloc[i] if i < len(west) else None
        try:
            if re is not None:
                rank = int(re["PlayoffRank"])
                team_e = f"{re['TeamCity']} {re['TeamName']}"
                tr_e = constants.get_tricode_from_team(team_e)
                stdscr.addstr(r, 0, f"{rank:<2} ")
                stdscr.attron(_standings_row_attr(rank))
                stdscr.attron(curses.color_pair(color_ctx.get_team_highlight_pair(tr_e)))
                stdscr.addstr(r, 4, f"{team_e[:22]:<22}")
                stdscr.attroff(curses.color_pair(color_ctx.get_team_highlight_pair(tr_e)))
                stdscr.attroff(_standings_row_attr(rank))
                stdscr.addstr(r, 26, f"{int(re['WINS']):<3} {int(re['LOSSES']):<3} {re['WinPCT']:.1%}")
        except (curses.error, (KeyError, IndexError)):
            pass
        try:
            if rw is not None:
                rank = int(rw["PlayoffRank"])
                team_w = f"{rw['TeamCity']} {rw['TeamName']}"
                tr_w = constants.get_tricode_from_team(team_w)
                stdscr.addstr(r, col_width + 2, f"{rank:<2} ")
                stdscr.attron(_standings_row_attr(rank))
                stdscr.attron(curses.color_pair(color_ctx.get_team_highlight_pair(tr_w)))
                stdscr.addstr(r, col_width + 6, f"{team_w[:22]:<22}")
                stdscr.attroff(curses.color_pair(color_ctx.get_team_highlight_pair(tr_w)))
                stdscr.attroff(_standings_row_attr(rank))
                stdscr.addstr(r, col_width + 28, f"{int(rw['WINS']):<3} {int(rw['LOSSES']):<3} {rw['WinPCT']:.1%}")
        except (curses.error, (KeyError, IndexError)):
            pass


STANDINGS_NARROW_ROWS = 36


def _draw_standings_narrow(stdscr, table_start, east, west, height, color_ctx, standings_scroll=0, footer_lines=1):
    """Draw standings in narrow/compact layout with optional scroll. Only draws visible rows."""
    visible = min(STANDINGS_NARROW_ROWS, max(0, height - table_start - footer_lines))
    if visible <= 0:
        return

    for L in range(standings_scroll, min(standings_scroll + visible, STANDINGS_NARROW_ROWS)):
        screen_row = table_start + (L - standings_scroll)
        if screen_row >= height - footer_lines - 1:
            break
        try:
            if L == 0:
                stdscr.addstr(screen_row, 0, " EAST (1-6 Playoff | 7-10 Play-in) ", curses.A_BOLD | curses.A_REVERSE)
            elif L == 1:
                stdscr.addstr(screen_row, 0, f"{'#':<2} {'Team':<28} {'W':<4} {'L':<4} {'PCT':<6}")
            elif 2 <= L <= 16 and east is not None and (L - 2) < len(east):
                line = east.iloc[L - 2]
                rank = int(line["PlayoffRank"])
                team = f"{line['TeamCity']} {line['TeamName']}"
                tr = constants.get_tricode_from_team(team)
                stdscr.addstr(screen_row, 0, f"{rank:<2} ")
                stdscr.attron(_standings_row_attr(rank))
                stdscr.attron(curses.color_pair(color_ctx.get_team_highlight_pair(tr)))
                stdscr.addstr(screen_row, 4, f"{team[:26]:<28}")
                stdscr.attroff(curses.color_pair(color_ctx.get_team_highlight_pair(tr)))
                stdscr.attroff(_standings_row_attr(rank))
                stdscr.addstr(screen_row, 34, f"{int(line['WINS']):<4} {int(line['LOSSES']):<4} {line['WinPCT']:.1%}")
            elif L == 17:
                stdscr.addstr(screen_row, 0, "")
            elif L == 18:
                stdscr.addstr(screen_row, 0, " WEST (1-6 Playoff | 7-10 Play-in) ", curses.A_BOLD | curses.A_REVERSE)
            elif L == 19:
                stdscr.addstr(screen_row, 0, f"{'#':<2} {'Team':<28} {'W':<4} {'L':<4} {'PCT':<6}")
            elif 20 <= L <= 35 and west is not None and (L - 20) < len(west):
                line = west.iloc[L - 20]
                rank = int(line["PlayoffRank"])
                team = f"{line['TeamCity']} {line['TeamName']}"
                tr = constants.get_tricode_from_team(team)
                stdscr.addstr(screen_row, 0, f"{rank:<2} ")
                stdscr.attron(_standings_row_attr(rank))
                stdscr.attron(curses.color_pair(color_ctx.get_team_highlight_pair(tr)))
                stdscr.addstr(screen_row, 4, f"{team[:26]:<28}")
                stdscr.attroff(curses.color_pair(color_ctx.get_team_highlight_pair(tr)))
                stdscr.attroff(_standings_row_attr(rank))
                stdscr.addstr(screen_row, 34, f"{int(line['WINS']):<4} {int(line['LOSSES']):<4} {line['WinPCT']:.1%}")
        except (curses.error, (KeyError, IndexError)):
            pass


def _draw_dashboard_footer(stdscr, height, width, cfg, filter_favorite_only=False, scroll_hint=False):
    filter_label = config.get_text(cfg, "footer_filter")
    if filter_favorite_only:
        filter_label = filter_label + " *"
    fav_tricode = config.favorite_team(cfg)
    fav_label = constants.TRICODE_TO_TEAM_NAME.get(fav_tricode, config.get_text(cfg, "footer_favorite"))
    line1 = f" [1-9,0,a-j] {config.get_text(cfg, 'footer_games')}  [T] {config.get_text(cfg, 'footer_teams')}  [L] {fav_label}  [G] {config.get_text(cfg, 'footer_date')}  [,][.]  [D] {config.get_text(cfg, 'footer_today')}  [R] {config.get_text(cfg, 'footer_refresh')} "
    line2 = f" [F] {filter_label}  [C] {config.get_text(cfg, 'footer_config')}  [?] {config.get_text(cfg, 'footer_help')}  [Q] {config.get_text(cfg, 'footer_quit')} "
    if scroll_hint:
        line2 += " [↑][↓] Scroll standings "
    try:
        if width >= 100:
            footer = line1 + line2
            stdscr.addstr(height - 1, 0, footer[: width - 1], curses.A_DIM)
        else:
            stdscr.addstr(height - 2, 0, line1[: width - 1], curses.A_DIM)
            stdscr.addstr(height - 1, 0, line2[: width - 1], curses.A_DIM)
    except curses.error:
        pass


def _favorite_notification(all_games, em_andamento, nao_comecaram, fav, cfg, tz_info):
    """Return short message if favorite team is playing now or starting soon, else None."""
    if not fav or not cfg:
        return None
    for g in em_andamento:
        if _game_has_team(g, fav):
            return config.get_text(cfg, "favorite_playing_now").strip()
    now = datetime.now(tz_info) if tz_info else datetime.now().astimezone()
    for g in nao_comecaram:
        if not _game_has_team(g, fav):
            continue
        try:
            gt = parser.parse(g.get("gameTimeUTC") or "").replace(tzinfo=timezone.utc)
            if tz_info:
                gt = gt.astimezone(tz_info)
            else:
                gt = gt.astimezone()
            delta_mins = (gt - now).total_seconds() / 60
            if 0 <= delta_mins <= 60:
                mins = int(delta_mins)
                return config.get_text(cfg, "favorite_starting_soon").format(mins=mins).strip()
        except Exception:
            pass
    return None


def draw_dashboard(stdscr, games, scoreboard_date, east, west, game_date_str, cfg, api_client, color_ctx, last_refresh=None, league_leaders=None, filter_favorite_only=False, game_sort=None, tz_info=None, standings_scroll=0, refresh_in_progress=False):
    height, width = stdscr.getmaxyx()
    stdscr.clear()

    em_andamento, nao_comecaram, finalizados = categorize_games(games)

    fav = config.favorite_team(cfg) if filter_favorite_only or (game_sort == "favorite_first") else None
    sort_key = _make_game_sort_key(cfg, game_sort, fav)
    if sort_key:
        em_andamento = sorted(em_andamento, key=sort_key)
        nao_comecaram = sorted(nao_comecaram, key=sort_key)
        finalizados = sorted(finalizados, key=sort_key)

    if filter_favorite_only and fav:
        em_andamento = [g for g in em_andamento if _game_has_team(g, fav)]
        nao_comecaram = [g for g in nao_comecaram if _game_has_team(g, fav)]
        finalizados = [g for g in finalizados if _game_has_team(g, fav)]

    all_games = em_andamento + nao_comecaram + finalizados

    if refresh_in_progress:
        live_str = " " + config.get_text(cfg or {}, "header_updating") + " "
    elif last_refresh is not None:
        refresh_dt = datetime.fromtimestamp(last_refresh, tz=timezone.utc)
        refresh_dt = refresh_dt.astimezone(tz_info) if tz_info else refresh_dt.astimezone(tz=None)
        live_str = f" \u2022 LIVE \u2022 Updated at {refresh_dt.strftime('%H:%M:%S')} " if em_andamento else f" \u2022 Last update: {refresh_dt.strftime('%H:%M')} "
    else:
        live_str = ""

    favorite_notification = _favorite_notification(all_games, em_andamento, nao_comecaram, fav, cfg, tz_info)
    refreshing_msg = (" " + config.get_text(cfg or {}, "header_updating") + " ") if refresh_in_progress else None
    err = api_client.get_last_error()
    row = _draw_dashboard_header(stdscr, width, game_date_str, live_str, em_andamento, err, cfg, refreshing_msg=refreshing_msg, favorite_notification=favorite_notification)
    game_idx = 0
    layout = config.layout_mode(cfg) if cfg else "auto"

    if em_andamento:
        row, game_idx = _draw_games_section(stdscr, row, em_andamento, game_idx, width, cfg, color_ctx, " GAMES IN PROGRESS ", tz_info=tz_info, layout_mode=layout)
    if nao_comecaram:
        row, game_idx = _draw_games_section(stdscr, row, nao_comecaram, game_idx, width, cfg, color_ctx, " GAMES NOT STARTED ", tz_info=tz_info, layout_mode=layout)
    if finalizados:
        row, game_idx = _draw_games_section(stdscr, row, finalizados, game_idx, width, cfg, color_ctx, " GAMES FINAL ", tz_info=tz_info, layout_mode=layout)

    sep_row = row
    try:
        stdscr.addstr(sep_row, 0, "-" * min(width - 1, 80))
    except curses.error:
        pass

    table_start = _draw_league_leaders(stdscr, sep_row, width, height, league_leaders)
    col_width = min(55, width // 2 - 2) if width >= 100 else min(50, width - 2)
    layout = config.layout_mode(cfg) if cfg else "auto"
    use_wide_standings = (layout == "wide") or (layout == "auto" and width >= 100)
    standings_scroll = standings_scroll or 0

    footer_lines = 2 if width < 100 else 1
    if use_wide_standings:
        _draw_standings_wide(stdscr, table_start, height, east, west, col_width, color_ctx)
        max_standings_scroll = 0
    else:
        visible_standings = max(0, height - table_start - footer_lines)
        max_standings_scroll = max(0, STANDINGS_NARROW_ROWS - visible_standings)
        standings_scroll = min(max(standings_scroll, 0), max_standings_scroll)
        _draw_standings_narrow(stdscr, table_start, east, west, height, color_ctx, standings_scroll=standings_scroll, footer_lines=footer_lines)

    _draw_dashboard_footer(stdscr, height, width, cfg, filter_favorite_only, scroll_hint=not use_wide_standings and max_standings_scroll > 0)
    stdscr.refresh()
    return all_games, max_standings_scroll if not use_wide_standings else 0


def _game_has_team(game, tricode):
    """True se o jogo envolve o time dado (tricode)."""
    away = game.get("awayTeam", {}).get("teamTricode", "")
    home = game.get("homeTeam", {}).get("teamTricode", "")
    return tricode.upper() in (away.upper(), home.upper())


def _make_game_sort_key(cfg, game_sort, fav):
    """Return a sort key function for games, or None for default order."""
    if not game_sort or game_sort == "time":
        def by_time(g):
            try:
                return parser.parse(g.get("gameTimeUTC", "") or "9999")
            except Exception:
                return parser.parse("9999")
        return by_time
    if game_sort == "favorite_first" and fav:
        def by_fav_then_time(g):
            has_fav = 0 if _game_has_team(g, fav) else 1
            try:
                t = parser.parse(g.get("gameTimeUTC", "") or "9999")
            except Exception:
                t = parser.parse("9999")
            return (has_fav, t)
        return by_fav_then_time
    return None
