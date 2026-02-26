"""Team selection and team page: roster, leaders, upcoming/last games."""
import curses
from collections import namedtuple
from concurrent.futures import ThreadPoolExecutor
from datetime import timezone
from dateutil import parser

import config
import constants
from .helpers import safe_addstr, wait_key, format_team_name
from . import player as player_ui
from nba_api.stats.library.parameters import StatCategoryAbbreviation

TeamRow = namedtuple("TeamRow", "tricode name rank wins losses")


def _conference_to_display_rows(conf, header_label):
    display = []
    selectable = []
    if conf is None or conf.empty:
        return display, selectable
    display.append(("header", header_label, None))
    for _, line in conf.iterrows():
        team = f"{line['TeamCity']} {line['TeamName']}"
        tr = constants.get_tricode_from_team(team)
        row = TeamRow(tr, team, int(line["PlayoffRank"]), int(line["WINS"]), int(line["LOSSES"]))
        display.append(("team", row, tr))
        selectable.append((tr, team))
    display.append(("sep", None, None))
    return display, selectable


def _build_teams_list(east, west):
    display = []
    selectable = []
    if east is not None and not east.empty:
        de, se = _conference_to_display_rows(east, " EAST ")
        display.extend(de)
        selectable.extend(se)
    if west is not None and not west.empty:
        dw, sw = _conference_to_display_rows(west, " WEST ")
        display.extend(dw)
        selectable.extend(sw)
    if not selectable:
        all_teams = [(t, constants.TRICODE_TO_TEAM_NAME.get(t, t)) for t in constants.TRICODE_TO_TEAM_ID]
        all_teams.sort(key=lambda x: x[1])
        for t, n in all_teams:
            display.append(("team", TeamRow(t, n, None, None, None), t))
            selectable.append((t, n))
    return display, selectable


