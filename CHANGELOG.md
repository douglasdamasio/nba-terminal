# Changelog

All notable changes to the NBA Terminal App are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added (implemented from backlog)

- **Tela de ajuda:** atalhos `?` e `H` abrem tela com lista de teclas; footer inclui `?` Help e `F` Filter.
- **Persistir data:** última data visualizada salva em config (`last_game_date`); ao reabrir o app, jogos dessa data são carregados.
- **Filtro “só meu time”:** tecla `F` alterna filtro para mostrar apenas jogos em que o time favorito joga; footer indica quando o filtro está ativo (`F Filter *`).
- **Ordenação configurável:** em Config (C), opção “Game sort” (Time / Favorite first); jogos podem ser ordenados por horário ou com time favorito primeiro.
- **Docstrings e README:** docstring no topo de cada módulo em `src/`; README com funcionalidades, instalação, uso, atalhos e estrutura do projeto.

### Planned (see [docs/MELHORIAS.md](docs/MELHORIAS.md))

- Tela de ajuda (atalhos)
- Persistir data selecionada
- Filtro "só jogos do meu time"
- Ordenação configurável de jogos
- Docstrings e documentação de módulos
- Constantes e eliminação de magic numbers
- Logging
- Timezone configurável
- Modo acessibilidade (alto contraste)
- Export JSON/CSV via CLI
- Tratamento de erros e feedback ao usuário
- Simplificar código com bibliotecas (tenacity, cachetools, pydantic, typer, etc.)
- Type hints no projeto
- Refatorar key handling (main loop)
- Cache em disco
- Refresh flexível / modo auto
- Testes automatizados ampliados
- Temas / esquemas de cores configuráveis
- API rate limiting e backoff
- Separar lógica de negócio da UI
- Injeção de dependências e testabilidade
- Play-by-play / última jogada no box score
- Notificações / alertas (time favorito ou jogo próximo do fim)

### Added (implemented from backlog – segunda leva)

- **Constantes e magic numbers (1.6):** TTLs de cache, retries e mensagens de splash em `constants.py`; `api.py` e `main.py` usam essas constantes.
- **Logging (1.7):** `logging_config.py` com nível por variável de ambiente `NBA_DEBUG` (DEBUG) ou WARNING; log de falhas em `api.py` (fetch_games, fetch_standings).
- **Timezone configurável (1.8):** Opção em Config (C) para Timezone (Local, America/Sao_Paulo, America/New_York, Europe/London). Horários de jogo e “Updated at” usam `zoneinfo`.
- **Modo alto contraste (1.9):** Opção em Config (C) para Tema (Padrão / Alto contraste). Em alto contraste, cores por time desativadas (apenas bold/reverse).
- **Export JSON/CSV via CLI (1.10):** Flags `--export-games json|csv` e `--export-standings json|csv` para imprimir jogos ou standings em formato estruturado (pipe ou arquivo).

### Added (implemented from backlog – terceira leva, nível médio)

- **Tratamento de erros e feedback (2.1):** Mensagens amigáveis em falhas de API (timeout, rede, rate limit) via `_user_facing_error`; header do dashboard mostra erro e "[R] Tentar novamente" (i18n `error_retry`).
- **Bibliotecas externas (2.2):** Retry com tenacity; cache em memória com cachetools (TTLCache); dateutil em `parse_date_string` em `ui/screens.py`. Dependências em `requirements.txt`.
- **Type hints (2.3):** Anotações em `config.py`, `api.py`, `main.py`, `key_handlers.py` e em funções principais (parse_date_string, get_action, fetch_games, fetch_standings, etc.).
- **Key handlers (2.4):** Módulo `src/key_handlers.py` com `get_action(key, game_count)` retornando ações (quit, refresh, config, help, filter, teams, date, today, prev_day, next_day, favorite_team, game:N); loop em `main.py` refatorado para switch por ação.
- **Cache em disco (2.5):** Standings e league leaders persistidos em `~/.config/nba-terminal/cache/` (JSON com timestamp e TTL); leitura antes da API e gravação após sucesso.

### Added (melhorias nível médio – 2.6 a 2.11)

- **Refresh flexível / modo auto (2.6):** Opções de intervalo 10, 15, 30, 60, 120 s e "off" (0); modo "auto" (30 s quando há jogos ao vivo, 120 s caso contrário). Config: novo campo `refresh_mode` e ciclo de intervalos na tela.
- **Testes ampliados (2.7):** Testes em `tests/test_pure.py` importam de `core` e `api`; adicionada classe `TestBuildQuarterScores` para `api.build_quarter_scores`.
- **Temas (2.8):** Tema **light** em Config e `ui/colors.py` (preto/branco); ciclo default → high_contrast → light.
- **Rate limiting (2.9):** `ApiClient._rate_limit()` com intervalo mínimo 0,6 s entre requisições; log em DEBUG.
- **Core / lógica separada (2.10):** Novo `src/core.py` com `categorize_games`, `format_live_clock`, `game_index_label`; dashboard e main importam de core.
- **Injeção de dependências (2.11):** Documentado como atendido (telas recebem cfg, api_client, color_ctx por parâmetro).

### Added (bibliotecas externas – pydantic e typer)

- **Pydantic (config):** Modelo `AppConfig` em `config.py` com validação e defaults (language, refresh_interval_seconds, favorite_team, game_sort, theme, etc.). `load_config()` valida com `AppConfig.model_validate()` e retorna dict; `save_config()` valida antes de gravar.
- **Typer (CLI):** Substituição de `argparse` por **typer** em `main.py`. Opções `-t`, `-s`, `-l`, `--export-games`, `--export-standings` com ajuda em português; validação de `json`/`csv` nos exports; sem argumentos abre o modo TUI.

---

## [1.0.0] – 2025-02

### Added

- **Dashboard (TUI):** jogos do dia com status (em andamento, não iniciados, finalizados), placar e horário; destaque para time favorito (*MY TEAM*).
- **Standings:** tabelas East e West (1–6 playoff, 7–10 play-in) com cores por time.
- **League leaders:** top 3 em pontos, rebotes, assistências e triple-doubles na temporada.
- **Navegação por data:** teclas `,` / `.` (ou `[` / `]`) e setas para dia anterior/próximo; `G` para ir para data; `D` para voltar a hoje.
- **Box score:** teclas `1`–`9`, `0`, `a`–`j` para abrir estatísticas do jogo (placar por quarto, estatísticas de time e jogadores).
- **Página do time:** `T` para escolher time, `L` para ir ao time favorito; resumo da temporada, líderes (PTS/REB/AST), próximos e últimos jogos, roster e fun fact.
- **Configuração:** tela `C` com idioma (EN/PT), intervalo de atualização (15/30/60 s) e time favorito. Config salvo em `~/.config/nba-terminal/config.json`.
- **Atualização automática:** refresh periódico quando há jogos em andamento (intervalo configurável).
- **CLI:** flags `-t` (today games), `-s` (standings), `-l` (last results) para saída em texto e sair.
- **Cores:** suporte a cores por time (true color quando o terminal permite, fallback para cores básicas).
- **i18n:** strings em inglês e português para configuração e footer.

### Technical

- Uso de `nba_api` (live scoreboard, box score, standings, league leaders, team game log, roster).
- Cache em memória com TTL para jogos, standings, league leaders e box score.
- Retry com backoff exponencial em chamadas de API.
- Interface baseada em `curses`.

---

[Unreleased]: https://github.com/douglasdamasio/nba-terminal/compare/v1.0.0...HEAD  
[1.0.0]: https://github.com/douglasdamasio/nba-terminal/releases/tag/v1.0.0
