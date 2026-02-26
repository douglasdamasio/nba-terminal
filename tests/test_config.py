"""Tests for config module: AppConfig, get_config_dir, load/save, get_text, helpers."""
import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import config


class TestGetConfigDir(unittest.TestCase):
    def test_linux_macos_uses_xdg_or_config(self):
        with patch.dict(os.environ, {"XDG_CONFIG_HOME": "/xdg"}, clear=False):
            with patch("sys.platform", "linux"):
                self.assertEqual(config.get_config_dir(), "/xdg/nba-terminal")
        with patch.dict(os.environ, {}, clear=False):
            with patch("sys.platform", "darwin"):
                self.assertIn("nba-terminal", config.get_config_dir())
                self.assertTrue(config.get_config_dir().endswith("nba-terminal"))

    def test_windows_uses_appdata(self):
        with patch("sys.platform", "win32"):
            with patch.dict(os.environ, {"APPDATA": "C:\\Users\\X\\AppData\\Roaming"}, clear=False):
                d = config.get_config_dir()
                self.assertIn("nba-terminal", d)
                self.assertIn("AppData", d)
                self.assertTrue(d.endswith("nba-terminal"))


class TestAppConfig(unittest.TestCase):
    def test_defaults(self):
        cfg = config.AppConfig()
        self.assertEqual(cfg.language, "en")
        self.assertEqual(cfg.refresh_interval_seconds, 30)
        self.assertEqual(cfg.favorite_team, "LAL")
        self.assertEqual(cfg.game_sort, "time")
        self.assertEqual(cfg.theme, "default")
        self.assertEqual(cfg.layout_mode, "auto")

    def test_validation_rejects_invalid_language(self):
        with self.assertRaises(Exception):
            config.AppConfig(language="fr")

    def test_validation_accepts_pt(self):
        cfg = config.AppConfig(language="pt")
        self.assertEqual(cfg.language, "pt")

    def test_validation_refresh_interval_bounds(self):
        config.AppConfig(refresh_interval_seconds=0)
        config.AppConfig(refresh_interval_seconds=300)
        with self.assertRaises(Exception):
            config.AppConfig(refresh_interval_seconds=-1)
        with self.assertRaises(Exception):
            config.AppConfig(refresh_interval_seconds=301)


class TestConfigHelpers(unittest.TestCase):
    def test_get_text_en(self):
        self.assertEqual(config.get_text({"language": "en"}, "footer_quit"), "Quit")
        self.assertEqual(config.get_text(None, "footer_quit"), "Quit")

    def test_get_text_pt(self):
        self.assertEqual(config.get_text({"language": "pt"}, "footer_quit"), "Sair")

    def test_get_text_unknown_key_returns_key(self):
        self.assertEqual(config.get_text({"language": "en"}, "unknown_key"), "unknown_key")

    def test_favorite_team(self):
        self.assertEqual(config.favorite_team({}), "LAL")
        self.assertEqual(config.favorite_team({"favorite_team": "BOS"}), "BOS")
        self.assertEqual(config.favorite_team(None), "LAL")

    def test_refresh_interval(self):
        self.assertEqual(config.refresh_interval({}), 30)
        self.assertEqual(config.refresh_interval({"refresh_interval_seconds": 60}), 60)

    def test_last_game_date(self):
        self.assertIsNone(config.last_game_date({}))
        self.assertEqual(config.last_game_date({"last_game_date": "2025-02-16"}), "2025-02-16")

    def test_game_sort(self):
        self.assertEqual(config.game_sort({}), "time")
        self.assertEqual(config.game_sort({"game_sort": "favorite_first"}), "favorite_first")

    def test_timezone(self):
        self.assertEqual(config.timezone({}), "localtime")
        self.assertEqual(config.timezone({"timezone": "America/Sao_Paulo"}), "America/Sao_Paulo")

    def test_theme(self):
        self.assertEqual(config.theme({}), "default")
        self.assertEqual(config.theme({"theme": "high_contrast"}), "high_contrast")

    def test_refresh_mode(self):
        self.assertEqual(config.refresh_mode({}), "fixed")
        self.assertEqual(config.refresh_mode({"refresh_mode": "auto"}), "auto")

    def test_layout_mode(self):
        self.assertEqual(config.layout_mode({}), "auto")
        self.assertEqual(config.layout_mode({"layout_mode": "compact"}), "compact")

    def test_get_tzinfo_localtime(self):
        self.assertIsNone(config.get_tzinfo({}))
        self.assertIsNone(config.get_tzinfo({"timezone": "localtime"}))

    def test_get_tzinfo_valid_zone(self):
        tz = config.get_tzinfo({"timezone": "America/Sao_Paulo"})
        self.assertIsNotNone(tz)
        self.assertEqual(str(tz), "America/Sao_Paulo")

    def test_get_tzinfo_invalid_zone_returns_none(self):
        self.assertIsNone(config.get_tzinfo({"timezone": "Invalid/Zone"}))


class TestLoadSaveConfig(unittest.TestCase):
    def test_load_config_missing_file_creates_default(self):
        tmp = Path(__file__).resolve().parent / "tmp_config_nba"
        tmp.mkdir(exist_ok=True)
        config_path = tmp / "config.json"
        if config_path.exists():
            config_path.unlink()
        try:
            with patch.object(config, "get_config_path", return_value=str(config_path)):
                cfg = config.load_config()
            self.assertIn("language", cfg)
            self.assertIn("favorite_team", cfg)
            self.assertTrue(config_path.exists())
        finally:
            if config_path.exists():
                config_path.unlink()
            if tmp.exists():
                try:
                    tmp.rmdir()
                except OSError:
                    pass

    def test_save_config_valid_persists(self):
        tmp = Path(__file__).resolve().parent / "tmp_config_nba"
        tmp.mkdir(exist_ok=True)
        config_path = tmp / "config.json"
        try:
            with patch.object(config, "get_config_path", return_value=str(config_path)):
                config.save_config({"language": "pt", "favorite_team": "BOS"})
            self.assertTrue(config_path.exists())
            data = json.loads(config_path.read_text(encoding="utf-8"))
            self.assertEqual(data.get("language"), "pt")
            self.assertEqual(data.get("favorite_team"), "BOS")
        finally:
            if config_path.exists():
                config_path.unlink()
            if tmp.exists():
                try:
                    tmp.rmdir()
                except OSError:
                    pass


if __name__ == "__main__":
    unittest.main()
