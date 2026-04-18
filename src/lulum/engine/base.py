from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncIterator


@dataclass
class ModelInfo:
    name: str
    engine: str
    size: str | None = None
    params: str | None = None
    details: dict[str, str] = field(default_factory=dict)

    @property
    def full_name(self) -> str:
        return f"{self.engine}:{self.name}"


class Engine(ABC):
    name: str

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if this engine is installed and reachable."""

    @abstractmethod
    async def list_models(self) -> list[ModelInfo]:
        """Return models available to this engine."""

    @abstractmethod
    async def load_model(self, model_name: str) -> None:
        """Prepare/load a model for inference."""

    @abstractmethod
    async def generate(
        self, messages: list[dict[str, str]], **kwargs: object
    ) -> AsyncIterator[str]:
        """Stream tokens for a chat-completion request.

        messages: OpenAI-style [{"role": "user", "content": "..."}]
        Yields string chunks as they arrive.
        """
        yield ""  # make this a generator for type checkers

    async def unload(self) -> None:
        """Release model resources."""
