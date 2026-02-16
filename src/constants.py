"""Constantes: mapeamento de times (tricode, nome, cores), estatísticas e fun facts."""
TEAM_TO_TRICODE = {
    "Atlanta Hawks": "ATL", "Boston Celtics": "BOS", "Brooklyn Nets": "BKN",
    "Charlotte Hornets": "CHA", "Chicago Bulls": "CHI", "Cleveland Cavaliers": "CLE",
    "Dallas Mavericks": "DAL", "Denver Nuggets": "DEN", "Detroit Pistons": "DET",
    "Golden State Warriors": "GSW", "Houston Rockets": "HOU", "Indiana Pacers": "IND",
    "LA Clippers": "LAC", "Los Angeles Clippers": "LAC", "Los Angeles Lakers": "LAL",
    "LA Lakers": "LAL", "Memphis Grizzlies": "MEM",
    "Miami Heat": "MIA", "Milwaukee Bucks": "MIL", "Minnesota Timberwolves": "MIN",
    "New Orleans Pelicans": "NOP", "New York Knicks": "NYK", "Oklahoma City Thunder": "OKC",
    "Orlando Magic": "ORL", "Philadelphia 76ers": "PHI", "Phoenix Suns": "PHX",
    "Portland Trail Blazers": "POR", "Sacramento Kings": "SAC", "San Antonio Spurs": "SAS",
    "Toronto Raptors": "TOR", "Utah Jazz": "UTA", "Washington Wizards": "WAS",
}

TRICODE_TO_TEAM_NAME = {v: k for k, v in TEAM_TO_TRICODE.items()}

TEAM_COLORS_RGB = {
    "ATL": (224, 58, 62), "BOS": (0, 122, 51), "BKN": (128, 128, 128),
    "CHA": (29, 17, 96), "CHI": (206, 17, 65), "CLE": (134, 0, 56),
    "DAL": (0, 83, 140), "DEN": (14, 34, 64), "DET": (200, 16, 46),
    "GSW": (29, 66, 138), "HOU": (206, 17, 65), "IND": (0, 45, 98),
    "LAC": (200, 16, 46), "LAL": (253, 185, 39), "MEM": (93, 118, 169),
    "MIA": (152, 0, 46), "MIL": (0, 71, 27), "MIN": (12, 35, 64),
    "NOP": (0, 22, 65), "NYK": (0, 107, 182), "OKC": (0, 122, 193),
    "ORL": (0, 119, 192), "PHI": (0, 107, 182), "PHX": (29, 17, 96),
    "POR": (224, 58, 62), "SAC": (91, 43, 129), "SAS": (196, 206, 212),
    "TOR": (206, 17, 65), "UTA": (0, 43, 92), "WAS": (0, 43, 92),
}

TRICODE_TO_BASIC_COLOR_NAMES = {
    "ATL": "COLOR_RED", "BOS": "COLOR_GREEN", "BKN": "COLOR_WHITE",
    "CHA": "COLOR_MAGENTA", "CHI": "COLOR_RED", "CLE": "COLOR_MAGENTA",
    "DAL": "COLOR_BLUE", "DEN": "COLOR_BLUE", "DET": "COLOR_RED",
    "GSW": "COLOR_BLUE", "HOU": "COLOR_RED", "IND": "COLOR_BLUE",
    "LAC": "COLOR_RED", "LAL": "COLOR_YELLOW", "MEM": "COLOR_CYAN",
    "MIA": "COLOR_RED", "MIL": "COLOR_GREEN", "MIN": "COLOR_BLUE",
    "NOP": "COLOR_BLUE", "NYK": "COLOR_BLUE", "OKC": "COLOR_CYAN",
    "ORL": "COLOR_CYAN", "PHI": "COLOR_BLUE", "PHX": "COLOR_MAGENTA",
    "POR": "COLOR_RED", "SAC": "COLOR_MAGENTA", "SAS": "COLOR_WHITE",
    "TOR": "COLOR_RED", "UTA": "COLOR_BLUE", "WAS": "COLOR_BLUE",
}

TRICODE_TO_TEAM_ID = {
    "ATL": 1610612737, "BOS": 1610612738, "BKN": 1610612751, "CHA": 1610612766,
    "CHI": 1610612741, "CLE": 1610612739, "DAL": 1610612742, "DEN": 1610612743,
    "DET": 1610612765, "GSW": 1610612744, "HOU": 1610612745, "IND": 1610612754,
    "LAC": 1610612746, "LAL": 1610612747, "MEM": 1610612763, "MIA": 1610612748,
    "MIL": 1610612749, "MIN": 1610612750, "NOP": 1610612740, "NYK": 1610612752,
    "OKC": 1610612760, "ORL": 1610612753, "PHI": 1610612755, "PHX": 1610612756,
    "POR": 1610612757, "SAC": 1610612758, "SAS": 1610612759, "TOR": 1610612761,
    "UTA": 1610612762, "WAS": 1610612764,
}

