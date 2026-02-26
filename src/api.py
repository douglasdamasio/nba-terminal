"""NBA API client: games, standings, league leaders, box score, and team data (cache and retry)."""
from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timezone, timedelta
from typing import Any, Callable, Optional, Tuple

from dateutil import parser
import pandas as pd

from cachetools import TTLCache
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

from nba_api.live.nba.endpoints import scoreboard, boxscore
from nba_api.stats.endpoints import (
    commonplayerinfo,
    commonteamroster,
    leaguegamelog,
    leaguestandingsv3,
    playergamelog,
    scoreboardv3,
    teamgamelog,
    teaminfocommon,
    leagueleaders,
)
from nba_api.stats.library.parameters import PlayerOrTeamAbbreviation, Season, StatCategoryAbbreviation

import config
import constants


def _disk_cache_dir() -> str:
    d = os.path.join(config.CONFIG_DIR, "cache")
    os.makedirs(d, exist_ok=True)
    return d


def _disk_cache_get(key: str, ttl: int) -> Optional[Any]:
    path = os.path.join(_disk_cache_dir(), f"{key}.json")
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        ts = data.get("ts", 0)
        if time.time() - ts >= ttl:
            return None
        return data.get("data")
    except (json.JSONDecodeError, OSError):
        return None


def _disk_cache_set(key: str, value: Any) -> None:
    path = os.path.join(_disk_cache_dir(), f"{key}.json")
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"ts": time.time(), "data": value}, f, indent=0)
    except OSError:
        pass


def _disk_cache_get_offline(key: str, max_age_seconds: int) -> Optional[Any]:
    """Return cached data if file exists and age <= max_age_seconds (for offline fallback)."""
    path = os.path.join(_disk_cache_dir(), f"{key}.json")
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        ts = data.get("ts", 0)
        if time.time() - ts > max_age_seconds:
            return None
        return data.get("data")
    except (json.JSONDecodeError, OSError):
        return None


def _user_facing_error(exc: Exception, default_prefix: str) -> str:
    """Short, user-friendly message derived from the exception."""
    msg = str(exc).strip() or type(exc).__name__
    err_lower = msg.lower()
    if "timeout" in err_lower or "timed out" in err_lower:
        return "Connection timeout. Try again later."
    if "connection" in err_lower or "network" in err_lower or "unreachable" in err_lower:
        return "No connection. Check your network."
    if "rate" in err_lower or "429" in msg or "too many" in err_lower:
        return "Too many requests. Wait a moment and retry."
    if "404" in msg or "not found" in err_lower:
        return "Data not found."
    if len(msg) > 60:
        return default_prefix + ": " + msg[:57] + "..."
    return default_prefix + ": " + msg


def _is_triple_double_row(row):
    def _v(key):
        try:
            val = row.get(key, 0)
            return int(float(val)) if val is not None and str(val) != "nan" else 0
        except (TypeError, ValueError):
            return 0
    pts, reb, ast, stl, blk = _v("PTS"), _v("REB"), _v("AST"), _v("STL"), _v("BLK")
    return sum(1 for x in (pts, reb, ast, stl, blk) if x >= 10) >= 3


def build_quarter_scores(away_team, home_team):
    away_periods = away_team.get("periods") or []
    home_periods = home_team.get("periods") or []
    if not away_periods and not home_periods:
        return None
    by_period = {}
    for p in away_periods:
        num = p.get("period") or 0
        score = p.get("score") or 0
        if num not in by_period:
            by_period[num] = [0, 0]
        by_period[num][0] = score
    for p in home_periods:
        num = p.get("period") or 0
        score = p.get("score") or 0
        if num not in by_period:
            by_period[num] = [0, 0]
        by_period[num][1] = score
    if not by_period:
        return None
    reg = [1, 2, 3, 4]
    ot_periods = sorted(k for k in by_period if k not in reg)
    headers = ["Q1", "Q2", "Q3", "Q4"]
    away_scores = [by_period.get(i, [0, 0])[0] for i in reg]
    home_scores = [by_period.get(i, [0, 0])[1] for i in reg]
    if ot_periods:
        away_ot = sum(by_period.get(k, [0, 0])[0] for k in ot_periods)
        home_ot = sum(by_period.get(k, [0, 0])[1] for k in ot_periods)
        headers.append("OT")
        away_scores.append(away_ot)
        home_scores.append(home_ot)
    away_total = away_team.get("score")
    home_total = home_team.get("score")
    if away_total is None:
        away_total = sum(away_scores)
    if home_total is None:
        home_total = sum(home_scores)
    headers.append("Total")
    away_scores.append(away_total)
    home_scores.append(home_total)
    return {"headers": headers, "away": away_scores, "home": home_scores}


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    reraise=True,
)
def _with_retry(thunk: Callable[[], Any]) -> Any:
    """Execute thunk with retry (tenacity). Used by fetch_games and fetch_standings."""
    return thunk()


