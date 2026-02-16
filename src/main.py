#!/usr/bin/env python3
"""Entrada do NBA Terminal App: loop principal TUI, atalhos de teclado e modo CLI."""

from __future__ import annotations

import curses
import time
from types import SimpleNamespace
from typing import Optional
from datetime import datetime, timezone, timedelta
from dateutil import parser

import typer

import config
import api
import constants
from key_handlers import get_action
from core import categorize_games, format_live_clock
from ui.dashboard import draw_dashboard, draw_splash
from ui import colors
from ui.screens import show_config_screen, prompt_date
from ui.teams import show_teams_picker, show_team_page
from ui.boxscore import show_game_stats
from ui.help import show_help
from ui.helpers import format_team_name


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

    draw_splash(stdscr, constants.SPLASH_LOADING_GAMES)
    stdscr.refresh()
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
    games, scoreboard_date = api_client.fetch_games(game_date.isoformat())

    draw_splash(stdscr, constants.SPLASH_LOADING_STANDINGS)
    stdscr.refresh()
    east, west = api_client.fetch_standings()
    draw_splash(stdscr, constants.SPLASH_LOADING_LEADERS)
    stdscr.refresh()
    league_leaders = api_client.fetch_league_leaders()
    em_andamento, nao_comecaram, finalizados = categorize_games(games)
    game_list = em_andamento + nao_comecaram + finalizados

    last_refresh = time.time()
    filter_favorite_only = False
    game_sort_mode = config.game_sort(cfg)

    def _effective_refresh_interval(has_live: bool) -> int:
        base = config.refresh_interval(cfg)
        if base == 0:
            return 0
        if config.refresh_mode(cfg) == "auto":
            return 30 if has_live else 120
        return base

    while True:
        refresh_interval = _effective_refresh_interval(bool(em_andamento))
        tz_info = config.get_tzinfo(cfg)
        game_list = draw_dashboard(
            stdscr, games, scoreboard_date, east, west, game_date.isoformat(), cfg, api_client, color_ctx,
            last_refresh=last_refresh, league_leaders=league_leaders,
            filter_favorite_only=filter_favorite_only, game_sort=game_sort_mode,
            tz_info=tz_info,
        )

        try:
            key = stdscr.getch()
        except Exception:
            key = -1

        action = get_action(key, len(game_list))

        if action == "quit":
            break
        if action == "refresh":
            games, scoreboard_date = api_client.fetch_games(game_date.isoformat())
            east, west = api_client.fetch_standings()
            league_leaders = api_client.fetch_league_leaders()
            em_andamento, nao_comecaram, finalizados = categorize_games(games)
            game_list = em_andamento + nao_comecaram + finalizados
            last_refresh = time.time()
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
        elif action and action.startswith("game:"):
            idx = int(action.split(":")[1])
            stdscr.nodelay(False)
            show_game_stats(stdscr, game_list[idx], cfg, color_ctx, api_client)
            stdscr.nodelay(True)


def _format_game_line(game):
    away = game.get("awayTeam", {})
    home = game.get("homeTeam", {})
    away_name = format_team_name(away)
    home_name = format_team_name(home)
    away_t = away.get("teamTricode", "")
    home_t = home.get("teamTricode", "")
    away_s = away.get("score") or 0
    home_s = home.get("score") or 0
    status = game.get("gameStatusText", "")
    if away_s or home_s:
        status = format_live_clock(game) or status
    try:
        game_time = parser.parse(game["gameTimeUTC"]).replace(tzinfo=timezone.utc).astimezone(tz=None)
        time_str = game_time.strftime("%H:%M")
    except Exception:
        time_str = "-"
    placar = f"{away_s} x {home_s}" if (away_s or home_s) else "vs"
    return f"{away_t} {away_name} @ {home_t} {home_name}  {placar}  [{status}]  {time_str}"


def _print_standings_text(east, west):
    def print_conf(conf, title):
        if conf is None or conf.empty:
            return
        print(title)
        print(f"  {'#':<2} {'Team':<28} {'W':<4} {'L':<4} {'PCT':<6}")
        print("  " + "-" * 46)
        for _, line in conf.head(15).iterrows():
            rank = int(line["PlayoffRank"])
            team = f"{line['TeamCity']} {line['TeamName']}"
            w, l_ = int(line["WINS"]), int(line["LOSSES"])
            pct = line["WinPCT"]
            print(f"  {rank:<2} {team[:26]:<28} {w:<4} {l_:<4} {pct:.1%}")
        print()

    print_conf(east, "=== EAST ===")
    print_conf(west, "=== WEST ===")


