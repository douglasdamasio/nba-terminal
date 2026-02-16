# NBA Terminal App

TUI (Terminal User Interface) para acompanhar jogos da NBA, standings, líderes da temporada e box score direto no terminal.

![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)

## Funcionalidades

- **Dashboard:** jogos do dia (em andamento, não iniciados, finalizados), placar e horário; destaque para o time favorito
- **Standings:** tabelas East e West (playoff e play-in) com cores por time
- **League leaders:** top 3 em pontos, rebotes, assistências e triple-doubles
- **Navegação por data:** teclas `,` / `.` ou setas para mudar o dia; `G` para ir para uma data; `D` para hoje. A última data visualizada é guardada e restaurada ao reabrir o app
- **Box score:** teclas `1`–`9`, `0`, `a`–`j` para abrir estatísticas do jogo
- **Página do time:** `T` para escolher time; `L` para ir ao time favorito (resumo, líderes, próximos/últimos jogos, roster)
- **Configuração (C):** idioma (EN/PT), intervalo de atualização (10/15/30/60/120 s ou off), modo de atualização (fixo ou auto), time favorito, ordenação dos jogos e tema (padrão, alto contraste, claro); dados salvos em `~/.config/nba-terminal/`
- **Filtro e ordenação:** `F` para filtrar só jogos do time favorito; ordenação por horário ou “time favorito primeiro”
- **Ajuda:** `?` ou `H` para ver todos os atalhos
- **Erro de rede:** em falha de carregamento o header mostra mensagem curta e "[R] Tentar novamente"
- **Cache em disco:** standings e league leaders são cacheados em `~/.config/nba-terminal/cache/` (TTL 1h) para reduzir chamadas à API

## Requisitos

- Python 3.9 ou superior
- Terminal com suporte a cores (recomendado)

**Variável de ambiente:** `NBA_DEBUG=1` para ativar logging em nível DEBUG (diagnóstico de falhas de API).

## Instalação

```bash
git clone https://github.com/douglasdamasio/nba-terminal.git
cd nba-terminal
pip install -r requirements.txt
```

## Uso

**Modo TUI (interativo):**

```bash
python -m src.main
# ou, se src estiver no PYTHONPATH:
python src/main.py
```

**Modo CLI (saída em texto e sai):** Use `python -m src.main --help` para ver todas as opções.

```bash
python -m src.main -t          # jogos de hoje
python -m src.main -s          # standings (East/West)
python -m src.main -l          # últimos resultados (último dia com jogos)
python -m src.main --export-games json     # jogos de hoje em JSON
python -m src.main --export-games csv      # jogos de hoje em CSV
python -m src.main --export-standings json # standings em JSON
python -m src.main --export-standings csv  # standings em CSV
```

## Atalhos (modo TUI)

| Tecla | Ação |
|-------|------|
| `1`–`9`, `0`, `a`–`j` | Abrir box score do jogo |
| `T` | Times (escolher e ver página do time) |
| `L` | Ir ao time favorito |
| `G` | Ir para data |
| `,` / `[` / ← | Dia anterior |
| `.` / `]` / → | Próximo dia |
| `D` | Voltar para hoje |
| `R` | Atualizar dados |
| `C` | Configurações |
| `F` | Filtrar só jogos do meu time (liga/desliga) |
| `?` / `H` | Ajuda (lista de atalhos) |
| `Q` | Sair |

## Configuração

O arquivo fica em `~/.config/nba-terminal/config.json`. Campos:

- `language`: `"en"` ou `"pt"`
- `refresh_interval_seconds`: 15, 30 ou 60
- `favorite_team`: tricode (ex.: `"LAL"`, `"BOS"`)
- `last_game_date`: última data visualizada (opcional, ex.: `"2025-02-16"`)
- `game_sort`: `"time"` (horário) ou `"favorite_first"` (time favorito primeiro). Também alterável na tela Config (C)
- `refresh_mode`: `"fixed"` ou `"auto"` (auto = 30 s com jogos ao vivo, 120 s sem)
- `timezone`: `"localtime"`, `"America/Sao_Paulo"`, `"America/New_York"`, `"Europe/London"` (horários na interface)
- `theme`: `"default"`, `"high_contrast"` ou `"light"` (claro)

## Estrutura do projeto

```
nba/
├── src/
│   ├── main.py         # Entrada, loop principal, CLI (typer)
│   ├── config.py      # Configuração e i18n (pydantic AppConfig)
│   ├── api.py         # Cliente NBA API, cache, retry (tenacity), rate limit
│   ├── core.py        # Lógica pura: categorize_games, format_live_clock, game_index_label
│   ├── key_handlers.py # Mapeamento tecla → ação (quit, refresh, game:N, etc.)
│   ├── constants.py   # Times, cores, estatísticas, REFRESH_INTERVAL_CHOICES
│   └── ui/
│       ├── dashboard.py  # Dashboard, jogos e standings
│       ├── screens.py    # Config, data, favorito
│       ├── help.py       # Tela de ajuda
│       ├── teams.py      # Lista de times e página do time
│       ├── boxscore.py   # Box score do jogo
│       ├── colors.py     # Cores por time
│       └── helpers.py    # Helpers de UI
├── docs/
│   └── MELHORIAS.md  # Backlog de melhorias
├── tests/
├── requirements.txt
├── CHANGELOG.md
└── README.md
```

## Dependências

- [nba_api](https://github.com/swar/nba_api) – dados da NBA
- [python-dateutil](https://dateutil.readthedocs.io/) – parsing de datas
- [tenacity](https://tenacity.readthedocs.io/) – retry com backoff em chamadas de API
- [cachetools](https://cachetools.readthedocs.io/) – cache em memória com TTL
- [pydantic](https://docs.pydantic.dev/) – validação da configuração (`AppConfig`)
- [typer](https://typer.tiangolo.com/) – CLI com opções tipadas e ajuda (`-t`, `-s`, `-l`, `--export-games`, `--export-standings`)

## Changelog e melhorias

- [CHANGELOG.md](CHANGELOG.md) – histórico de versões
- [docs/MELHORIAS.md](docs/MELHORIAS.md) – backlog de melhorias (implementadas e planejadas)

## Licença

Uso pessoal / educacional. Dados da NBA via nba_api (ver termos de uso da API).

## Autor

Douglas Damasio – [github.com/douglasdamasio](https://github.com/douglasdamasio)
