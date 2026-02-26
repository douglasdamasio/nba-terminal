# NBA Terminal App

TUI (Terminal User Interface) to follow NBA games, standings, season leaders, and box scores right in the terminal.

![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)

**Plataforma:** suporte a **macOS, Linux e Windows**. Config e cache usam diretórios padrão por OS (veja [Configuration](#configuration)).

## Features

- **Dashboard:** Today's games (in progress, not started, final) with score and time; highlight for favorite team
- **Standings:** East and West tables (playoff and play-in) with team colors
- **League leaders:** Top 3 in points, rebounds, assists, and triple-doubles
- **Date navigation:** Keys `,` / `.` or arrow keys to change day; `G` to go to a date; `D` for today. Last viewed date is saved and restored when reopening the app
- **Box score:** Keys `1`–`9`, `0`, `a`–`j` to open game statistics; **[P] Player page** when a player is selected (season stats, recent games); **head-to-head** (last meeting and season series) shown at top
- **Team page:** `T` to choose team; `L` to go to favorite team (summary, leaders, **head-to-head vs next opponent**, upcoming/last games, roster)
- **Settings (C):** Language (EN/PT), refresh interval (10/15/30/60/120 s or off), refresh mode (fixed or auto), favorite team, game order, theme (default, high contrast, light), and **layout** (auto, compact, wide); data saved in the [config directory](#configuration) for your OS
- **Filter and sort:** `F` to filter only your team's games; sort by time or “favorite first”
- **Help:** `?` or `H` to see all shortcuts
- **Network error:** On load failure the header shows a short message and “[R] Retry”
- **Offline / cache:** Games, standings and league leaders are cached on disk. When the network fails, the app uses cached data (up to 24h) and shows **"Offline – data from cache"** in the header so you can keep browsing
- **Disk cache:** Config and cache under the same base directory: `cache/` for standings, leaders and games (1h TTL for fresh data; 24h for offline fallback)

## Requirements

- Python 3.9 or higher
- Terminal with color support (recommended)

**Environment variable:** `NBA_DEBUG=1` to enable DEBUG-level logging (API failure diagnosis).

## Installation

**From source:**

```bash
git clone https://github.com/douglasdamasio/nba-terminal.git
cd nba-terminal
pip install -r requirements.txt
```

**With Homebrew (macOS):**

```bash
brew tap douglasdamasio/nba-terminal
brew install nba-terminal
```

See [docs/HOMEBREW.md](docs/HOMEBREW.md) for publishing or maintaining the Homebrew formula.

## Usage

**TUI mode (interactive):**

```bash
python -m src.main
# or, if src is on PYTHONPATH:
python src/main.py
```

**CLI mode (text output and exit):** Run `python -m src.main --help` to see all options.

```bash
python -m src.main -t          # today's games
python -m src.main -s          # standings (East/West)
python -m src.main -l          # last results (most recent day with games)
python -m src.main --export-games json     # today's games as JSON
python -m src.main --export-games csv     # today's games as CSV
python -m src.main --export-standings json # standings as JSON
python -m src.main --export-standings csv  # standings as CSV
```

## Shortcuts (TUI mode)

| Key | Action |
|-----|--------|
| `1`–`9`, `0`, `a`–`j` | Open game box score |
| `T` | Teams (pick and view team page) |
| `L` | Go to favorite team |
| `G` | Go to date |
| `,` / `[` / ← | Previous day |
| `.` / `]` / → | Next day |
| `D` | Back to today |
| `R` | Refresh data |
| `C` | Settings |
| `F` | Filter only my team's games (toggle) |
| `?` / `H` | Help (shortcut list) |
| `Q` | Quit |

In **box score**: [A]/[H]/[B] switch team view, [1]/[2] team page, [↑][↓] select player, [Enter] game stats, **[P] player page** (season + recent games), [Q] back.

## Configuration

**Config directory (by OS):**
- **Windows:** `%APPDATA%\\nba-terminal\\` (e.g. `C:\\Users\\You\\AppData\\Roaming\\nba-terminal\\`)
- **Linux / macOS:** `~/.config/nba-terminal/` (or `$XDG_CONFIG_HOME/nba-terminal/` if set)

Config file: `config.json` inside that directory. Fields:

- `language`: `"en"` or `"pt"`
- `refresh_interval_seconds`: 10, 15, 30, 60, 120, or 0 (off)
- `favorite_team`: tricode (e.g. `"LAL"`, `"BOS"`)
- `last_game_date`: last viewed date (optional, e.g. `"2025-02-16"`)
- `game_sort`: `"time"` (by time) or `"favorite_first"`. Also changeable in Settings (C)
- `refresh_mode`: `"fixed"` or `"auto"` (auto = 30 s when games live, 120 s otherwise)
- `timezone`: `"localtime"`, `"America/Sao_Paulo"`, `"America/New_York"`, `"Europe/London"` (for display times)
- `theme`: `"default"`, `"high_contrast"`, or `"light"`
- `layout_mode`: `"auto"` (by screen width), `"compact"`, or `"wide"`

## Project structure

```
nba/
├── src/
│   ├── main.py         # Entry point, main loop, CLI (typer)
│   ├── config.py       # Config and i18n (pydantic AppConfig)
│   ├── api.py          # NBA API client, cache, retry (tenacity), rate limit
│   ├── core.py         # Pure logic: categorize_games, format_live_clock, game_index_label
│   ├── key_handlers.py # Key → action mapping (quit, refresh, game:N, etc.)
│   ├── constants.py    # Teams, colors, stats, REFRESH_INTERVAL_CHOICES
│   └── ui/
│       ├── dashboard.py  # Dashboard, games and standings
│       ├── screens.py    # Config, date, favorite
│       ├── help.py       # Help screen
│       ├── teams.py      # Team list and team page
│       ├── boxscore.py   # Game box score
│       ├── colors.py     # Team colors
│       └── helpers.py    # UI helpers
├── tests/
├── requirements.txt
├── CHANGELOG.md
└── README.md
```

## Dependencies

- [nba_api](https://github.com/swar/nba_api) – NBA data
- [python-dateutil](https://dateutil.readthedocs.io/) – date parsing
- [tenacity](https://tenacity.readthedocs.io/) – retry with backoff for API calls
- [cachetools](https://cachetools.readthedocs.io/) – in-memory cache with TTL
- [pydantic](https://docs.pydantic.dev/) – config validation (`AppConfig`)
- [typer](https://typer.tiangolo.com/) – CLI with typed options and help (`-t`, `-s`, `-l`, `--export-games`, `--export-standings`)

## Changelog and improvements

- [CHANGELOG.md](CHANGELOG.md) – version history
- [docs/MELHORIAS.md](docs/MELHORIAS.md) – improvement backlog (done and planned)

## License

This project is distributed under the **MIT License**. See the [LICENSE](LICENSE) file for the full text.

NBA data is provided via [nba_api](https://github.com/swar/nba_api); see the API terms of use for data usage.

## Author

Douglas Damasio – [github.com/douglasdamasio](https://github.com/douglasdamasio)
