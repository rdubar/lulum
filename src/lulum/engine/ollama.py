from __future__ import annotations

import json
from typing import AsyncIterator

import httpx

from lulum.engine.base import Engine, ModelInfo


class OllamaEngine(Engine):
    name = "ollama"

    def __init__(self, host: str = "http://localhost:11434") -> None:
        self.host = host
        self.model: str | None = None

    async def is_available(self) -> bool:
        try:
            async with httpx.AsyncClient() as client:
                r = await client.get(self.host, timeout=2.0)
                return r.status_code == 200
        except (httpx.ConnectError, httpx.TimeoutException):
            return False

    async def list_models(self) -> list[ModelInfo]:
        try:
            async with httpx.AsyncClient() as client:
                r = await client.get(f"{self.host}/api/tags", timeout=5.0)
                r.raise_for_status()
                data = r.json()
        except (httpx.HTTPError, httpx.TimeoutException):
            return []

        models: list[ModelInfo] = []
        for m in data.get("models", []):
            size_bytes = m.get("size", 0)
            size_str = f"{size_bytes / (1024**3):.1f} GB" if size_bytes else None
            details = m.get("details", {})
            models.append(
                ModelInfo(
                    name=m["name"],
                    engine=self.name,
                    size=size_str,
                    params=details.get("parameter_size"),
                    details={k: str(v) for k, v in details.items()},
                )
            )
        return models

    async def load_model(self, model_name: str) -> None:
        self.model = model_name

    async def generate(
        self, messages: list[dict[str, str]], **kwargs: object
    ) -> AsyncIterator[str]:
        if not self.model:
            raise RuntimeError("No model loaded. Use /use ollama:<model> first.")

        payload: dict = {
            "model": self.model,
            "messages": messages,
            "stream": True,
        }

        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream(
                "POST", f"{self.host}/api/chat", json=payload
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    content = data.get("message", {}).get("content", "")
                    if content:
                        yield content
                    if data.get("done"):
                        return

    async def unload(self) -> None:
        self.model = None
