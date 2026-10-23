#!/usr/bin/env python3
"""Main Entrypoint for HG GridMind — Open Agent Hackathon 2026.

Usage:
    python main.py run                  # Runs incident investigation
    python main.py run --signoff        # Runs investigation and exercises human approval gate
    python main.py test                 # Executes offline test suite
    python main.py web --port 8080      # Launches interactive web demo
"""

from __future__ import annotations

import argparse
import sys
import unittest
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.cli import run_investigation, serve_web


def main() -> None:
    parser = argparse.ArgumentParser(
        description="HG GridMind: The AI Incident Commander That Can Explain Why (Challenge 02)"
    )
    subparsers = parser.add_subparsers(dest="command", help="Subcommand to execute")

    # Run command
    run_parser = subparsers.add_parser("run", help="Run incident investigation")
    run_parser.add_argument(
        "--fixture",
        type=Path,
        default=ROOT_DIR / "fixtures" / "incident_INC_2026_UTIL_8812.json",
        help="Path to synthetic incident dataset fixture",
    )
    run_parser.add_argument(
        "--signoff",
        action="store_true",
        help="Simulate authorized human operator sign-off",
    )
    run_parser.add_argument(
        "--operator",
        type=str,
        default="Hernan Greco",
        help="Operator name for human approval gate",
    )

    # Test command
    subparsers.add_parser("test", help="Execute offline unit tests")

    # Web command
    web_parser = subparsers.add_parser("web", help="Launch interactive web dashboard")
    web_parser.add_argument("--port", type=int, default=8080, help="Web port (default 8080)")

    args = parser.parse_args()

    if args.command == "run" or args.command is None:
        fixture = getattr(args, "fixture", ROOT_DIR / "fixtures" / "incident_INC_2026_UTIL_8812.json")
        signoff = getattr(args, "signoff", False)
        operator = getattr(args, "operator", "Hernan Greco")
        run_investigation(fixture, signoff=signoff, operator_name=operator)
    elif args.command == "test":
        suite = unittest.defaultTestLoader.discover(str(ROOT_DIR / "tests"))
        runner = unittest.TextTestRunner(verbosity=2)
        res = runner.run(suite)
        sys.exit(0 if res.wasSuccessful() else 1)
    elif args.command == "web":
        serve_web(port=args.port, web_dir=ROOT_DIR / "web")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