class ApiClient:
    def __init__(self):
        self._cache_games = TTLCache(maxsize=128, ttl=constants.CACHE_TTL_GAMES)
        self._cache_standings = TTLCache(maxsize=4, ttl=constants.CACHE_TTL_STANDINGS)
        self._cache_leaders = TTLCache(maxsize=4, ttl=constants.CACHE_TTL_LEAGUE_LEADERS)
        self._cache_box = TTLCache(maxsize=64, ttl=constants.CACHE_TTL_BOX_SCORE)
        self._last_error = None
        self._last_request_time: float = 0
        self._last_games_from_cache = False
        self._last_standings_from_cache = False
        self._last_leaders_from_cache = False

    def any_data_from_cache(self) -> bool:
        """True if any of the last fetch (games, standings, leaders) used offline/cached data."""
        return (
            self._last_games_from_cache
            or self._last_standings_from_cache
            or self._last_leaders_from_cache
        )

    def _rate_limit(self) -> None:
        """Wait for minimum interval between requests (rate limiting)."""
        elapsed = time.time() - self._last_request_time
        if elapsed < constants.RATE_LIMIT_MIN_INTERVAL:
            delay = constants.RATE_LIMIT_MIN_INTERVAL - elapsed
            logger.debug("Rate limit: waiting %.2fs", delay)
            time.sleep(delay)
        self._last_request_time = time.time()

    def get_last_error(self) -> Optional[str]:
        return self._last_error

    def get_initial_data_from_cache_only(
        self, game_date_iso: str
    ) -> Tuple[list, str, Optional[Any], Optional[Any], dict]:
        """
        Load initial data from disk cache only (no network). Use when API is slow or unavailable.
        Returns (games, scoreboard_date, east, west, league_leaders).
        """
        cache_key = f"games:{game_date_iso}"
        games, scoreboard_date = [], game_date_iso
        offline_games = _disk_cache_get_offline(cache_key, constants.CACHE_TTL_OFFLINE)
        if offline_games is not None and isinstance(offline_games, (list, tuple)) and len(offline_games) >= 2:
            games, scoreboard_date = offline_games[0], offline_games[1]

        east, west = None, None
        disk_standings = _disk_cache_get_offline("standings", constants.CACHE_TTL_OFFLINE)
        if disk_standings is not None:
            try:
                east = pd.DataFrame(disk_standings["east"]) if disk_standings.get("east") else None
                west = pd.DataFrame(disk_standings["west"]) if disk_standings.get("west") else None
                if east is not None and east.empty:
                    east = None
                if west is not None and west.empty:
                    west = None
            except Exception:
                pass

        league_leaders = {"PTS": [], "REB": [], "AST": [], "TDBL": []}
        disk_leaders = _disk_cache_get_offline("league_leaders", constants.CACHE_TTL_OFFLINE)
        if disk_leaders is not None and isinstance(disk_leaders, dict):
            for k, v in disk_leaders.items():
                league_leaders[k] = [tuple(x) for x in v] if isinstance(v, list) else v

        return (games, scoreboard_date, east, west, league_leaders)

    def _cache_get(self, cache: Any, key: str) -> Any:
        try:
            return cache[key]
        except KeyError:
            return None

    def _cache_set(self, cache: Any, key: str, value: Any) -> None:
        cache[key] = value

    def fetch_games(self, game_date: Optional[str] = None) -> Tuple[list, str]:
        today = datetime.now().date().isoformat()
        date_str = game_date if game_date else today
        cache_key = f"games:{date_str}"
        cached = self._cache_get(self._cache_games, cache_key)
        if cached is not None:
            return cached

        def _do():
            if game_date is None or date_str == today:
                try:
                    board = scoreboard.ScoreBoard(timeout=constants.REQUEST_TIMEOUT)
                    return board.games.get_dict(), board.score_board_date
                except Exception:
                    pass
            sb = scoreboardv3.ScoreboardV3(game_date=date_str, timeout=constants.REQUEST_TIMEOUT)
            resp = sb.nba_response.get_dict()
            scoreboard_data = resp.get("scoreboard", {})
            games = scoreboard_data.get("games", [])
            scoreboard_date = scoreboard_data.get("gameDate", date_str)
            return games, scoreboard_date

        try:
            self._last_error = None
            self._last_games_from_cache = False
            self._rate_limit()
            result = _with_retry(_do)
            self._cache_set(self._cache_games, cache_key, result)
            _disk_cache_set(cache_key, result)
            return result
        except Exception as e:
            self._last_error = _user_facing_error(e, "Games")
            logger.warning("fetch_games failed: %s", e, exc_info=True)
            offline = _disk_cache_get_offline(cache_key, constants.CACHE_TTL_OFFLINE)
            if offline is not None and isinstance(offline, (list, tuple)) and len(offline) >= 2:
                self._last_games_from_cache = True
                return offline[0], offline[1]
            return [], date_str

    def fetch_standings(self) -> Tuple[Optional[Any], Optional[Any]]:
        disk = _disk_cache_get("standings", constants.CACHE_TTL_STANDINGS)
        if disk is not None:
            try:
                east = pd.DataFrame(disk["east"]) if disk.get("east") else None
                west = pd.DataFrame(disk["west"]) if disk.get("west") else None
                if east is not None and east.empty:
                    east = None
                if west is not None and west.empty:
                    west = None
                return east, west
            except Exception:
                pass
        cached = self._cache_get(self._cache_standings, "standings")
        if cached is not None:
            return cached

        def _do():
            standings = leaguestandingsv3.LeagueStandingsV3(timeout=constants.REQUEST_TIMEOUT)
            df = standings.get_data_frames()[0]
            if df.empty:
                return None, None
            east = df[df["Conference"] == "East"].sort_values("PlayoffRank")
            west = df[df["Conference"] == "West"].sort_values("PlayoffRank")
            return east, west

        try:
            self._last_error = None
            self._last_standings_from_cache = False
            self._rate_limit()
            result = _with_retry(_do)
            self._cache_set(self._cache_standings, "standings", result)
            east, west = result
            _disk_cache_set("standings", {
                "east": east.to_dict(orient="records") if east is not None and not east.empty else [],
                "west": west.to_dict(orient="records") if west is not None and not west.empty else [],
            })
            return result
        except Exception as e:
            self._last_error = _user_facing_error(e, "Standings")
            logger.warning("fetch_standings failed: %s", e, exc_info=True)
            disk = _disk_cache_get_offline("standings", constants.CACHE_TTL_OFFLINE)
            if disk is not None:
                try:
                    east = pd.DataFrame(disk["east"]) if disk.get("east") else None
                    west = pd.DataFrame(disk["west"]) if disk.get("west") else None
                    if east is not None and east.empty:
                        east = None
                    if west is not None and west.empty:
                        west = None
                    if east is not None or west is not None:
                        self._last_standings_from_cache = True
                        return east, west
                except Exception:
                    pass
            return None, None

    def _fetch_triple_double_leaders(self):
        try:
            log = leaguegamelog.LeagueGameLog(
                player_or_team_abbreviation=PlayerOrTeamAbbreviation.player,
                timeout=constants.REQUEST_TIMEOUT,
            )
            df = _with_retry(lambda: log.get_data_frames()[0])
            if df.empty:
                return []
            name_col = next((c for c in ("PLAYER_NAME", "PLAYER", "NAME") if c in df.columns), None)
            team_col = "TEAM_ABBREVIATION" if "TEAM_ABBREVIATION" in df.columns else ("TEAM" if "TEAM" in df.columns else None)
            if name_col is None and "PLAYER_ID" in df.columns:
                name_col = "PLAYER_ID"
            if name_col is None:
                return []
            group_cols = [name_col]
            if team_col:
                group_cols.append(team_col)
            df["_td"] = df.apply(_is_triple_double_row, axis=1)
            td = df[df["_td"]].groupby(group_cols, dropna=False).size().reset_index(name="COUNT")
            td = td.sort_values("COUNT", ascending=False).head(3)
            return [
                (str(row[name_col]), str(row[team_col]) if team_col else "-", int(row["COUNT"]))
                for _, row in td.iterrows()
            ]
        except Exception:
            return []

    def fetch_league_leaders(self):
        disk = _disk_cache_get("league_leaders", constants.CACHE_TTL_LEAGUE_LEADERS)
        if disk is not None:
            try:
                out = {}
                for k, v in disk.items():
                    out[k] = [tuple(x) for x in v] if isinstance(v, list) else v
                return out
            except Exception:
                pass
        cached = self._cache_get(self._cache_leaders, "league_leaders")
        if cached is not None:
            return cached

        try:
            self._last_leaders_from_cache = False
            self._rate_limit()
            result = {"PTS": [], "REB": [], "AST": [], "TDBL": []}
            for stat, col in [
                (StatCategoryAbbreviation.pts, "PTS"),
                (StatCategoryAbbreviation.reb, "REB"),
                (StatCategoryAbbreviation.ast, "AST"),
            ]:
                try:
                    def _do(s=stat, c=col):
                        ldf = leagueleaders.LeagueLeaders(stat_category_abbreviation=s, timeout=constants.REQUEST_TIMEOUT).get_data_frames()[0]
                        return [(p.get("PLAYER", "-"), p.get("TEAM", "-"), p.get(c, 0)) for _, p in ldf.head(3).iterrows()]
                    result[col] = _with_retry(_do)
                except Exception:
                    pass
            try:
                result["TDBL"] = _with_retry(self._fetch_triple_double_leaders)
            except Exception:
                pass
            self._cache_set(self._cache_leaders, "league_leaders", result)
            _disk_cache_set("league_leaders", {k: [list(t) for t in v] for k, v in result.items()})
            return result
        except Exception as e:
            logger.warning("fetch_league_leaders failed: %s", e)
            offline = _disk_cache_get_offline("league_leaders", constants.CACHE_TTL_OFFLINE)
            if offline is not None and isinstance(offline, dict):
                self._last_leaders_from_cache = True
                out = {}
                for k, v in offline.items():
                    out[k] = [tuple(x) for x in v] if isinstance(v, list) else v
                return out
            return {"PTS": [], "REB": [], "AST": [], "TDBL": []}

    def get_box_score(self, game_id: Optional[str]) -> Optional[dict]:
        if not game_id:
            return None
        cache_key = f"box:{game_id}"
        cached = self._cache_get(self._cache_box, cache_key)
        if cached is not None:
            return cached
        try:
            bs = boxscore.BoxScore(game_id, timeout=constants.REQUEST_TIMEOUT)
            game_data = bs.game.get_dict()
            self._cache_set(self._cache_box, cache_key, game_data)
            return game_data
        except Exception:
            return None

    def fetch_team_games(self, team_id: int, limit: int = 10) -> list:
        """Last/recent games for a team (by team_id). Returns list of dicts with GAME_DATE, MATCHUP, WL, PTS, etc."""
        try:
            self._rate_limit()
            log = teamgamelog.TeamGameLog(team_id=team_id, season=Season.default, timeout=constants.REQUEST_TIMEOUT)
            df = log.get_data_frames()[0]
            if df.empty:
                return []
            return df.head(limit).to_dict("records")
        except Exception:
            return []

    def fetch_team_upcoming_games(self, team_tricode: str, days: int = 14, limit: int = 10) -> list:
        """Next/upcoming games for a team (by tricode). Includes today. Returns list of (date_str, game) with date and time."""
        games = []
        today = datetime.now().date()
        tricode_upper = (team_tricode or "").strip().upper()
        for d in range(0, days + 1):
            try:
                self._rate_limit()
                date_str = (today + timedelta(days=d)).isoformat()
                sb = scoreboardv3.ScoreboardV3(game_date=date_str, timeout=constants.REQUEST_TIMEOUT)
                resp = sb.nba_response.get_dict()
                for g in resp.get("scoreboard", {}).get("games", []):
                    away = g.get("awayTeam", {}).get("teamTricode", "")
                    home = g.get("homeTeam", {}).get("teamTricode", "")
                    if tricode_upper in (away, home):
                        games.append((date_str, g))
                        if len(games) >= limit:
                            return games
            except Exception:
                pass
        return games

    def fetch_team_page_info(self, team_id):
        try:
            return teaminfocommon.TeamInfoCommon(team_id=team_id, timeout=constants.REQUEST_TIMEOUT)
        except Exception:
            return None

    def fetch_team_page_leader(self, stat, tricode, col):
        try:
            ldf = leagueleaders.LeagueLeaders(stat_category_abbreviation=stat, timeout=constants.REQUEST_TIMEOUT).get_data_frames()[0]
            team_leaders = ldf[ldf["TEAM"] == tricode].head(3)
            if not team_leaders.empty:
                return (col, [(p.get("PLAYER", "-"), p.get(col, 0)) for _, p in team_leaders.iterrows()])
        except Exception:
            pass
        return (col, [])

    def fetch_team_roster(self, team_id):
        try:
            roster = commonteamroster.CommonTeamRoster(team_id=team_id, timeout=constants.REQUEST_TIMEOUT)
            dfs = roster.get_data_frames()
            if dfs and not dfs[0].empty:
                return dfs[0]
        except Exception:
            pass
        return None

    def fetch_player_info(self, player_id: int):
        """Fetch player profile and headline stats (CommonPlayerInfo). Returns dict with DISPLAY_FIRST_LAST, PTS, REB, AST, etc. or None."""
        try:
            self._rate_limit()
            info = _with_retry(lambda: commonplayerinfo.CommonPlayerInfo(player_id=player_id, timeout=constants.REQUEST_TIMEOUT))
            dfs = info.get_data_frames()
            if not dfs or dfs[0].empty:
                return None
            out = dfs[0].iloc[0].to_dict()
            if len(dfs) > 1 and not dfs[1].empty:
                for k, v in dfs[1].iloc[0].items():
                    if k not in out or out[k] is None:
                        out[k] = v
            return out
        except Exception:
            return None

    def fetch_player_game_log(self, player_id: int, limit: int = 10) -> list:
        """Fetch recent game log for a player. Returns list of dicts with GAME_DATE, MATCHUP, PTS, etc."""
        try:
            self._rate_limit()
            log = _with_retry(
                lambda: playergamelog.PlayerGameLog(
                    player_id=str(player_id),
                    season=Season.default,
                    timeout=constants.REQUEST_TIMEOUT,
                )
            )
            df = log.get_data_frames()[0]
            if df.empty:
                return []
            return df.head(limit).to_dict("records")
        except Exception:
            return []

    def fetch_head_to_head(self, team_id_a: int, team_id_b: int) -> dict:
        """
        Fetch head-to-head between two teams (current season).
        Returns dict with last_meeting (date, matchup, pts_a, pts_b, wl_a) and season_series (wins_a, wins_b, games).
        """
        out = {"last_meeting": None, "season_series": {"wins_a": 0, "wins_b": 0, "games": []}}
        tricode_b = next((t for t, tid in constants.TRICODE_TO_TEAM_ID.items() if tid == team_id_b), None)
        tricode_a = next((t for t, tid in constants.TRICODE_TO_TEAM_ID.items() if tid == team_id_a), None)
        if not tricode_b or not tricode_a:
            return out
        try:
            self._rate_limit()
            log_a = teamgamelog.TeamGameLog(team_id=team_id_a, season=Season.default, timeout=constants.REQUEST_TIMEOUT)
            df_a = _with_retry(lambda: log_a.get_data_frames()[0])
            games_a = []
            for _, row in df_a.iterrows():
                matchup = str(row.get("MATCHUP", ""))
                opp = (matchup.split(" vs. ")[1].strip() if " vs. " in matchup else
                       matchup.split(" @ ")[1].strip() if " @ " in matchup else "")
                if opp == tricode_b:
                    games_a.append({
                        "GAME_DATE": row.get("GAME_DATE"),
                        "MATCHUP": row.get("MATCHUP"),
                        "WL": row.get("WL"),
                        "PTS": row.get("PTS"),
                    })
            if not games_a:
                return out
            games_a.sort(key=lambda g: g.get("GAME_DATE", ""), reverse=True)
            out["season_series"]["games"] = games_a
            out["season_series"]["wins_a"] = sum(1 for g in games_a if g.get("WL") == "W")
            self._rate_limit()
            log_b = teamgamelog.TeamGameLog(team_id=team_id_b, season=Season.default, timeout=constants.REQUEST_TIMEOUT)
            df_b = _with_retry(lambda: log_b.get_data_frames()[0])
            games_b = []
            for _, row in df_b.iterrows():
                matchup = str(row.get("MATCHUP", ""))
                opp = (matchup.split(" vs. ")[1].strip() if " vs. " in matchup else
                       matchup.split(" @ ")[1].strip() if " @ " in matchup else "")
                if opp == tricode_a:
                    games_b.append({"GAME_DATE": row.get("GAME_DATE"), "WL": row.get("WL"), "PTS": row.get("PTS")})
            out["season_series"]["wins_b"] = sum(1 for g in games_b if g.get("WL") == "W")
            g = games_a[0]
            date_last = g.get("GAME_DATE")
            out["last_meeting"] = {
                "date": date_last,
                "matchup": g.get("MATCHUP"),
                "wl_a": g.get("WL"),
                "pts_a": g.get("PTS"),
                "pts_b": None,
            }
            for gb in games_b:
                if gb.get("GAME_DATE") == date_last:
                    out["last_meeting"]["pts_b"] = gb.get("PTS")
                    break
        except Exception:
            pass
        return out
