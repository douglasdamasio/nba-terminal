"""Cores por time: pares curses (true color ou fallback básico) para destaque no dashboard."""
import curses

import constants

TRICODE_TO_BASIC_COLOR = {
    k: getattr(curses, v) for k, v in constants.TRICODE_TO_BASIC_COLOR_NAMES.items()
}


class ColorContext:
    def __init__(self, theme="default"):
        self._pair_mode = None
        self._theme = theme if theme in ("default", "high_contrast", "light") else "default"

    def set_theme(self, theme):
        self._theme = theme if theme in ("default", "high_contrast", "light") else "default"

    def init_pairs(self):
        if self._theme == "light":
            self._pair_mode = "light"
            try:
                curses.init_pair(1, curses.COLOR_BLACK, -1)
                curses.init_pair(31, curses.COLOR_BLACK, curses.COLOR_WHITE)
                curses.init_pair(39, curses.COLOR_WHITE, curses.COLOR_BLACK)
            except curses.error:
                pass
            return
        if self._theme == "high_contrast":
            self._pair_mode = "high_contrast"
            try:
                curses.init_pair(1, curses.COLOR_WHITE, -1)
                curses.init_pair(31, curses.COLOR_WHITE, curses.COLOR_BLACK)
                curses.init_pair(39, curses.COLOR_BLACK, curses.COLOR_WHITE)
            except curses.error:
                pass
            return
        if curses.can_change_color():
            tricodes = list(constants.TEAM_COLORS_RGB.keys())
            for i, tricode in enumerate(tricodes[: min(30, curses.COLORS - 100)]):
                r, g, b = constants.TEAM_COLORS_RGB[tricode]
                if (r, g, b) == (128, 128, 128):
                    r, g, b = 180, 180, 180
                try:
                    curses.init_color(100 + i, r * 1000 // 255, g * 1000 // 255, b * 1000 // 255)
                    curses.init_pair(i + 1, 100 + i, -1)
                    if tricode in ("BKN", "SAS", "LAL"):
                        curses.init_pair(i + 31, curses.COLOR_BLACK, 100 + i)
                    else:
                        curses.init_pair(i + 31, curses.COLOR_WHITE, 100 + i)
                except curses.error:
                    break
            self._pair_mode = "truecolor"
            return
        self._pair_mode = "basic"
        for i, fg in enumerate([
            curses.COLOR_RED, curses.COLOR_GREEN, curses.COLOR_YELLOW,
            curses.COLOR_BLUE, curses.COLOR_MAGENTA, curses.COLOR_CYAN,
            curses.COLOR_WHITE, curses.COLOR_WHITE,
        ], 1):
            try:
                curses.init_pair(i, fg, -1)
                curses.init_pair(i + 30, curses.COLOR_WHITE, fg)
            except curses.error:
                pass
        try:
            curses.init_pair(39, curses.COLOR_BLACK, curses.COLOR_WHITE)
        except curses.error:
            pass

    def get_team_color_pair(self, tricode):
        if not tricode or self._pair_mode in ("high_contrast", "light"):
            return 1
        tricode = tricode.upper()
        if self._pair_mode == "truecolor":
            tricodes = list(constants.TEAM_COLORS_RGB.keys())
            if tricode in tricodes:
                return min(tricodes.index(tricode) + 1, 30)
            return 7
        color = TRICODE_TO_BASIC_COLOR.get(tricode, curses.COLOR_WHITE)
        return {curses.COLOR_RED: 1, curses.COLOR_GREEN: 2, curses.COLOR_YELLOW: 3,
                curses.COLOR_BLUE: 4, curses.COLOR_MAGENTA: 5, curses.COLOR_CYAN: 6,
                curses.COLOR_WHITE: 7}.get(color, 7)

    def get_team_highlight_pair(self, tricode):
        if not tricode or self._pair_mode in ("high_contrast", "light"):
            return 31
        tricode = tricode.upper()
        if tricode in ("BKN", "SAS", "LAL"):
            return 39 if self._pair_mode == "basic" else (list(constants.TEAM_COLORS_RGB.keys()).index(tricode) + 31)
        if self._pair_mode == "truecolor":
            tricodes = list(constants.TEAM_COLORS_RGB.keys())
            if tricode in tricodes:
                return min(tricodes.index(tricode) + 31, 60)
            return 31
        color = TRICODE_TO_BASIC_COLOR.get(tricode, curses.COLOR_WHITE)
        return {curses.COLOR_RED: 31, curses.COLOR_GREEN: 32, curses.COLOR_YELLOW: 33,
                curses.COLOR_BLUE: 34, curses.COLOR_MAGENTA: 35, curses.COLOR_CYAN: 36,
                curses.COLOR_WHITE: 37}.get(color, 37)
