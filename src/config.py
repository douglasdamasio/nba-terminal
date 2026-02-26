"""App configuration: load/save config.json, i18n (EN/PT), and preference helpers."""
from __future__ import annotations

import json
import os
import sys
from typing import Any, Literal, Optional
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field

__version__ = "1.0.0"
DEVELOPER_NAME = "Douglas Damasio"
DEVELOPER_GITHUB = "github.com/douglasdamasio"

CONFIG_FILENAME = "config.json"


def get_config_dir() -> str:
    """Return config directory for the current OS (Windows: %%APPDATA%%/nba-terminal, Linux/macOS: ~/.config/nba-terminal or $XDG_CONFIG_HOME)."""
    if sys.platform == "win32":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
        return os.path.join(base, "nba-terminal")
    base = os.environ.get("XDG_CONFIG_HOME", os.path.join(os.path.expanduser("~"), ".config"))
    return os.path.join(base, "nba-terminal")


CONFIG_DIR = get_config_dir()


class AppConfig(BaseModel):
    """Validated app configuration model (pydantic). Default values and types are enforced."""

    language: Literal["en", "pt"] = "en"
    refresh_interval_seconds: int = Field(default=30, ge=0, le=300)  # 0 = off
    refresh_mode: Literal["fixed", "auto"] = "fixed"
    favorite_team: str = Field(default="LAL", min_length=2, max_length=5)
    last_game_date: Optional[str] = None
    game_sort: Literal["time", "favorite_first"] = "time"
    timezone: str = Field(default="localtime", min_length=1)
    theme: Literal["default", "high_contrast", "light"] = "default"
    layout_mode: Literal["auto", "compact", "wide"] = "auto"

    model_config = {"extra": "ignore"}


DEFAULT_CONFIG = AppConfig().model_dump(mode="json")

