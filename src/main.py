#!/usr/bin/env python3
"""NBA Terminal App entry point: main TUI loop, keyboard shortcuts, and CLI mode."""

from __future__ import annotations

import curses
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
from typing import Optional
from datetime import datetime, timezone, timedelta
from dateutil import parser

import typer

import config
import constants
from key_handlers import get_action
from core import categorize_games
from ui.dashboard import draw_dashboard, draw_splash
from ui import colors
from ui.screens import show_config_screen, prompt_date
from ui.teams import show_teams_picker, show_team_page
from ui.boxscore import show_game_stats
from ui.help import show_help
import cli_formatters


def main(stdscr, cfg, api_client, color_ctx):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(500)

    curses.start_color()
    curses.use_default_colors()
    color_ctx.init_pairs()

    draw_splash(stdscr, constants.SPLASH_STARTING)
    stdscr.refresh()
    time.sleep(0.3)

    today = datetime.now().date()
    saved_date = config.last_game_date(cfg)
    if saved_date:
        try:
            game_date = datetime.strptime(saved_date, "%Y-%m-%d").date()
            if game_date > today:
                game_date = today
        except (ValueError, TypeError):
            game_date = today
    else:
        game_date = today
    game_date_iso = game_date.isoformat()

    draw_splash(stdscr, constants.SPLASH_LOADING_GAMES)
    stdscr.refresh()

    result_holder: list = [None]
    load_error_holder: list = [None]

    def load_initial_data() -> None:
        try:
            with ThreadPoolExecutor(max_workers=3) as executor:
                fut_games = executor.submit(api_client.fetch_games, game_date_iso)
                fut_standings = executor.submit(api_client.fetch_standings)
                fut_leaders = executor.submit(api_client.fetch_league_leaders)
                games, scoreboard_date = fut_games.result()
                east, west = fut_standings.result()
                league_leaders = fut_leaders.result()
            result_holder[0] = (games, scoreboard_date, east, west, league_leaders)
        except Exception as e:
            load_error_holder[0] = e

    load_thread = threading.Thread(target=load_initial_data, daemon=True)
    load_thread.start()
    waited = 0
    while load_thread.is_alive() and waited < constants.INITIAL_LOAD_TIMEOUT:
        load_thread.join(timeout=0.08)
        waited += 0.08
        if load_thread.is_alive():
            progress = (time.time() * 2) % 1.0
            draw_splash(stdscr, constants.SPLASH_LOADING_GAMES, progress=progress)
    if result_holder[0] is not None:
        games, scoreboard_date, east, west, league_leaders = result_holder[0]
    else:
        cache_holder: list = [None]
        def read_cache() -> None:
            cache_holder[0] = api_client.get_initial_data_from_cache_only(game_date_iso)
        cache_thread = threading.Thread(target=read_cache, daemon=True)
        cache_thread.start()
        cache_thread.join(timeout=constants.CACHE_READ_TIMEOUT)
        if cache_holder[0] is not None:
            games, scoreboard_date, east, west, league_leaders = cache_holder[0]
            api_client._last_games_from_cache = bool(games)
            api_client._last_standings_from_cache = east is not None or west is not None
            api_client._last_leaders_from_cache = bool(
                league_leaders.get("PTS") or league_leaders.get("REB") or league_leaders.get("AST")
            )
        else:
            games, scoreboard_date, east, west = [], game_date_iso, None, None
            league_leaders = {"PTS": [], "REB": [], "AST": [], "TDBL": []}
        if not games and east is None and west is None:
            api_client._last_error = "Connection timed out or unavailable. Press [R] to retry."

    em_andamento, nao_comecaram, finalizados = categorize_games(games)
    game_list = em_andamento + nao_comecaram + finalizados

    last_refresh = time.time()
    filter_favorite_only = False
    game_sort_mode = config.game_sort(cfg)
    standings_scroll = 0
    refresh_in_progress = False

    def _effective_refresh_interval(has_live: bool) -> int:
        base = config.refresh_interval(cfg)
        if base == 0:
            return 0
        if config.refresh_mode(cfg) == "auto":
            return 30 if has_live else 120
        return base

    tz_info = config.get_tzinfo(cfg)

    while True:
        refresh_interval = _effective_refresh_interval(bool(em_andamento))
        result = draw_dashboard(
            stdscr, games, scoreboard_date, east, west, game_date.isoformat(), cfg, api_client, color_ctx,
            last_refresh=last_refresh, league_leaders=league_leaders,
            filter_favorite_only=filter_favorite_only, game_sort=game_sort_mode,
            tz_info=tz_info, standings_scroll=standings_scroll,
            refresh_in_progress=refresh_in_progress,
        )
        game_list, max_standings_scroll = result[0], result[1] if isinstance(result, tuple) else 0

        try:
            key = stdscr.getch()
        except Exception:
            key = -1

        action = get_action(key, len(game_list))

        if action == "quit":
            break
        if action == "refresh":
            refresh_in_progress = True
            try:
                with ThreadPoolExecutor(max_workers=3) as executor:
                    fut_games = executor.submit(api_client.fetch_games, game_date.isoformat())
                    fut_standings = executor.submit(api_client.fetch_standings)
                    fut_leaders = executor.submit(api_client.fetch_league_leaders)
                    games, scoreboard_date = fut_games.result()
                    east, west = fut_standings.result()
                    league_leaders = fut_leaders.result()
                em_andamento, nao_comecaram, finalizados = categorize_games(games)
                game_list = em_andamento + nao_comecaram + finalizados
                last_refresh = time.time()
            finally:
                refresh_in_progress = False
        elif key == -1 and refresh_interval > 0 and em_andamento and (time.time() - last_refresh) >= refresh_interval:
            games, scoreboard_date = api_client.fetch_games(game_date.isoformat())
            em_andamento, nao_comecaram, finalizados = categorize_games(games)
            game_list = em_andamento + nao_comecaram + finalizados
            last_refresh = time.time()
        elif action == "config":
            stdscr.nodelay(False)
            show_config_screen(stdscr, cfg)
            game_sort_mode = config.game_sort(cfg)
            color_ctx.set_theme(config.theme(cfg))
            color_ctx.init_pairs()
            stdscr.nodelay(True)
        elif action == "help":
            stdscr.nodelay(False)
            show_help(stdscr, cfg)
            stdscr.nodelay(True)
        elif action == "filter":
            filter_favorite_only = not filter_favorite_only
        elif action == "teams":
            stdscr.nodelay(False)
            show_teams_picker(stdscr, east, west, cfg, color_ctx, api_client)
            stdscr.nodelay(True)
        elif action == "date":
            target_date = prompt_date(stdscr, game_date)
            if target_date:
                game_date = target_date
                cfg["last_game_date"] = game_date.isoformat()
                config.save_config(cfg)
                games, scoreboard_date = api_client.fetch_games(game_date.isoformat())
                em_andamento, nao_comecaram, finalizados = categorize_games(games)
                game_list = em_andamento + nao_comecaram + finalizados
                last_refresh = time.time()
        elif action == "favorite_team":
            stdscr.nodelay(False)
            tricode = config.favorite_team(cfg)
            team_name = constants.TRICODE_TO_TEAM_NAME.get(tricode, tricode)
            show_team_page(stdscr, tricode, team_name, cfg, color_ctx, api_client)
            stdscr.nodelay(True)
        elif action == "today":
            game_date = datetime.now().date()
            cfg["last_game_date"] = game_date.isoformat()
            config.save_config(cfg)
            games, scoreboard_date = api_client.fetch_games(game_date.isoformat())
            em_andamento, nao_comecaram, finalizados = categorize_games(games)
            game_list = em_andamento + nao_comecaram + finalizados
            last_refresh = time.time()
        elif action == "prev_day":
            game_date -= timedelta(days=1)
            cfg["last_game_date"] = game_date.isoformat()
            config.save_config(cfg)
            games, scoreboard_date = api_client.fetch_games(game_date.isoformat())
            em_andamento, nao_comecaram, finalizados = categorize_games(games)
            game_list = em_andamento + nao_comecaram + finalizados
            last_refresh = time.time()
        elif action == "next_day":
            game_date += timedelta(days=1)
            cfg["last_game_date"] = game_date.isoformat()
            config.save_config(cfg)
            games, scoreboard_date = api_client.fetch_games(game_date.isoformat())
            em_andamento, nao_comecaram, finalizados = categorize_games(games)
            game_list = em_andamento + nao_comecaram + finalizados
            last_refresh = time.time()
        elif action == "scroll_up" and max_standings_scroll > 0:
            standings_scroll = max(0, standings_scroll - 1)
        elif action == "scroll_down" and max_standings_scroll > 0:
            standings_scroll = min(max_standings_scroll, standings_scroll + 1)
        elif action and action.startswith("game:"):
            idx = int(action.split(":")[1])
            stdscr.nodelay(False)
            show_game_stats(stdscr, game_list[idx], cfg, color_ctx, api_client)
            stdscr.nodelay(True)


