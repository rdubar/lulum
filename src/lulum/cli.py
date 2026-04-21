from __future__ import annotations

import argparse

from lulum import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lulum",
        description="Unified local LLM shell",
    )
    parser.add_argument(
        "-V", "--version", action="version", version=f"%(prog)s {__version__}"
    )
    parser.add_argument(
        "--credits", action="store_true", help="Show credits and project URL"
    )
    parser.add_argument(
        "-u",
        "--update",
        action="store_true",
        help="Run `uv tool upgrade lulum` and exit",
    )
    parser.add_argument(
        "-m", "--model", help="Model to load on start (engine:model)"
    )
    parser.add_argument(
        "-c", "--command", help="One-shot prompt (non-interactive)"
    )

    sub = parser.add_subparsers(dest="subcommand")
    sub.add_parser("engines", help="List available engines")
    sub.add_parser("models", help="List available models")

    return parser
