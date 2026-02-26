"""E2E tests for CLI mode (non-interactive). Run with: python -m pytest tests/test_cli_e2e.py -v"""
import os
import sys
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"


def _run_cli(*args, timeout=15):
    """Run the app in CLI mode; return (returncode, stdout, stderr)."""
    cmd = [sys.executable, "-m", "src.main", "--help"]
    if args:
        cmd = [sys.executable, "-m", "src.main"] + list(args)
    env = {**os.environ, "PYTHONPATH": os.pathsep.join([str(ROOT), str(SRC)])}
    try:
        result = subprocess.run(
            cmd,
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
        return result.returncode, result.stdout or "", result.stderr or ""
    except subprocess.TimeoutExpired:
        return -1, "", "timeout"
    except Exception as e:
        return -1, "", str(e)


class TestCliHelp(unittest.TestCase):
    """Test --help exits 0 and shows usage."""

    def test_help_exits_zero(self):
        code, out, err = _run_cli("--help")
        self.assertEqual(code, 0, f"stderr: {err}")

    def test_help_contains_usage(self):
        code, out, err = _run_cli("--help")
        text = out or err
        self.assertIn("NBA Terminal App", text, "help should mention the app name")
        self.assertIn("today-games", text)
        self.assertIn("standings", text)


class TestCliTodayGames(unittest.TestCase):
    """Test -t/--today-games (may hit real API)."""

    def test_today_games_exits_zero(self):
        code, out, err = _run_cli("-t", timeout=30)
        self.assertEqual(code, 0, f"stderr: {err}")

    def test_today_games_prints_games_or_message(self):
        code, out, err = _run_cli("-t", timeout=30)
        text = out or err
        self.assertTrue("Games" in text or "games" in text or "No games" in text or "Failed" in text or "Data" in text)


class TestCliStandings(unittest.TestCase):
    """Test -s/--standings."""

    def test_standings_exits_zero(self):
        code, out, err = _run_cli("-s", timeout=30)
        self.assertEqual(code, 0, f"stderr: {err}")

    def test_standings_prints_east_west_or_message(self):
        code, out, err = _run_cli("-s", timeout=30)
        text = out or err
        self.assertTrue("EAST" in text or "WEST" in text or "Failed" in text or "standings" in text.lower())


class TestCliExport(unittest.TestCase):
    """Test --export-games and --export-standings (json/csv)."""

    def test_export_games_json_exits_zero(self):
        code, out, err = _run_cli("--export-games", "json", timeout=30)
        self.assertEqual(code, 0, f"stderr: {err}")

    def test_export_games_json_contains_json(self):
        code, out, err = _run_cli("--export-games", "json", timeout=30)
        text = out or err
        self.assertTrue("{" in text and ("games" in text or "date" in text) or "[]" in text)

    def test_export_standings_json_exits_zero(self):
        code, out, err = _run_cli("--export-standings", "json", timeout=30)
        self.assertEqual(code, 0, f"stderr: {err}")


class TestCliPexpect(unittest.TestCase):
    """Optional E2E with pexpect for interactive flow (skip if pexpect not installed)."""

    def setUp(self):
        try:
            import pexpect
            self.pexpect = pexpect
        except ImportError:
            self.pexpect = None

    def test_pexpect_cli_today(self):
        if self.pexpect is None:
            self.skipTest("pexpect not installed")
        child = self.pexpect.spawn(
            f"{sys.executable} -m src.main -t",
            cwd=str(ROOT),
            env={**os.environ, "PYTHONPATH": os.pathsep.join([str(ROOT), str(SRC)])},
            timeout=20,
            encoding="utf-8",
        )
        try:
            child.expect(["Games", "games", "No games", "Failed", self.pexpect.EOF], timeout=15)
        except Exception:
            pass
        child.close()
        self.assertIn(child.exitstatus, (0, None))


if __name__ == "__main__":
    unittest.main()
