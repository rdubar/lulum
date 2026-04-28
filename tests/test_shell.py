from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout

from lulum.engine.base import ModelInfo
from lulum.shell import Shell


class FakeEngine:
    def __init__(
        self,
        name: str,
        *,
        available: bool = True,
        models: list[ModelInfo] | None = None,
    ) -> None:
        self.name = name
        self._available = available
        self._models = models or []

    async def is_available(self) -> bool:
        return self._available

    async def list_models(self) -> list[ModelInfo]:
        return list(self._models)

    async def load_model(self, model_name: str) -> None:
        return None

    async def unload(self) -> None:
        return None


class FlakyOllamaEngine(FakeEngine):
    def __init__(self, results: list[bool]) -> None:
        super().__init__("ollama", available=False, models=[])
        self.results = list(results)
        self.calls = 0

    async def is_available(self) -> bool:
        self.calls += 1
        if self.results:
            return self.results.pop(0)
        return False


class ShellStartupTests(unittest.IsolatedAsyncioTestCase):
    async def test_detect_engines_collects_models(self) -> None:
        shell = Shell(
            engines=[
                FakeEngine(
                    "apple",
                    models=[ModelInfo(name="on-device", engine="apple")],
                ),
                FakeEngine("ollama", models=[]),
            ]
        )

        await shell._detect_engines()

        self.assertTrue(shell._engine_status["apple"])
        self.assertEqual(shell._engine_models["apple"][0].full_name, "apple:on-device")
        self.assertEqual(shell._engine_status_text("ollama"), "ready, no models")

    async def test_ollama_availability_retries(self) -> None:
        engine = FlakyOllamaEngine([False, False, True])
        shell = Shell(engines=[engine])

        available = await shell._engine_available_with_retry("ollama", engine)

        self.assertTrue(available)
        self.assertEqual(engine.calls, 3)

    async def test_auto_select_reports_total_discovered_models(self) -> None:
        apple = FakeEngine(
            "apple",
            models=[ModelInfo(name="on-device", engine="apple")],
        )
        ollama = FakeEngine(
            "ollama",
            models=[ModelInfo(name="llama3.2:1b", engine="ollama")],
        )
        shell = Shell(engines=[apple, ollama])
        await shell._detect_engines()

        used: list[str] = []

        async def _fake_use(model: str, reset_history: bool = True) -> None:
            used.append(model)
            shell.active_model = model
            shell.active_engine = shell.engines[model.split(":", 1)[0]]

        shell._cmd_use = _fake_use  # type: ignore[method-assign]

        output = io.StringIO()
        with redirect_stdout(output):
            await shell._auto_select_model(reset_history=False)

        self.assertEqual(used, ["apple:on-device"])
        self.assertIn("2 discovered models available", output.getvalue())

    async def test_print_banner_shows_ollama_guidance(self) -> None:
        shell = Shell(
            engines=[
                FakeEngine("apple", available=False),
                FakeEngine("ollama", models=[]),
                FakeEngine("mlx", models=[]),
            ]
        )
        await shell._detect_engines()

        output = io.StringIO()
        with redirect_stdout(output):
            shell._print_banner()

        banner = output.getvalue()
        self.assertIn("ollama (ready, no models)", banner)
        self.assertIn("Try: ollama pull llama3.2:1b", banner)

    async def test_restore_history_restores_when_model_matches(self) -> None:
        shell = Shell(engines=[FakeEngine("apple")])
        shell.active_model = "apple:on-device"
        shell.local_history = type(
            "StubHistory",
            (),
            {
                "load_chat_history": staticmethod(
                    lambda: (
                        "apple:on-device",
                        [{"role": "user", "content": "Hello"}],
                    )
                )
            },
        )()

        output = io.StringIO()
        with redirect_stdout(output):
            shell._restore_history()

        self.assertEqual(shell.history, [{"role": "user", "content": "Hello"}])
        self.assertIn("Restored 1 saved messages", output.getvalue())

    async def test_restore_history_skips_when_model_differs(self) -> None:
        shell = Shell(engines=[FakeEngine("apple")])
        shell.active_model = "apple:on-device"
        shell.local_history = type(
            "StubHistory",
            (),
            {
                "load_chat_history": staticmethod(
                    lambda: (
                        "ollama:llama3.2:1b",
                        [{"role": "user", "content": "Hello"}],
                    )
                )
            },
        )()

        output = io.StringIO()
        with redirect_stdout(output):
            shell._restore_history()

        self.assertEqual(shell.history, [])
        self.assertIn("was not restored because the active model is apple:on-device", output.getvalue())


if __name__ == "__main__":
    unittest.main()
