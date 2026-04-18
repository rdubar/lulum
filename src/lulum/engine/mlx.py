from __future__ import annotations

import asyncio
from typing import AsyncIterator

from lulum.engine.base import Engine, ModelInfo


class MLXEngine(Engine):
    name = "mlx"

    def __init__(self) -> None:
        self._model = None
        self._tokenizer = None
        self._model_name: str | None = None

    async def is_available(self) -> bool:
        try:
            import mlx_lm  # noqa: F401

            return True
        except ImportError:
            return False

    async def list_models(self) -> list[ModelInfo]:
        if self._model_name:
            return [ModelInfo(name=self._model_name, engine=self.name)]
        return []

    async def load_model(self, model_name: str) -> None:
        import mlx_lm

        self._model, self._tokenizer = await asyncio.to_thread(
            mlx_lm.load, model_name
        )
        self._model_name = model_name

    async def generate(
        self, messages: list[dict[str, str]], **kwargs: object
    ) -> AsyncIterator[str]:
        if not self._model or not self._tokenizer:
            raise RuntimeError("No model loaded. Use /use mlx:<model> first.")

        import mlx_lm

        prompt = self._tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

        queue: asyncio.Queue[str | None] = asyncio.Queue()

        def _run() -> None:
            for token_text, _ in mlx_lm.stream_generate(
                self._model, self._tokenizer, prompt=prompt, max_tokens=2048
            ):
                queue.put_nowait(token_text)
            queue.put_nowait(None)

        loop = asyncio.get_event_loop()
        task = loop.run_in_executor(None, _run)

        while True:
            try:
                chunk = queue.get_nowait()
            except asyncio.QueueEmpty:
                await asyncio.sleep(0.01)
                continue
            if chunk is None:
                break
            yield chunk

        await task

    async def unload(self) -> None:
        self._model = None
        self._tokenizer = None
        self._model_name = None