def run_cli(args, api_client):
    cfg = config.load_config()
    tz_info = config.get_tzinfo(cfg)
    if getattr(args, "export_games", None):
        games, date_str = api_client.fetch_games()
        if args.export_games == "json":
            cli_formatters.export_games_json(games or [], date_str or "")
        else:
            cli_formatters.export_games_csv(games or [], date_str or "")
        return
    if getattr(args, "export_standings", None):
        east, west = api_client.fetch_standings()
        if args.export_standings == "json":
            cli_formatters.export_standings_json(east, west)
        else:
            cli_formatters.export_standings_csv(east, west)
        return
    if getattr(args, "export_boxscore", None):
        game_id = (args.export_boxscore or "").strip()
        fmt = getattr(args, "export_boxscore_format", "json") or "json"
        if not game_id:
            print("Error: game ID required for --export-boxscore", file=sys.stderr)
            return
        game_data = api_client.get_box_score(game_id)
        if game_data is None:
            print("Error: box score not found or failed to load.", file=sys.stderr)
            return
        if fmt == "json":
            cli_formatters.export_boxscore_json(game_data)
        else:
            cli_formatters.export_boxscore_csv(game_data)
        return
    if args.today_games:
        games, date_str = api_client.fetch_games()
        print(f"Games - {date_str}")
        print("-" * 60)
        if not games:
            print("No games or failed to load.")
        else:
            for g in games:
                print(cli_formatters.format_game_line(g, tz_info))
        return
    if args.standings:
        east, west = api_client.fetch_standings()
        if east is None and west is None:
            print("Failed to load standings.")
        else:
            cli_formatters.print_standings_text(east, west)
        return
    if args.last_results:
        today = datetime.now().date()
        max_days_back = 14
        games, date_str = [], None
        for d in range(1, max_days_back + 1):
            check_date = (today - timedelta(days=d)).isoformat()
            games, date_str = api_client.fetch_games(check_date)
            if games:
                break
        print(f"Last results - {date_str or 'not found'}")
        print("-" * 60)
        if not games:
            print("No games found in the last {} days or failed to load.".format(max_days_back))
        else:
            for g in games:
                print(cli_formatters.format_game_line(g, tz_info))
        return
    if getattr(args, "team_next", None):
        tricode = (args.team_next or "").strip().upper()
        team_name = constants.TRICODE_TO_TEAM_NAME.get(tricode, tricode)
        upcoming = api_client.fetch_team_upcoming_games(tricode)
        print(f"Next games - {tricode} {team_name}")
        print("-" * 60)
        if not upcoming:
            print("No upcoming games found for this team.")
        else:
            for date_str, g in upcoming:
                print(cli_formatters.format_upcoming_team_game(date_str, g, tz_info))
        return
    if getattr(args, "team_last", None):
        tricode = (args.team_last or "").strip().upper()
        team_name = constants.TRICODE_TO_TEAM_NAME.get(tricode, tricode)
        team_id = constants.TRICODE_TO_TEAM_ID.get(tricode)
        if not team_id:
            print(f"Unknown team: {tricode}")
            return
        past = api_client.fetch_team_games(team_id, limit=10)
        print(f"Last games - {tricode} {team_name}")
        print("-" * 60)
        if not past:
            print("No recent games found for this team.")
        else:
            for row in past:
                print(cli_formatters.format_past_team_game(row))
        return


