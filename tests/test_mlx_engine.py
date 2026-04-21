from __future__ import annotations

import subprocess
import unittest
from types import SimpleNamespace

from lulum.engine.mlx import MLXEngine


class MLXEngineTests(unittest.IsolatedAsyncioTestCase):
    async def test_is_available_uses_subprocess_probe(self) -> None:
        engine = MLXEngine()
        original_run = subprocess.run

        def _fake_run(*args, **kwargs):
            self.assertIn("import mlx_lm", args[0])
            return SimpleNamespace(returncode=0)

        subprocess.run = _fake_run
        try:
            available = await engine.is_available()
        finally:
            subprocess.run = original_run

        self.assertTrue(available)


if __name__ == "__main__":
    unittest.main()
