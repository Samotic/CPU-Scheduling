from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scheduler.utils.models import Process
from scheduler.utils.parser import load_processes


ROOT = Path(__file__).resolve().parents[1]


class ParserTests(unittest.TestCase):
    def load_text(self, text: str):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "processes.txt"
            path.write_text(text, encoding="utf-8")
            return load_processes(path)

    def test_comments_whitespace_and_integer_priorities(self):
        processes = self.load_text("  # workload\n\nP1\t0\t3\t-1\nP2 2 1 0\n")
        self.assertEqual(processes, [Process("P1", 0, 3, -1), Process("P2", 2, 1, 0)])

    def test_invalid_workloads(self):
        cases = [
            ("# empty\n", "No processes"),
            ("P1 0 1\n", "Line 1 must contain"),
            ("P1 0 one 1\n", "Line 1 contains a non-integer"),
            ("P1 -1 2 0\n", "arrival time must be non-negative"),
            ("P1 0 0 0\n", "burst time must be positive"),
            ("P1 0 -2 0\n", "burst time must be positive"),
            ("P1 0 2 0\nP1 1 1 1\n", "Line 2: duplicate PID"),
            ("IDLE 0 2 0\n", "reserved for idle intervals"),
        ]
        for text, message in cases:
            with self.subTest(text=text):
                with self.assertRaisesRegex(ValueError, message):
                    self.load_text(text)

    def test_missing_file(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(FileNotFoundError, "Input file not found"):
                load_processes(Path(directory) / "missing.txt")


class CliTests(unittest.TestCase):
    def run_cli(self, *arguments: str, module: bool = False):
        entry = ["-m", "scheduler.scheduler"] if module else ["scheduler/scheduler.py"]
        return subprocess.run(
            [sys.executable, *entry, *arguments],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=10,
        )

    def test_script_and_module_entry_points(self):
        for module in (False, True):
            with self.subTest(module=module):
                result = self.run_cli("--input", "processes.txt", "--algo", " fcfs ", module=module)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("Algorithm: FCFS", result.stdout)
                self.assertIn("Context Switches: 4", result.stdout)

    def test_round_robin_accepts_positive_quantum(self):
        result = self.run_cli("--input", "processes.txt", "--algo", "RR", "--quantum", "3")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Algorithm: RR(q=3)", result.stdout)

    def test_invalid_arguments_fail_before_simulation(self):
        cases = [
            (["--algo", "RR"], "--quantum is required"),
            (["--algo", "RR", "--quantum", "0"], "must be a positive integer"),
            (["--algo", "ALL", "--quantum", "0"], "must be a positive integer"),
            (["--algo", "RR", "--quantum", "-1"], "must be a positive integer"),
            (["--algo", "RR", "--quantum", "1.5"], "invalid int value"),
            (["--algo", "UNKNOWN"], "invalid choice"),
        ]
        for arguments, message in cases:
            with self.subTest(arguments=arguments):
                result = self.run_cli("--input", "processes.txt", *arguments)
                self.assertEqual(result.returncode, 2)
                self.assertIn(message, result.stderr)
                self.assertNotIn("Traceback", result.stderr)
                self.assertEqual(result.stdout, "")

    def test_invalid_workload_exits_instead_of_hanging(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.txt"
            path.write_text("P1 0 0 1\n", encoding="utf-8")
            result = self.run_cli("--input", str(path), "--algo", "SRTF")
        self.assertEqual(result.returncode, 2)
        self.assertIn("burst time must be positive", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_missing_input_is_a_readable_error(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "missing.txt"
            result = self.run_cli("--input", str(path), "--algo", "FCFS")
        self.assertEqual(result.returncode, 2)
        self.assertIn("Input file not found", result.stderr)
        self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
