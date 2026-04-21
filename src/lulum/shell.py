from __future__ import annotations

import asyncio
import sys
from typing import TYPE_CHECKING

from lulum import __version__
from lulum.engine.base import ModelInfo
from lulum.history import LocalHistory
from lulum.updater import run_update

if TYPE_CHECKING:
    from lulum.engine.base import Engine


class Shell:
    def __init__(self, engines: list[Engine]) -> None:
        self.engines: dict[str, Engine] = {e.name: e for e in engines}
        self.active_engine: Engine | None = None
        self.active_model: str | None = None
        self.history: list[dict[str, str]] = []
        self.local_history = LocalHistory()
        self._engine_status: dict[str, bool] = {}
        self._engine_models: dict[str, list[ModelInfo]] = {}

    async def run(
        self,
        initial_model: str | None = None,
        command: str | None = None,
    ) -> None:
        self.local_history.initialize_input_history()
        await self._detect_engines()

        if initial_model:
            await self._cmd_use(initial_model, reset_history=False)

        if not self.active_engine:
            await self._auto_select_model(reset_history=False)

        if command:
            if not self.active_engine:
                self._print_no_model_message()
                return
            await self._chat(command)
            return

        self._restore_history()
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

            self.local_history.save_input_history()

            if user_input.startswith("/"):
                should_quit = await self._handle_command(user_input)
                if should_quit:
                    break
            else:
                await self._chat(user_input)

    async def _detect_engines(self) -> None:
        results = await asyncio.gather(
            *(self._probe_engine(name, engine) for name, engine in self.engines.items())
        )
        self._engine_status = {name: available for name, available, _ in results}
        self._engine_models = {name: models for name, _, models in results}

    async def _probe_engine(
        self, name: str, engine: Engine
    ) -> tuple[str, bool, list[ModelInfo]]:
        available = await self._engine_available_with_retry(name, engine)
        if not available:
            return name, False, []

        try:
            models = await engine.list_models()
        except Exception:
            models = []
        return name, True, models

    async def _engine_available_with_retry(self, name: str, engine: Engine) -> bool:
        if name != "ollama":
            return await engine.is_available()

        delays = (0.0, 0.4, 1.0)
        for index, delay in enumerate(delays):
            if delay:
                await asyncio.sleep(delay)
            if await engine.is_available():
                return True
            if index == len(delays) - 1:
                break
        return False

    def _engine_status_text(self, name: str) -> str:
        if not self._engine_status.get(name):
            return "not available"

        models = self._engine_models.get(name, [])
        if name == "ollama" and not models:
            return "ready, no models"

        return "ready"

    def _discovered_model_count(self) -> int:
        return sum(len(models) for models in self._engine_models.values())

    def _startup_guidance_lines(self) -> list[str]:
        lines: list[str] = []

        if self._engine_status.get("ollama") and not self._engine_models.get("ollama"):
            lines.append("  Ollama is running but has no pulled models yet.")
            lines.append("  Try: ollama pull llama3.2:1b")

        if self._engine_status.get("mlx") and not self._engine_models.get("mlx"):
            lines.append("  MLX is ready. Load a model directly with /use mlx:<model-repo>.")

        return lines

    async def _auto_select_model(self, reset_history: bool = True) -> None:
        total_models = self._discovered_model_count()
        for name, engine in self.engines.items():
            if not self._engine_status.get(name):
                continue
            models = self._engine_models.get(name, [])
            if models:
                model = models[0]
                await self._cmd_use(model.full_name, reset_history=reset_history)
                print(f"  Auto-selected {model.full_name}")
                if total_models == 1:
                    print("  Only 1 discovered model is ready right now.\n")
                else:
                    print(f"  {total_models} discovered models available — use /models to see all\n")
                return

    def _print_banner(self) -> None:
        parts = []
        for name in self._engine_status:
            parts.append(f"{name} ({self._engine_status_text(name)})")
        engines_str = ", ".join(parts)

        print(f"\n  lulum v{__version__}")
        print(f"  Engines: {engines_str}")
        if self.active_model:
            print(f"  Active: {self.active_model}")
        else:
            print("  No model loaded — use /use engine:model")
            for line in self._startup_guidance_lines():
                print(line)
        print()

    def _prompt(self) -> str:
        return "> "

    def _print_no_model_message(self) -> None:
        print("Error: no model loaded.")
        print("Specify one with -m engine:model or /use engine:model.")
        for line in self._startup_guidance_lines():
            print(line)
        print()

    async def _handle_command(self, raw: str) -> bool:
        parts = raw.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1].strip() if len(parts) > 1 else ""

        commands: dict[str, object] = {
            "/engines": self._cmd_engines,
            "/engine": self._cmd_engine,
            "/models": self._cmd_models,
            "/use": lambda: self._cmd_use(arg),
            "/update": self._cmd_update,
            "/history": self._cmd_history,
            "/clear": lambda: self._cmd_clear(arg),
            "/version": self._cmd_version,
            "/credits": self._cmd_credits,
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
        for name in self._engine_status:
            status_text = self._engine_status_text(name)
            status = (
                f"\033[32m{status_text}\033[0m"
                if self._engine_status.get(name)
                else f"\033[31m{status_text}\033[0m"
            )
            active = " *" if (self.active_engine and self.active_engine.name == name) else ""
            print(f"  {name:<12} {status}{active}")
        print()

    async def _cmd_models(self) -> None:
        await self._detect_engines()
        print()
        found = False
        for name, engine in self.engines.items():
            if not self._engine_status.get(name):
                continue
            models = self._engine_models.get(name, [])
            for m in models:
                found = True
                size = f"  ({m.size})" if m.size else ""
                params = f"  [{m.params}]" if m.params else ""
                print(f"  {m.full_name:<40}{size}{params}")
            if name == "ollama" and not models:
                print("  ollama: running, but no models are installed yet")
                print("          try: ollama pull llama3.2:1b")
            if name == "mlx" and not models:
                print("  mlx: ready — load a model directly with /use mlx:<model-repo>")
        if not found:
            print("  No auto-discovered models found.")
            for line in self._startup_guidance_lines():
                print(line)
        print()

    async def _cmd_use(self, arg: str, reset_history: bool = True) -> None:
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
            if reset_history:
                self._clear_conversation_history()
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

    async def _cmd_update(self) -> None:
        await run_update()

    async def _cmd_clear(self, arg: str = "") -> None:
        target = arg.strip().lower()

        if target in ("", "all"):
            self._clear_conversation_history()
            if self.local_history.clear_input_history():
                print("Local conversation and input history cleared.\n")
            else:
                print("Conversation cleared. Input history is unavailable on this system.\n")
            return

        if target in ("chat", "conversation"):
            self._clear_conversation_history()
            print("Conversation history cleared.\n")
            return

        if target in ("input", "inputs", "lines"):
            if self.local_history.clear_input_history():
                print("Input history cleared.\n")
            else:
                print("Input history is unavailable on this system.\n")
            return

        print("Usage: /clear [all|chat|input]\n")

    async def _cmd_version(self) -> None:
        print(f"\n  lulum v{__version__}\n")

    async def _cmd_credits(self) -> None:
        print(
            f"\n"
            f"  lulum v{__version__}\n"
            f"  https://github.com/rdubar/lulum\n"
            f"\n"
            f"  Built and maintained by Roger Dubar (https://github.com/rdubar)\n"
            f"  Development assistance: Claude (Anthropic), Codex (OpenAI)\n"
            f"  MIT License\n"
        )

    async def _cmd_engine(self) -> None:
        if self.active_model:
            print(f"\n  {self.active_model}\n")
        else:
            print("\n  No model loaded — use /use engine:model\n")

    async def _cmd_help(self) -> None:
        print(
            f"""
  lulum v{__version__}

  Session
    /use engine:model   Load a model (e.g. /use ollama:llama3.2)
    /engine             Show the active engine and model
    /engines            List detected engines and availability
    /models             List models from available engines
    /update             Run `uv tool upgrade lulum`

  History
    /history            Show saved conversation history
    /clear              Clear saved conversation and input history
    /clear chat         Clear only saved conversation history
    /clear input        Clear only arrow-key prompt history

  Info
    /version            Show version
    /credits            Show credits, repo URL, and license
    /help               Show this help
    /quit               Exit lulum

  Local history lives in ~/.local/state/lulum/
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
        self.local_history.save_chat_history(self.history, model=self.active_model)

    def _restore_history(self) -> None:
        stored_model, history = self.local_history.load_chat_history()
        if not history:
            return

        if stored_model and self.active_model and stored_model != self.active_model:
            print(
                f"  Saved history for {stored_model} was not restored because"
                f" the active model is {self.active_model}. Use /clear to remove it.\n"
            )
            return

        self.history = history
        print(
            f"  Restored {len(self.history)} saved messages."
            f" Use /clear to start fresh.\n"
        )

    def _clear_conversation_history(self) -> None:
        self.history.clear()
        self.local_history.clear_chat_history()