def run():
    print("Starting NBA Terminal App...", flush=True)
    sys.stdout.flush()
    sys.stderr.flush()
    import api
    import logging_config
    logging_config.setup_logging()
    cfg = config.load_config()
    api_client = api.ApiClient()
    color_ctx = colors.ColorContext(theme=config.theme(cfg))
    try:
        curses.wrapper(lambda stdscr: main(stdscr, cfg, api_client, color_ctx))
    except KeyboardInterrupt:
        pass
    print("Goodbye! 🏀")


app = typer.Typer(
    name="nba-terminal",
    help="NBA Terminal App – games, standings and box score in the terminal. With no arguments, opens TUI mode.",
    no_args_is_help=False,
)


def _validate_tricode(value: Optional[str], flag_name: str) -> Optional[str]:
    if not value or not value.strip():
        return None
    tricode = value.strip().upper()
    if tricode not in constants.TRICODE_TO_TEAM_ID:
        raise typer.BadParameter(f"Unknown team '{value}'. Use a 3-letter code (e.g. LAL, BOS, GSW).")
    return tricode


@app.callback(invoke_without_command=True)
def main_callback(
    ctx: typer.Context,
    today_games: bool = typer.Option(False, "-t", "--today-games", help="List today's games and exit"),
    standings: bool = typer.Option(False, "-s", "--standings", help="Show East/West standings and exit"),
    last_results: bool = typer.Option(False, "-l", "--last-results", help="Last results (most recent day with games) and exit"),
    team_next: Optional[str] = typer.Option(None, "-n", "--team-next", help="Next/upcoming games for a team (e.g. LAL, BOS)"),
    team_last: Optional[str] = typer.Option(None, "-a", "--team-last", help="Last/recent games for a team (e.g. LAL, BOS)"),
    export_games: Optional[str] = typer.Option(None, "-e", "--export-games", help="Export today's games: json or csv"),
    export_standings: Optional[str] = typer.Option(None, "-x", "--export-standings", help="Export standings: json or csv"),
    export_boxscore: Optional[str] = typer.Option(None, "-b", "--export-boxscore", help="Export box score by game ID (e.g. 0042400123)"),
    export_boxscore_format: Optional[str] = typer.Option("json", "--export-boxscore-format", help="Format for --export-boxscore: json or csv"),
) -> None:
    if export_games is not None and export_games not in ("json", "csv"):
        raise typer.BadParameter("--export-games must be json or csv")
    if export_standings is not None and export_standings not in ("json", "csv"):
        raise typer.BadParameter("--export-standings must be json or csv")
    if export_boxscore_format is not None and export_boxscore_format not in ("json", "csv"):
        raise typer.BadParameter("--export-boxscore-format must be json or csv")
    if team_next is not None:
        team_next = _validate_tricode(team_next, "--team-next")
    if team_last is not None:
        team_last = _validate_tricode(team_last, "--team-last")
    if ctx.invoked_subcommand is not None:
        return
    if today_games or standings or last_results or team_next or team_last or export_games or export_standings or export_boxscore:
        import api
        args = SimpleNamespace(
            today_games=today_games,
            standings=standings,
            last_results=last_results,
            team_next=team_next,
            team_last=team_last,
            export_games=export_games,
            export_standings=export_standings,
            export_boxscore=export_boxscore,
            export_boxscore_format=export_boxscore_format or "json",
        )
        run_cli(args, api.ApiClient())
    else:
        run()


if __name__ == "__main__":
    app()