def _export_games_json(games, date_str):
    import json
    out = {"date": date_str, "games": games}
    print(json.dumps(out, indent=2, ensure_ascii=False))


def _export_games_csv(games, date_str):
    import csv
    import sys
    writer = csv.writer(sys.stdout)
    writer.writerow(["date", "awayTeam", "homeTeam", "awayScore", "homeScore", "status"])
    for g in games:
        away = g.get("awayTeam", {})
        home = g.get("homeTeam", {})
        writer.writerow([
            date_str,
            away.get("teamTricode", ""),
            home.get("teamTricode", ""),
            away.get("score", ""),
            home.get("score", ""),
            g.get("gameStatusText", ""),
        ])


def _export_standings_json(east, west):
    import json
    out = {}
    if east is not None and not east.empty:
        out["east"] = east.to_dict(orient="records")
    if west is not None and not west.empty:
        out["west"] = west.to_dict(orient="records")
    print(json.dumps(out, indent=2, ensure_ascii=False))


def _export_standings_csv(east, west):
    import csv
    import sys
    writer = csv.writer(sys.stdout)
    writer.writerow(["conference", "rank", "team", "wins", "losses", "pct"])
    for conf_name, conf in [("East", east), ("West", west)]:
        if conf is not None and not getattr(conf, "empty", True):
            for _, row in conf.head(15).iterrows():
                team = f"{row['TeamCity']} {row['TeamName']}"
                writer.writerow([
                    conf_name,
                    int(row["PlayoffRank"]),
                    team,
                    int(row["WINS"]),
                    int(row["LOSSES"]),
                    f"{row['WinPCT']:.3f}",
                ])


def run_cli(args, api_client):
    if getattr(args, "export_games", None):
        games, date_str = api_client.fetch_games()
        if args.export_games == "json":
            _export_games_json(games or [], date_str or "")
        else:
            _export_games_csv(games or [], date_str or "")
        return
    if getattr(args, "export_standings", None):
        east, west = api_client.fetch_standings()
        if args.export_standings == "json":
            _export_standings_json(east, west)
        else:
            _export_standings_csv(east, west)
        return
    if args.today_games:
        games, date_str = api_client.fetch_games()
        print(f"Games - {date_str}")
        print("-" * 60)
        if not games:
            print("No games or failed to load.")
        else:
            for g in games:
                print(_format_game_line(g))
        return
    if args.standings:
        east, west = api_client.fetch_standings()
        if east is None and west is None:
            print("Failed to load standings.")
        else:
            _print_standings_text(east, west)
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
                print(_format_game_line(g))
        return


def run():
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
    help="NBA Terminal App – jogos, standings e box score no terminal. Sem argumentos, abre o modo TUI.",
    no_args_is_help=False,
)


@app.callback(invoke_without_command=True)
def main_callback(
    ctx: typer.Context,
    today_games: bool = typer.Option(False, "-t", "--today-games", help="Listar jogos de hoje e sair"),
    standings: bool = typer.Option(False, "-s", "--standings", help="Mostrar standings East/West e sair"),
    last_results: bool = typer.Option(False, "-l", "--last-results", help="Últimos resultados (dia mais recente com jogos) e sair"),
    export_games: Optional[str] = typer.Option(None, "--export-games", help="Exportar jogos de hoje: json ou csv"),
    export_standings: Optional[str] = typer.Option(None, "--export-standings", help="Exportar standings: json ou csv"),
) -> None:
    if export_games is not None and export_games not in ("json", "csv"):
        raise typer.BadParameter("--export-games must be json or csv")
    if export_standings is not None and export_standings not in ("json", "csv"):
        raise typer.BadParameter("--export-standings must be json or csv")
    if ctx.invoked_subcommand is not None:
        return
    if today_games or standings or last_results or export_games or export_standings:
        args = SimpleNamespace(
            today_games=today_games,
            standings=standings,
            last_results=last_results,
            export_games=export_games,
            export_standings=export_standings,
        )
        run_cli(args, api.ApiClient())
    else:
        run()


if __name__ == "__main__":
    app()
