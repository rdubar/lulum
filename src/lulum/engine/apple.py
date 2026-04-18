from __future__ import annotations

import asyncio
import json
import subprocess
import sys
from pathlib import Path
from typing import AsyncIterator

from lulum.engine.base import Engine, ModelInfo

_TOOL_SRC = Path(__file__).parent / "apple-llm.swift"
_TOOL_BIN = Path.home() / ".cache" / "lulum" / "apple-llm"


class AppleEngine(Engine):
    name = "apple"

    async def is_available(self) -> bool:
        if sys.platform != "darwin":
            return False
        try:
            result = await asyncio.to_thread(
                subprocess.run,
                [
                    "xcrun", "--sdk", "macosx", "swift", "-e",
                    "import FoundationModels; print(SystemLanguageModel.default.availability)",
                ],
                capture_output=True,
                text=True,
                timeout=15,
            )
            return result.returncode == 0 and "available" in result.stdout
        except Exception:
            return False

    async def list_models(self) -> list[ModelInfo]:
        return [
            ModelInfo(
                name="on-device",
                engine=self.name,
                details={"note": "Apple Intelligence on-device model (macOS 26+)"},
            )
        ]

    async def load_model(self, model_name: str) -> None:
        await self._ensure_binary()

    async def generate(
        self, messages: list[dict[str, str]], **kwargs: object
    ) -> AsyncIterator[str]:
        await self._ensure_binary()

        payload = json.dumps(messages).encode()

        proc = await asyncio.create_subprocess_exec(
            str(_TOOL_BIN),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        assert proc.stdin and proc.stdout and proc.stderr

        proc.stdin.write(payload)
        await proc.stdin.drain()
        proc.stdin.close()

        while True:
            chunk = await proc.stdout.read(128)
            if not chunk:
                break
            yield chunk.decode(errors="replace")

        await proc.wait()
        if proc.returncode != 0:
            err = (await proc.stderr.read()).decode().strip()
            raise RuntimeError(f"apple-llm: {err}")

    async def unload(self) -> None:
        pass

    async def _ensure_binary(self) -> None:
        if _TOOL_BIN.exists():
            return
        if not _TOOL_SRC.exists():
            raise FileNotFoundError(f"Swift source not found: {_TOOL_SRC}")
        _TOOL_BIN.parent.mkdir(parents=True, exist_ok=True)
        print("Building apple-llm (one-time compile)…", flush=True)
        result = await asyncio.to_thread(
            subprocess.run,
            [
                "xcrun", "--sdk", "macosx", "swiftc",
                "-framework", "FoundationModels",
                str(_TOOL_SRC), "-o", str(_TOOL_BIN),
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Compile failed:\n{result.stderr}")
        print("apple-llm ready.", flush=True)
