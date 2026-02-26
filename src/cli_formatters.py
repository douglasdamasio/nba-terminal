"""CLI formatters and exporters: games, standings, box score (text output, JSON, CSV)."""
from __future__ import annotations

import csv
import json
import sys
from datetime import timezone
from typing import Any, List, Optional

from dateutil import parser

import config
from core import format_live_clock
from ui.helpers import format_team_name


def format_game_line(game: dict, tz_info=None) -> str:
    """Format a single game line for CLI output."""
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
        game_time = parser.parse(game["gameTimeUTC"]).replace(tzinfo=timezone.utc)
        if tz_info:
            game_time = game_time.astimezone(tz_info)
        else:
            game_time = game_time.astimezone(tz=None)
        time_str = game_time.strftime("%H:%M")
    except Exception:
        time_str = "-"
    placar = f"{away_s} x {home_s}" if (away_s or home_s) else "vs"
    return f"{away_t} {away_name} @ {home_t} {home_name}  {placar}  [{status}]  {time_str}"


def format_upcoming_team_game(date_str: str, game: dict, tz_info=None) -> str:
    """Format upcoming team game line for CLI."""
    away = game.get("awayTeam", {})
    home = game.get("homeTeam", {})
    away_name = format_team_name(away)
    home_name = format_team_name(home)
    try:
        game_time = parser.parse(game.get("gameTimeUTC") or "").replace(tzinfo=timezone.utc)
        if tz_info:
            game_time = game_time.astimezone(tz_info)
        else:
            game_time = game_time.astimezone(tz=None)
        time_str = game_time.strftime("%H:%M")
    except Exception:
        time_str = "--:--"
    return f"{date_str}  {time_str}  {away_name} @ {home_name}"


def format_past_team_game(row: dict) -> str:
    """Format past team game row for CLI."""
    date_str = row.get("GAME_DATE", "")
    matchup = row.get("MATCHUP", "-")
    wl = row.get("WL", "")
    pts = row.get("PTS", "")
    return f"{date_str}  {matchup}  {wl}  ({pts} pts)"


def print_standings_text(east, west) -> None:
    """Print East/West standings to stdout."""
    def print_conf(conf, title):
        if conf is None or getattr(conf, "empty", True):
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


def export_games_json(games: list, date_str: str) -> None:
    """Export games to stdout as JSON."""
    out = {"date": date_str, "games": games}
    print(json.dumps(out, indent=2, ensure_ascii=False))


def export_games_csv(games: list, date_str: str) -> None:
    """Export games to stdout as CSV."""
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


def export_standings_json(east, west) -> None:
    """Export standings to stdout as JSON."""
    out = {}
    if east is not None and not east.empty:
        out["east"] = east.to_dict(orient="records")
    if west is not None and not west.empty:
        out["west"] = west.to_dict(orient="records")
    print(json.dumps(out, indent=2, ensure_ascii=False))


def export_standings_csv(east, west) -> None:
    """Export standings to stdout as CSV."""
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


def _box_score_players_list(game_data: dict) -> List[dict]:
    """Extract flat list of players with team from box score game_data."""
    out = []
    for side in ("awayTeam", "homeTeam"):
        team = game_data.get(side, {})
        tricode = team.get("teamTricode", "")
        for p in team.get("players", []):
            rec = {
                "name": p.get("name", "-"),
                "jerseyNum": p.get("jerseyNum", ""),
                "teamTricode": tricode,
                "statistics": p.get("statistics", {}),
            }
            out.append(rec)
    return out


def export_boxscore_json(game_data: dict) -> None:
    """Export box score to stdout as JSON."""
    away = game_data.get("awayTeam", {})
    home = game_data.get("homeTeam", {})
    out = {
        "gameId": game_data.get("gameId"),
        "gameStatusText": game_data.get("gameStatusText"),
        "awayTeam": {
            "teamId": away.get("teamId"),
            "teamTricode": away.get("teamTricode"),
            "score": away.get("score"),
            "players": [
                {"name": p.get("name"), "jerseyNum": p.get("jerseyNum"), "statistics": p.get("statistics", {})}
                for p in away.get("players", [])
            ],
        },
        "homeTeam": {
            "teamId": home.get("teamId"),
            "teamTricode": home.get("teamTricode"),
            "score": home.get("score"),
            "players": [
                {"name": p.get("name"), "jerseyNum": p.get("jerseyNum"), "statistics": p.get("statistics", {})}
                for p in home.get("players", [])
            ],
        },
    }
    print(json.dumps(out, indent=2, ensure_ascii=False))


def export_boxscore_csv(game_data: dict) -> None:
    """Export box score players to stdout as CSV."""
    writer = csv.writer(sys.stdout)
    writer.writerow(["team", "jersey", "name", "points", "reboundsTotal", "assists", "steals", "blocks", "turnovers"])
    for side in ("awayTeam", "homeTeam"):
        team = game_data.get(side, {})
        tricode = team.get("teamTricode", "")
        for p in team.get("players", []):
            stats = p.get("statistics", {})
            writer.writerow([
                tricode,
                p.get("jerseyNum", ""),
                p.get("name", ""),
                stats.get("points", ""),
                stats.get("reboundsTotal", ""),
                stats.get("assists", ""),
                stats.get("steals", ""),
                stats.get("blocks", ""),
                stats.get("turnovers", ""),
            ])
