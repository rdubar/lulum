from __future__ import annotations

import asyncio
import subprocess


async def run_update() -> int:
    print("Running `uv tool upgrade lulum`...\n")
    try:
        result = await asyncio.to_thread(
            subprocess.run,
            ["uv", "tool", "upgrade", "lulum"],
            check=False,
        )
    except FileNotFoundError:
        print("Error: `uv` is not installed or not on PATH.")
        print("Install uv first, then run `uv tool upgrade lulum`.\n")
        return 1

    if result.returncode == 0:
        print("\nlulum update complete.")
        print("Restart lulum to use the new version.\n")
    return result.returncode