def _draw_loading(stdscr, tricode, team_name, message="Loading"):
    height, width = stdscr.getmaxyx()
    stdscr.clear()
    try:
        stdscr.addstr(height // 2 - 2, max(0, (width - len(team_name) - 10) // 2), f" {tricode} - {team_name} ", curses.A_BOLD)
        stdscr.addstr(height // 2, max(0, (width - len(message) - 8) // 2), f" {message}... ", curses.A_DIM)
        stdscr.refresh()
    except curses.error:
        pass


def _load_team_page_data(api_client, team_id, tricode):
    with ThreadPoolExecutor(max_workers=8) as executor:
        fut_info = executor.submit(api_client.fetch_team_page_info, team_id)
        fut_pts = executor.submit(api_client.fetch_team_page_leader, StatCategoryAbbreviation.pts, tricode, "PTS")
        fut_reb = executor.submit(api_client.fetch_team_page_leader, StatCategoryAbbreviation.reb, tricode, "REB")
        fut_ast = executor.submit(api_client.fetch_team_page_leader, StatCategoryAbbreviation.ast, tricode, "AST")
        fut_upcoming = executor.submit(api_client.fetch_team_upcoming_games, tricode)
        fut_past = executor.submit(api_client.fetch_team_games, team_id)
        fut_roster = executor.submit(api_client.fetch_team_roster, team_id)
        info = fut_info.result()
        leader_data = {}
        for fut in (fut_pts, fut_reb, fut_ast):
            col, data = fut.result()
            if data:
                leader_data[col] = data
        upcoming = fut_upcoming.result()
        past = fut_past.result()
        roster_df = fut_roster.result()
    roster_list = roster_df.to_dict("records") if roster_df is not None and not roster_df.empty else []
    # Load head-to-head once (vs next opponent) to avoid API calls on every redraw
    h2h = {}
    if team_id and upcoming:
        try:
            date_str, g = upcoming[0]
            away = g.get("awayTeam", {})
            home = g.get("homeTeam", {})
            opp_tricode = away.get("teamTricode") if tricode.upper() == home.get("teamTricode", "") else home.get("teamTricode")
            opp_team_id = constants.TRICODE_TO_TEAM_ID.get(opp_tricode.upper()) if opp_tricode else None
            if opp_team_id:
                h2h = api_client.fetch_head_to_head(int(team_id), int(opp_team_id))
        except (TypeError, ValueError):
            pass
    return info, leader_data, upcoming, past, roster_list, h2h


def _draw_team_page_header(stdscr, tricode, team_name, cfg, color_ctx):
    symbol = " * " if tricode.upper() == config.favorite_team(cfg) else " "
    stdscr.addstr(0, 0, f"{symbol}{tricode} - {team_name} ", curses.A_BOLD | curses.A_REVERSE)
    stdscr.attron(curses.color_pair(color_ctx.get_team_highlight_pair(tricode)))
    stdscr.addstr(1, 0, " Team Page ")
    stdscr.attroff(curses.color_pair(color_ctx.get_team_highlight_pair(tricode)))


def _draw_team_season_section(draw, row, info):
    df = None
    if info is not None:
        try:
            if hasattr(info, "team_info_common") and hasattr(info.team_info_common, "get_data_frame"):
                df = info.team_info_common.get_data_frame()
            elif hasattr(info, "get_data_frames"):
                dfs = info.get_data_frames()
                if dfs and not dfs[0].empty:
                    df = dfs[0]
        except Exception:
            pass
    if df is None or df.empty:
        return row
    r = df.iloc[0]
    draw(row, " SEASON SUMMARY ", curses.A_BOLD | curses.A_REVERSE)
    row += 1
    draw(row, f"  Record: {int(r.get('W', 0))}-{int(r.get('L', 0))} | Conf: #{int(r.get('CONF_RANK', 0))} | Div: #{int(r.get('DIV_RANK', 0))}")
    return row + 2


def _draw_team_leaders_section(draw, row, max_row, leader_data):
    for title, col in constants.LEADER_CATEGORIES:
        if row >= max_row:
            return row
        draw(row, f" {title} ", curses.A_BOLD | curses.A_REVERSE)
        row += 1
        for pname, val in leader_data.get(col, []):
            if row >= max_row:
                return row
            draw(row, f"  * {pname} ({val:.1f})", curses.A_BOLD | curses.color_pair(2))
            row += 1
        row += 1
    return row


def _draw_team_roster_section(draw, row, max_row, roster_list, selected_roster_idx, top_3_names):
    if row >= max_row:
        return row
    draw(row, " ELENCO ", curses.A_BOLD | curses.A_REVERSE)
    row += 1
    if not roster_list:
        draw(row, "  Roster not available")
        return row + 2
    for i, r in enumerate(roster_list):
        if row >= max_row:
            return row
        full_name = str(r.get("PLAYER", "-"))
        pname = full_name[:28]
        num = str(r.get("NUM", ""))
        pos = str(r.get("POSITION", ""))
        is_top3 = full_name in top_3_names
        is_sel = i == selected_roster_idx
        attr = curses.A_BOLD | curses.color_pair(2) if is_top3 else 0
        if is_sel:
            attr = attr | curses.A_REVERSE
        draw(row, f"  #{num:<3} {pname:<28} {pos}", attr)
        row += 1
    return row + 2


def _draw_team_head_to_head_section(draw, row, max_row, tricode, h2h, upcoming, cfg):
    """Draw head-to-head vs next opponent (h2h is pre-fetched to avoid API calls on every redraw)."""
    if row >= max_row or not upcoming or not h2h:
        return row
    date_str, g = upcoming[0]
    away = g.get("awayTeam", {})
    home = g.get("homeTeam", {})
    opp_tricode = away.get("teamTricode") if tricode.upper() == home.get("teamTricode", "") else home.get("teamTricode")
    if not opp_tricode:
        return row
    if not h2h.get("last_meeting") and not (h2h.get("season_series") or {}).get("games"):
        return row
    draw(row, " " + config.get_text(cfg, "head_to_head") + f" vs {opp_tricode} ", curses.A_BOLD | curses.A_REVERSE)
    row += 1
    ss = h2h.get("season_series") or {}
    wins_a = ss.get("wins_a", 0) or 0
    wins_b = ss.get("wins_b", 0) or 0
    draw(row, f"  {config.get_text(cfg, 'season_series')}: {tricode} {wins_a}-{wins_b} {opp_tricode}")
    row += 1
    last = h2h.get("last_meeting") or {}
    if last.get("date"):
        pts_a, pts_b = last.get("pts_a"), last.get("pts_b")
        if pts_a is not None and pts_b is not None:
            draw(row, f"  {config.get_text(cfg, 'last_meeting')}: {last['date']}  {tricode} {pts_a}-{pts_b} {opp_tricode}")
        else:
            draw(row, f"  {config.get_text(cfg, 'last_meeting')}: {last['date']}  {last.get('matchup', '')}")
        row += 1
    return row + 2


def _draw_team_upcoming_section(draw, row, max_row, upcoming):
    if row >= max_row:
        return row
    draw(row, " UPCOMING GAMES ", curses.A_BOLD | curses.A_REVERSE)
    row += 1
    if not upcoming:
        draw(row, "  No games scheduled")
        return row + 2
    for date_str, g in upcoming:
        if row >= max_row:
            return row
        away = g.get("awayTeam", {})
        home = g.get("homeTeam", {})
        a, h = format_team_name(away), format_team_name(home)
        try:
            gt = parser.parse(g.get("gameTimeUTC", "") or "").replace(tzinfo=timezone.utc).astimezone(tz=None)
            time_str = gt.strftime("%H:%M")
        except Exception:
            time_str = "--:--"
        draw(row, f"  {date_str} {time_str} - {a} @ {h}")
        row += 1
    return row + 2


def _draw_team_past_section(draw, row, max_row, past):
    if row >= max_row:
        return row
    draw(row, " PAST GAMES ", curses.A_BOLD | curses.A_REVERSE)
    row += 1
    if not past:
        draw(row, "  -")
        return row + 2
    for gm in past[:5]:
        if row >= max_row:
            return row
        draw(row, f"  {gm.get('GAME_DATE', '')}: {gm.get('MATCHUP', '-')} {gm.get('WL', '-')} ({gm.get('PTS', '-')} pts)")
        row += 1
    return row + 2


def _draw_team_fun_fact_section(draw, row, max_row, tricode, width):
    if row >= max_row:
        return row
    draw(row, " FUN FACT ", curses.A_BOLD | curses.A_REVERSE)
    row += 1
    fact = constants.TEAM_FUN_FACTS.get(tricode.upper(), "NBA team.")
    for i in range(0, len(fact), width - 4):
        if row >= max_row:
            return row
        draw(row, "  " + fact[i:i + width - 4])
        row += 1
    return row


def show_team_player_card(stdscr, player_name, num, position, team_name, tricode, color_ctx):
    height, width = stdscr.getmaxyx()
    stdscr.clear()
    safe_addstr(stdscr, 0, 0, f" #{num} {player_name} ", curses.A_BOLD | curses.A_REVERSE, max_width=width)
    stdscr.attron(curses.color_pair(color_ctx.get_team_highlight_pair(tricode)))
    safe_addstr(stdscr, 1, 0, f" {team_name} ", max_width=width)
    stdscr.attroff(curses.color_pair(color_ctx.get_team_highlight_pair(tricode)))
    safe_addstr(stdscr, 3, 0, f"  Position: {position}", max_width=width)
    safe_addstr(stdscr, 5, 0, "  Game stats available when opening a box score and selecting the player.", max_width=width)
    safe_addstr(stdscr, height - 1, 0, " Press any key to go back ", curses.A_DIM, max_width=width)
    stdscr.refresh()
    wait_key(stdscr)


def _build_team_page_lines(width, max_lines, info, leader_data, roster_list, selected_roster_idx, top_3_names, tricode, h2h, upcoming, past, cfg):
    """Build team page content as a list of (text, attr). Returns (lines, content_height)."""
    lines = []

    def draw(y, text, attr=0):
        if y >= max_lines:
            return
        while len(lines) <= y:
            lines.append(("", 0))
        lines[y] = (text[: width - 1], attr)

    row = _draw_team_season_section(draw, 0, info)
    row = _draw_team_leaders_section(draw, row, max_lines, leader_data)
    row = _draw_team_roster_section(draw, row, max_lines, roster_list, selected_roster_idx, top_3_names)
    row = _draw_team_head_to_head_section(draw, row, max_lines, tricode, h2h, upcoming, cfg)
    row = _draw_team_upcoming_section(draw, row, max_lines, upcoming)
    row = _draw_team_past_section(draw, row, max_lines, past)
    row = _draw_team_fun_fact_section(draw, row, max_lines, tricode, width)
    return (lines, len(lines))


def show_team_page(stdscr, tricode, team_name, cfg, color_ctx, api_client, team_id=None):
    team_id = team_id or constants.TRICODE_TO_TEAM_ID.get(tricode.upper())
    if not team_id:
        return

    stdscr.clear()
    _draw_loading(stdscr, tricode, team_name, "Loading data")
    stdscr.refresh()
    curses.doupdate()

    try:
        info, leader_data, upcoming, past, roster_list, h2h = _load_team_page_data(api_client, team_id, tricode)
    except Exception:
        info, leader_data, upcoming, past, roster_list, h2h = None, {}, [], [], [], {}
    if info is None and not roster_list:
        try:
            height, width = stdscr.getmaxyx()
            stdscr.clear()
            stdscr.addstr(height // 2 - 1, 0, " Failed to load team data. Press any key. "[: width - 1], curses.A_BOLD | curses.A_REVERSE)
            stdscr.refresh()
            wait_key(stdscr)
        except curses.error:
            pass
        return
    selected_roster_idx = 0
    top_3_names = {name for col in ("PTS", "REB", "AST") if col in leader_data for name, _ in leader_data.get(col, [])}

    scroll_offset = 0
    max_content_lines = 800

    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        content_start = 2
        view_height = height - content_start - 2
        if view_height <= 0:
            view_height = 1

        try:
            _draw_team_page_header(stdscr, tricode, team_name, cfg, color_ctx)
            content_lines, content_height = _build_team_page_lines(
                width, max_content_lines, info, leader_data, roster_list, selected_roster_idx, top_3_names,
                tricode, h2h, upcoming, past, cfg
            )
            scroll_offset = max(0, min(scroll_offset, max(0, content_height - view_height)))
            for i in range(view_height):
                idx = scroll_offset + i
                if idx < content_height:
                    text, attr = content_lines[idx]
                    try:
                        if attr:
                            stdscr.attron(attr)
                        stdscr.addstr(content_start + i, 0, text)
                        if attr:
                            stdscr.attroff(attr)
                    except curses.error:
                        pass
            footer = " [↑][↓] Player  [PgUp][PgDn] Scroll  [Enter] Player  [Q] Back "
            stdscr.addstr(height - 1, 0, footer[: width - 1], curses.A_DIM)
        except (curses.error, Exception):
            try:
                stdscr.addstr(height - 1, 0, " [Q] Back ", curses.A_DIM)
            except curses.error:
                pass

        stdscr.refresh()
        stdscr.nodelay(False)
        key = stdscr.getch()
        stdscr.nodelay(True)

        if key == ord("q") or key == ord("Q") or key == 27:
            break
        if key == curses.KEY_PPAGE:
            scroll_offset = max(0, scroll_offset - max(1, view_height // 2))
        elif key == curses.KEY_NPAGE:
            scroll_offset = min(max(0, content_height - view_height), scroll_offset + max(1, view_height // 2))
        elif key == curses.KEY_UP and roster_list:
            selected_roster_idx = max(0, selected_roster_idx - 1)
        elif key == curses.KEY_DOWN and roster_list:
            selected_roster_idx = min(len(roster_list) - 1, selected_roster_idx + 1)
        elif (key == ord("\n") or key == ord("\r")) and roster_list and 0 <= selected_roster_idx < len(roster_list):
            r = roster_list[selected_roster_idx]
            player_name = str(r.get("PLAYER", "-"))
            person_id = r.get("PLAYER_ID") or r.get("player_id")
            if person_id is not None:
                player_ui.show_player_page(stdscr, person_id, player_name, tricode, cfg, color_ctx, api_client)
            else:
                show_team_player_card(stdscr, player_name, str(r.get("NUM", "")), str(r.get("POSITION", "")), team_name, tricode, color_ctx)


def show_teams_picker(stdscr, east, west, cfg, color_ctx, api_client):
    all_display, all_selectable = _build_teams_list(east, west)
    height, width = stdscr.getmaxyx()
    selected = 0
    offset = 0
    search_query = ""

    while True:
        if search_query:
            q = search_query.lower()
            teams = [(t, n) for t, n in all_selectable if q in t.lower() or q in n.lower()]
            if not teams:
                teams = all_selectable
            display = [("team", TeamRow(t, n, None, None, None), t) for t, n in teams]
        else:
            teams = all_selectable
            display = all_display

        selected = min(selected, len(teams) - 1) if teams else 0
        list_height = min(height - 5, len(display))
        display_rows = [i for i, (dtype, _, _) in enumerate(display) if dtype == "team"]
        if display_rows and selected < len(display_rows):
            sel_display_idx = display_rows[selected]
            if sel_display_idx < offset:
                offset = sel_display_idx
            elif sel_display_idx >= offset + list_height:
                offset = max(0, sel_display_idx - list_height + 1)

        stdscr.clear()
        try:
            stdscr.addstr(0, 0, " TEAMS AND STANDINGS - SELECT TO OPEN ", curses.A_BOLD | curses.A_REVERSE)
            hint = " ↑↓ navigate | Type to search | Enter open | [Q] back "
            if search_query:
                hint = f" Busca: {search_query}_ "
            stdscr.addstr(1, 0, hint[: width - 1], curses.A_DIM)
        except curses.error:
            pass

        team_row_idx = 0
        for i in range(list_height):
            idx = offset + i
            if idx >= len(display):
                break
            dtype, data, tr = display[idx]
            if dtype == "header":
                try:
                    stdscr.addstr(3 + i, 0, data, curses.A_BOLD | curses.A_REVERSE)
                except curses.error:
                    pass
            elif dtype == "sep":
                try:
                    stdscr.addstr(3 + i, 0, "")
                except curses.error:
                    pass
            else:
                row = data  # TeamRow
                if search_query:
                    line = f"  {row.tricode} - {row.name}"
                else:
                    rank_str = f"#{row.rank}" if row.rank else ""
                    rec = f" ({row.wins}-{row.losses})" if row.wins is not None and row.losses is not None else ""
                    line = f"  {rank_str:<3} {row.tricode} - {row.name}{rec}"
                is_sel = (teams and team_row_idx == selected)
                attr = curses.A_REVERSE if is_sel else 0
                if row.rank and row.rank <= 6:
                    attr |= curses.color_pair(2)
                elif row.rank and row.rank <= 10:
                    attr |= curses.color_pair(3)
                try:
                    stdscr.attron(curses.color_pair(color_ctx.get_team_highlight_pair(row.tricode)))
                    stdscr.addstr(3 + i, 0, line[: width - 1], attr)
                    stdscr.attroff(curses.color_pair(color_ctx.get_team_highlight_pair(row.tricode)))
                except curses.error:
                    pass
                team_row_idx += 1

        try:
            footer = " [up/down] navigate  [Enter] open team  [Q] back "
            stdscr.addstr(height - 1, 0, footer[: width - 1], curses.A_DIM)
        except curses.error:
            pass

        stdscr.refresh()
        stdscr.nodelay(False)
        key = stdscr.getch()
        stdscr.nodelay(True)

        if key == ord("q") or key == ord("Q") or key == 27:
            if search_query:
                search_query = ""
                continue
            return
        elif key == curses.KEY_BACKSPACE or key == 127:
            search_query = search_query[:-1]
            offset = 0
        elif key == curses.KEY_UP:
            selected = max(0, selected - 1)
        elif key == curses.KEY_DOWN:
            selected = min(len(teams) - 1, selected + 1)
        elif key == ord("\n") or key == ord("\r"):
            if teams:
                tricode, name = teams[selected]
                show_team_page(stdscr, tricode, name, cfg, color_ctx, api_client)
        elif key >= 32 and key < 127:
            search_query += chr(key).lower()
            selected = 0
            offset = 0