STRINGS = {
    "en": {
        "config_title": " SETTINGS ",
        "language": "Language",
        "refresh": "Refresh interval (seconds)",
        "favorite_team": "Favorite team",
        "developer": "Developer",
        "version": "Version",
        "back": "Back",
        "footer_games": "Games", "footer_teams": "Teams", "footer_lakers": "Lakers", "footer_date": "Go to date",
        "footer_today": "Today", "footer_refresh": "Refresh", "footer_quit": "Quit", "footer_config": "Settings",
        "footer_help": "? Help", "footer_filter": "F Filter",
        "score_by_quarter": " SCORE BY QUARTER ",
        "saved": "Saved.",
        "help_title": " HELP - KEYBOARD SHORTCUTS ",
        "help_press_key": "Press any key to close",
        "help_nav_date": "Previous / next day",
        "help_filter": "Filter: only my team's games",
        "help_help": "Show this help",
        "help_intro": "NBA Terminal shows live scores, standings, and stats. Navigate with the keys below.",
        "help_section_games": " GAMES (main screen) ",
        "help_games_select": " [1-9] [0] [a-j]  Select a game (then Enter for box score)",
        "help_games_nav": " [,] [.] [←] [→]   Previous day / next day",
        "help_games_today": " [D]                 Go to today's games",
        "help_games_date": " [G]                 Go to a specific date",
        "help_games_filter": " [F]                 Filter: show only favorite team's games",
        "help_section_team": " TEAM PAGE ",
        "help_team_scroll": " [U] [D]             Scroll the page up/down",
        "help_team_player": " [↑] [↓]             Select a player in the roster",
        "help_team_enter": " [Enter]             Open selected player's page",
        "help_section_global": " GLOBAL ",
        "help_global_teams": " [T]                 Open teams and standings",
        "help_global_fav": " [L]                 Jump to favorite team's games",
        "help_global_refresh": " [R]                 Refresh data",
        "help_global_config": " [C]                 Settings (language, theme, favorite team)",
        "help_global_help": " [?] [H]             Show this help",
        "help_global_quit": " [Q]                 Quit the application",
        "game_sort": "Game sort",
        "game_sort_time": "Time",
        "game_sort_favorite": "Favorite first",
        "timezone": "Timezone",
        "theme": "Theme",
        "theme_default": "Default",
        "theme_high_contrast": "High contrast",
        "theme_light": "Light",
        "refresh_mode": "Refresh mode",
        "refresh_mode_fixed": "Fixed interval",
        "refresh_mode_auto": "Auto (fast when games live)",
        "layout_mode": "Layout",
        "layout_auto": "Auto (by screen width)",
        "layout_compact": "Compact",
        "layout_wide": "Wide",
        "about_title": " ABOUT ",
        "error_retry": "Failed to load. {err}  [R] Retry",
        "offline_cached": "Offline – data from cache",
        "player_page": " Player page ",
        "player_height": "Height",
        "player_weight": "Weight",
        "player_school": "School",
        "player_country": "Country",
        "player_birthdate": "Birthdate",
        "player_season_stats": " Season stats ",
        "player_recent_games": " Recent games ",
        "head_to_head": " Head-to-head ",
        "last_meeting": "Last meeting",
        "season_series": "Season series",
        "my_team_label": "MY TEAM",
        "header_updating": "Updating…",
        "boxscore_hint_player": " [P] Player page ",
        "boxscore_hint_compare": " [C] Compare ",
        "favorite_playing_now": " Your team is playing now ",
        "favorite_starting_soon": " Your team starts in {mins} min ",
        "team_page_scroll_hint": " [U][D] Scroll ",
        "team_page_footer": " [↑][↓] Player  [U][D] Scroll  [Enter] Player  [Q] Back ",
        "team_roster": " ROSTER ",
        "team_roster_unavailable": "  Roster not available",
    },
    "pt": {
        "config_title": " CONFIGURAÇÃO ",
        "language": "Idioma",
        "refresh": "Intervalo de atualização (segundos)",
        "favorite_team": "Time favorito",
        "developer": "Desenvolvedor",
        "version": "Versão",
        "back": "Voltar",
        "footer_games": "Jogos", "footer_teams": "Times", "footer_lakers": "Lakers", "footer_date": "Ir para data",
        "footer_today": "Hoje", "footer_refresh": "Atualizar", "footer_quit": "Sair", "footer_config": "Config",
        "footer_help": "? Ajuda", "footer_filter": "F Filtro",
        "score_by_quarter": " PLACAR POR QUARTO ",
        "saved": "Salvo.",
        "help_title": " AJUDA - ATALHOS DE TECLADO ",
        "help_press_key": "Pressione qualquer tecla para fechar",
        "help_nav_date": "Dia anterior / próximo",
        "help_filter": "Filtro: só jogos do meu time",
        "help_help": "Mostrar esta ajuda",
        "help_intro": "O NBA Terminal mostra placares ao vivo, tabelas e estatísticas. Use as teclas abaixo.",
        "help_section_games": " JOGOS (tela principal) ",
        "help_games_select": " [1-9] [0] [a-j]  Selecionar jogo (Enter abre o box score)",
        "help_games_nav": " [,] [.] [←] [→]   Dia anterior / próximo",
        "help_games_today": " [D]                 Ir para os jogos de hoje",
        "help_games_date": " [G]                 Ir para uma data específica",
        "help_games_filter": " [F]                 Filtro: só jogos do time favorito",
        "help_section_team": " PÁGINA DO TIME ",
        "help_team_scroll": " [U] [D]             Rolar a página para cima/baixo",
        "help_team_player": " [↑] [↓]             Selecionar jogador no elenco",
        "help_team_enter": " [Enter]             Abrir página do jogador selecionado",
        "help_section_global": " GLOBAL ",
        "help_global_teams": " [T]                 Times e tabela de classificação",
        "help_global_fav": " [L]                 Ir para os jogos do time favorito",
        "help_global_refresh": " [R]                 Atualizar dados",
        "help_global_config": " [C]                 Configurações (idioma, tema, time favorito)",
        "help_global_help": " [?] [H]             Mostrar esta ajuda",
        "help_global_quit": " [Q]                 Sair do aplicativo",
        "game_sort": "Ordenação dos jogos",
        "game_sort_time": "Horário",
        "game_sort_favorite": "Favorito primeiro",
        "timezone": "Fuso horário",
        "theme": "Tema",
        "theme_default": "Padrão",
        "theme_high_contrast": "Alto contraste",
        "theme_light": "Claro",
        "refresh_mode": "Modo de atualização",
        "refresh_mode_fixed": "Intervalo fixo",
        "refresh_mode_auto": "Auto (rápido com jogos ao vivo)",
        "layout_mode": "Layout",
        "layout_auto": "Auto (pela largura)",
        "layout_compact": "Compacto",
        "layout_wide": "Amplo",
        "about_title": " SOBRE ",
        "error_retry": "Falha ao carregar. {err}  [R] Tentar novamente",
        "offline_cached": "Offline – dados em cache",
        "player_page": " Página do jogador ",
        "player_height": "Altura",
        "player_weight": "Peso",
        "player_school": "Universidade",
        "player_country": "País",
        "player_birthdate": "Nascimento",
        "player_season_stats": " Estatísticas da temporada ",
        "player_recent_games": " Jogos recentes ",
        "head_to_head": " Confronto direto ",
        "last_meeting": "Último confronto",
        "season_series": "Série da temporada",
        "my_team_label": "MEU TIME",
        "header_updating": "Atualizando…",
        "boxscore_hint_player": " [P] Página do jogador ",
        "boxscore_hint_compare": " [C] Comparar ",
        "favorite_playing_now": " Seu time está jogando agora ",
        "favorite_starting_soon": " Seu time começa em {mins} min ",
        "team_page_scroll_hint": " [U][D] Rolar ",
        "team_page_footer": " [↑][↓] Jogador  [U][D] Rolar  [Enter] Jogador  [Q] Voltar ",
        "team_roster": " ELENCO ",
        "team_roster_unavailable": "  Elenco não disponível",
    },
}


