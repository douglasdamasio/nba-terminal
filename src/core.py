"""Lógica de negócio pura: categorização de jogos, formatação de relógio e rótulos. UI importa daqui."""
from __future__ import annotations

from typing import Any, List, Tuple


def categorize_games(games: List[dict]) -> Tuple[List[dict], List[dict], List[dict]]:
    """
    Separa jogos em: em andamento (tem placar, não final), não iniciados, finalizados.
    Retorna (em_andamento, nao_comecaram, finalizados).
    """
    em_andamento, nao_comecaram, finalizados = [], [], []
    for g in games:
        status = g.get("gameStatusText", "")
        away_score = g.get("awayTeam", {}).get("score", 0)
        home_score = g.get("homeTeam", {}).get("score", 0)
        if status in ("Final", "Final/OT"):
            finalizados.append(g)
        elif away_score or home_score:
            em_andamento.append(g)
        else:
            nao_comecaram.append(g)
    return em_andamento, nao_comecaram, finalizados


def format_live_clock(game: dict) -> str:
    """Formata o relógio do jogo (ex.: Q3 5:30) a partir de gameStatusText, period e gameClock."""
    status = game.get("gameStatusText", "")
    if status and (status.startswith("Q") or ":" in status or "Halftime" in status):
        return status
    period = game.get("period", 0)
    clock = game.get("gameClock", "")
    if clock and period:
        s = str(clock)
        mins = 0
        if "M" in s:
            parts = s.replace("PT", "").replace("S", "").split("M")
            if len(parts) >= 2:
                mins = int(float(parts[0])) if parts[0] else 0
                s = parts[1]
        try:
            secs = int(float(s))
            return f"Q{period} {mins}:{secs:02d}"
        except (ValueError, TypeError):
            pass
    return status or "-"


def game_index_label(i: int) -> str:
    """Rótulo de tecla para o jogo na posição i: [1]..[9], [0], [a]..[j]."""
    if i < 9:
        return f" [{i+1}] "
    if i == 9:
        return " [0] "
    return f" [{chr(ord('a') + i - 10)}] "
