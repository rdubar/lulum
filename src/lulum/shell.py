from __future__ import annotations

import asyncio
import sys
from typing import TYPE_CHECKING

from lulum import __version__

if TYPE_CHECKING:
    from lulum.engine.base import Engine


class Shell:
    def __init__(self, engines: list[Engine]) -> None:
        self.engines: dict[str, Engine] = {e.name: e for e in engines}
        self.active_engine: Engine | None = None
        self.active_model: str | None = None
        self.history: list[dict[str, str]] = []
        self._engine_status: dict[str, bool] = {}

    async def run(
        self,
        initial_model: str | None = None,
        command: str | None = None,
    ) -> None:
        await self._detect_engines()

        if initial_model:
            await self._cmd_use(initial_model)

        if not self.active_engine:
            await self._auto_select_model()

        if command:
            if not self.active_engine:
                print("Error: no model loaded. Specify with -m engine:model")
                return
            await self._chat(command)
            return

        self._print_banner()

        while True:
            try:
                user_input = await asyncio.to_thread(input, self._prompt())
            except (EOFError, KeyboardInterrupt):
                print("\nBye!")
                break

            user_input = user_input.strip()
            if not user_input:
                continue

            if user_input.startswith("/"):
                should_quit = await self._handle_command(user_input)
                if should_quit:
                    break
            else:
                await self._chat(user_input)

    async def _detect_engines(self) -> None:
        tasks = {name: engine.is_available() for name, engine in self.engines.items()}
        for name, coro in tasks.items():
            self._engine_status[name] = await coro

    async def _auto_select_model(self) -> None:
        for name, engine in self.engines.items():
            if not self._engine_status.get(name):
                continue
            models = await engine.list_models()
            if models:
                model = models[0]
                await self._cmd_use(model.full_name)
                print(f"  Auto-selected {model.full_name} (only available model)")
                if len(models) > 1:
                    print(f"  {len(models)} models available — use /models to see all\n")
                else:
                    print()
                return

    def _print_banner(self) -> None:
        parts = []
        for name, available in self._engine_status.items():
            status = "ready" if available else "not available"
            parts.append(f"{name} ({status})")
        engines_str = ", ".join(parts)

        print(f"\n  lulum v{__version__}")
        print(f"  Engines: {engines_str}")
        if self.active_model:
            print(f"  Active: {self.active_model}")
        else:
            print("  No model loaded — use /use engine:model")
        print()

    def _prompt(self) -> str:
        model = self.active_model or "no model"
        return f"lulum [{model}]> "

    async def _handle_command(self, raw: str) -> bool:
        parts = raw.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1].strip() if len(parts) > 1 else ""

        commands: dict[str, object] = {
            "/engines": self._cmd_engines,
            "/models": self._cmd_models,
            "/use": lambda: self._cmd_use(arg),
            "/history": self._cmd_history,
            "/clear": self._cmd_clear,
            "/help": self._cmd_help,
            "/quit": None,
            "/exit": None,
        }

        if cmd in ("/quit", "/exit"):
            print("Bye!")
            return True

        handler = commands.get(cmd)
        if handler is None:
            print(f"Unknown command: {cmd}. Type /help for commands.")
            return False

        await handler()  # type: ignore[misc]
        return False

    async def _cmd_engines(self) -> None:
        await self._detect_engines()
        print()
        for name, available in self._engine_status.items():
            status = "\033[32mready\033[0m" if available else "\033[31mnot available\033[0m"
            active = " *" if (self.active_engine and self.active_engine.name == name) else ""
            print(f"  {name:<12} {status}{active}")
        print()

    async def _cmd_models(self) -> None:
        print()
        found = False
        for name, engine in self.engines.items():
            if not self._engine_status.get(name):
                continue
            models = await engine.list_models()
            for m in models:
                found = True
                size = f"  ({m.size})" if m.size else ""
                params = f"  [{m.params}]" if m.params else ""
                print(f"  {m.full_name:<40}{size}{params}")
        if not found:
            print("  No models found. Pull a model first (e.g. `ollama pull llama3.2`)")
        print()

    async def _cmd_use(self, arg: str) -> None:
        if ":" not in arg:
            print("Usage: /use engine:model  (e.g. /use ollama:llama3.2)")
            return

        engine_name, model_name = arg.split(":", 1)

        engine = self.engines.get(engine_name)
        if not engine:
            available = ", ".join(self.engines.keys())
            print(f"Unknown engine: {engine_name}. Available: {available}")
            return

        if not self._engine_status.get(engine_name):
            print(f"Engine '{engine_name}' is not available.")
            return

        if self.active_engine:
            await self.active_engine.unload()

        print(f"Loading {engine_name}:{model_name}...")
        try:
            await engine.load_model(model_name)
            self.active_engine = engine
            self.active_model = f"{engine_name}:{model_name}"
            self.history.clear()
            print(f"Ready.\n")
        except Exception as e:
            print(f"Failed to load model: {e}\n")

    async def _cmd_history(self) -> None:
        print()
        if not self.history:
            print("  (empty)")
        for i, msg in enumerate(self.history, 1):
            role = msg["role"]
            content = msg["content"]
            preview = content[:80] + ("..." if len(content) > 80 else "")
            print(f"  [{i}] {role}: {preview}")
        print()

    async def _cmd_clear(self) -> None:
        self.history.clear()
        print("Conversation cleared.\n")

    async def _cmd_help(self) -> None:
        print(
            """
  /use engine:model   Load a model (e.g. /use ollama:llama3.2)
  /engines            List available engines
  /models             List available models
  /history            Show conversation history
  /clear              Clear conversation history
  /help               Show this help
  /quit               Exit lulum
"""
        )

    async def _chat(self, text: str) -> None:
        if not self.active_engine:
            print("No model loaded. Use /use engine:model first.\n")
            return

        self.history.append({"role": "user", "content": text})
        full_response: list[str] = []

        try:
            async for chunk in self.active_engine.generate(self.history):
                sys.stdout.write(chunk)
                sys.stdout.flush()
                full_response.append(chunk)
        except Exception as e:
            print(f"\nError: {e}")
            self.history.pop()
            return

        sys.stdout.write("\n\n")
        sys.stdout.flush()
        self.history.append({"role": "assistant", "content": "".join(full_response)})