TEAM_FUN_FACTS = {
    "LAL": "17 NBA titles. 33-game win streak in 1971-72. Showtime in the 80s.",
    "BOS": "18 titles (record). Bill Russell dynasty: 11 in 13 years.",
    "GSW": "7 titles. Stephen Curry revolutionized the 3-point game.",
    "CHI": "6 titles in the Michael Jordan era (1991-1998).",
    "SAS": "5 titles. Tim Duncan, Tony Parker, Manu Ginobili.",
    "MIA": "3 titles. Big Three: LeBron, Wade, Bosh (2010-2014).",
    "NYK": "2 titles. Madison Square Garden - basketball's Mecca.",
    "BKN": "Founded in New Jersey (1967). Moved to Brooklyn in 2012.",
    "CLE": "1 title (2016). LeBron brings the title to Cleveland.",
    "MIL": "2 titles. Giannis MVP and the 'Greek Freak'.",
    "PHX": "Never won. Charles Barkley came close in 1993.",
    "DAL": "1 title (2011). Dirk Nowitzki Finals MVP.",
    "DEN": "1 title (2023). Nikola Jokić brought the title to the mountains.",
    "OKC": "Former Seattle SuperSonics. Kevin Durant, Russell Westbrook.",
    "POR": "1 title (1977). Bill Walton MVP.",
    "SAC": "1 title (1951). City of the King.",
    "UTA": "Karl Malone and John Stockton - legendary duo, no title.",
    "MEM": "Grit and Grind - defensive style of the 2010s.",
    "NOP": "Anthony Davis, Zion Williamson. Pelicans since 2013.",
    "HOU": "2 titles (1994, 1995). Hakeem Olajuwon.",
    "ATL": "Dominant in the 50s with Bob Pettit.",
    "CHA": "Michael Jordan has owned the team since 2010.",
    "ORL": "Shaquille O'Neal and Penny Hardaway in the 90s.",
    "WAS": "Former Bullets. Capital of basketball.",
    "IND": "Reggie Miller - legend from beyond the arc.",
    "DET": "Bad Boys (1989, 1990), Goin' to Work (2004).",
    "PHI": "Wilt Chamberlain 100 points in a game (1962).",
    "TOR": "Only Canadian team. 1 title (2019) with Kawhi.",
    "MIN": "Kevin Garnett MVP in 2004.",
    "LAC": "Always in the Lakers' shadow. Paul George and Kawhi.",
}

STAT_NAMES = {
    "points": "PTS", "fieldGoalsMade": "FGM", "fieldGoalsAttempted": "FGA",
    "fieldGoalsPercentage": "FG%", "threePointersMade": "3PM",
    "threePointersAttempted": "3PA", "threePointersPercentage": "3P%",
    "freeThrowsMade": "FTM", "freeThrowsAttempted": "FTA",
    "freeThrowsPercentage": "FT%", "reboundsOffensive": "OREB",
    "reboundsDefensive": "DREB", "reboundsTotal": "REB", "assists": "AST",
    "steals": "STL", "blocks": "BLK", "turnovers": "TO",
    "foulsPersonal": "PF", "plusMinusPoints": "+/-",
}

BOX_SCORE_STAT_KEYS = [
    "points", "fieldGoalsMade", "fieldGoalsAttempted", "fieldGoalsPercentage",
    "threePointersMade", "threePointersAttempted", "threePointersPercentage",
    "freeThrowsMade", "freeThrowsAttempted", "freeThrowsPercentage",
    "reboundsOffensive", "reboundsDefensive", "reboundsTotal",
    "assists", "steals", "blocks", "turnovers", "foulsPersonal", "plusMinusPoints",
]

LEADER_CATEGORIES = [("TOP 3 SCORERS", "PTS"), ("TOP 3 REBOUNDS", "REB"), ("TOP 3 ASSISTS", "AST")]

# Opções de intervalo de refresh (segundos); 0 = desligado
REFRESH_INTERVAL_CHOICES = [10, 15, 30, 60, 120, 0]

# API / cache (usado em api.py)
CACHE_TTL_STANDINGS = 3600
CACHE_TTL_GAMES = 90
CACHE_TTL_LEAGUE_LEADERS = 3600
CACHE_TTL_BOX_SCORE = 300
RETRY_MAX_ATTEMPTS = 3
RETRY_BASE_DELAY = 1
# Mínimo de segundos entre requisições à API (rate limiting suave)
RATE_LIMIT_MIN_INTERVAL = 0.6

# Splash / mensagens de carregamento (usado em main.py)
SPLASH_STARTING = "Starting..."
SPLASH_LOADING_GAMES = "Loading games..."
SPLASH_LOADING_STANDINGS = "Loading standings..."
SPLASH_LOADING_LEADERS = "Loading league leaders..."
SPLASH_PLEASE_WAIT = " Please wait... "


def get_tricode_from_team(team_full):
    for name, tricode in TEAM_TO_TRICODE.items():
        if name in team_full or (team_full or "").strip() == name:
            return tricode
    return ""


def is_triple_double(stats):
    if not stats:
        return False
    vals = [
        stats.get("points") or 0,
        stats.get("reboundsTotal") or 0,
        stats.get("assists") or 0,
        stats.get("steals") or 0,
        stats.get("blocks") or 0,
    ]
    return sum(1 for v in vals if v >= 10) >= 3
