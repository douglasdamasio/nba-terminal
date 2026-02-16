"""Configuração do app: carregar/salvar config.json, i18n (EN/PT) e helpers de preferências."""
from __future__ import annotations

import json
import os
from typing import Any, Literal, Optional
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field

__version__ = "1.0.0"
DEVELOPER_NAME = "Douglas Damasio"
DEVELOPER_GITHUB = "github.com/douglasdamasio"

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config", "nba-terminal")
CONFIG_FILENAME = "config.json"


class AppConfig(BaseModel):
    """Modelo validado da configuração do app (pydantic). Valores padrão e tipos garantidos."""

    language: Literal["en", "pt"] = "en"
    refresh_interval_seconds: int = Field(default=30, ge=0, le=300)  # 0 = off
    refresh_mode: Literal["fixed", "auto"] = "fixed"
    favorite_team: str = Field(default="LAL", min_length=2, max_length=5)
    last_game_date: Optional[str] = None
    game_sort: Literal["time", "favorite_first"] = "time"
    timezone: str = Field(default="localtime", min_length=1)
    theme: Literal["default", "high_contrast", "light"] = "default"

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
        "about_title": " ABOUT ",
        "error_retry": "Failed to load. {err}  [R] Retry",
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
        "about_title": " SOBRE ",
        "error_retry": "Falha ao carregar. {err}  [R] Tentar novamente",
    },
}


def get_config_path() -> str:
    return os.path.join(CONFIG_DIR, CONFIG_FILENAME)


def load_config() -> dict[str, Any]:
    """Carrega config do disco, valida com Pydantic e retorna dict (compatível com o resto do app)."""
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
    """Valida config com Pydantic e grava no disco (só valores válidos são persistidos)."""
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
    """Retorna a última data visualizada (string YYYY-MM-DD) ou None."""
    return (cfg or {}).get("last_game_date")


def game_sort(cfg: Optional[dict]) -> str:
    """Retorna o modo de ordenação: 'time' ou 'favorite_first'."""
    return (cfg or {}).get("game_sort", "time")


def timezone(cfg: Optional[dict]) -> str:
    """Retorna o nome do timezone (ex.: 'America/Sao_Paulo') ou 'localtime' para o do sistema."""
    return (cfg or {}).get("timezone", "localtime")


def theme(cfg: Optional[dict]) -> str:
    """Retorna o tema: 'default', 'high_contrast' ou 'light'."""
    return (cfg or {}).get("theme", "default")


def refresh_mode(cfg: Optional[dict]) -> str:
    """Retorna o modo de refresh: 'fixed' ou 'auto'."""
    return (cfg or {}).get("refresh_mode", "fixed")


def get_tzinfo(cfg: Optional[dict]) -> Optional[ZoneInfo]:
    """Retorna tzinfo para formatação de datas. 'localtime' => None (usa sistema)."""
    tz_name = timezone(cfg)
    if not tz_name or tz_name == "localtime":
        return None
    try:
        return ZoneInfo(tz_name)
    except Exception:
        return None
