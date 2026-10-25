"""Official Meterless Open Core Conformance Runner Test.

Executes the official TypeScript conformance test suites for:
1. H-MEM (Hierarchical Memory): 13 checks against vectors.json
2. World Model Engine: 8 checks for stable IDs, idempotency, and audit ordering
3. Markovian Engine: 8 checks for efficiency math, chunkConfig snapshots, and marker protocol

Verifies 100% compliance against Meterless Open Core (Apache 2.0).
"""

from __future__ import annotations

import os
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent


class TestMeterlessOfficialConformance(unittest.TestCase):
    """Executes official TypeScript conformance runners via npx tsx."""

    @classmethod
    def setUpClass(cls):
        cls.npx_cmd = shutil.which("npx") or shutil.which("npx.cmd")

    def _run_conformance(self, engine_name: str, runner_rel_path: str) -> subprocess.CompletedProcess:
        if not self.npx_cmd:
            self.skipTest("npx not available in PATH")

        engine_dir = ROOT_DIR / "engines" / "meterless" / engine_name
        runner_path = engine_dir / runner_rel_path
        if not runner_path.exists():
            self.skipTest(f"Runner not found: {runner_path}")

        cmd = [self.npx_cmd, "--yes", "tsx", str(runner_path)]
        res = subprocess.run(
            cmd,
            cwd=str(engine_dir),
            capture_output=True,
            text=True,
            timeout=30,
        )
        return res

    def test_hmem_official_conformance_13_checks(self):
        """H-MEM: Executes official conformance runner verifying 13/13 checks pass."""
        res = self._run_conformance("hmem", "conformance/runner.ts")
        self.assertEqual(
            res.returncode,
            0,
            f"H-MEM conformance failed with code {res.returncode}:\n{res.stdout}\n{res.stderr}",
        )
        self.assertIn("13/13 checks passed", res.stdout)

    def test_world_model_official_conformance_8_checks(self):
        """World Model: Executes official conformance runner verifying 8/8 checks pass."""
        res = self._run_conformance("world-model", "conformance/runner.ts")
        self.assertEqual(
            res.returncode,
            0,
            f"World Model conformance failed with code {res.returncode}:\n{res.stdout}\n{res.stderr}",
        )
        self.assertIn("8/8 checks passed", res.stdout)

    def test_markovian_official_conformance_8_checks(self):
        """Markovian: Executes official conformance runner verifying 8/8 checks pass."""
        res = self._run_conformance("markovian", "conformance/runner.ts")
        self.assertEqual(
            res.returncode,
            0,
            f"Markovian conformance failed with code {res.returncode}:\n{res.stdout}\n{res.stderr}",
        )
        self.assertIn("8/8 checks passed", res.stdout)


if __name__ == "__main__":
    unittest.main()