def get_config_path() -> str:
    return os.path.join(CONFIG_DIR, CONFIG_FILENAME)


def load_config() -> dict[str, Any]:
    """Load config from disk, validate with Pydantic, and return a dict (compatible with the rest of the app)."""
    path = get_config_path()
    if os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            model = AppConfig.model_validate(data)
            return model.model_dump(mode="json")
        except (json.JSONDecodeError, OSError, Exception):
            pass
    os.makedirs(CONFIG_DIR, exist_ok=True)
    cfg = dict(DEFAULT_CONFIG)
    save_config(cfg)
    return cfg


def save_config(config: dict[str, Any]) -> None:
    """Validate config with Pydantic and write to disk (only valid values are persisted)."""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    try:
        model = AppConfig.model_validate(config)
        data = model.model_dump(mode="json")
    except Exception:
        data = config
    with open(get_config_path(), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def get_text(cfg: Optional[dict], key: str) -> str:
    lang = (cfg or {}).get("language", "en")
    return STRINGS.get(lang, STRINGS["en"]).get(key, key)


def favorite_team(cfg: Optional[dict]) -> str:
    return (cfg or {}).get("favorite_team", "LAL")


def refresh_interval(cfg: Optional[dict]) -> int:
    return (cfg or {}).get("refresh_interval_seconds", 30)


def last_game_date(cfg: Optional[dict]) -> Optional[str]:
    """Return the last viewed date (YYYY-MM-DD string) or None."""
    return (cfg or {}).get("last_game_date")


def game_sort(cfg: Optional[dict]) -> str:
    """Return the sort mode: 'time' or 'favorite_first'."""
    return (cfg or {}).get("game_sort", "time")


def timezone(cfg: Optional[dict]) -> str:
    """Return the timezone name (e.g. 'America/Sao_Paulo') or 'localtime' for system default."""
    return (cfg or {}).get("timezone", "localtime")


def theme(cfg: Optional[dict]) -> str:
    """Return the theme: 'default', 'high_contrast', or 'light'."""
    return (cfg or {}).get("theme", "default")


def refresh_mode(cfg: Optional[dict]) -> str:
    """Return the refresh mode: 'fixed' or 'auto'."""
    return (cfg or {}).get("refresh_mode", "fixed")


def layout_mode(cfg: Optional[dict]) -> str:
    """Return the layout mode: 'auto', 'compact', or 'wide'."""
    return (cfg or {}).get("layout_mode", "auto")


def get_tzinfo(cfg: Optional[dict]) -> Optional[ZoneInfo]:
    """Return tzinfo for date formatting. 'localtime' => None (use system)."""
    tz_name = timezone(cfg)
    if not tz_name or tz_name == "localtime":
        return None
    try:
        return ZoneInfo(tz_name)
    except Exception:
        return None
