from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Config:
    default_engine: str = "ollama"
    default_model: str | None = None
    ollama_host: str = "http://localhost:11434"
    bitnet_path: Path = Path("~/dev/lulum/engine/bitnet").expanduser()

    @classmethod
    def load(cls) -> Config:
        config_path = Path.home() / ".config" / "lulum" / "config.toml"
        if not config_path.exists():
            return cls()

        with open(config_path, "rb") as f:
            data = tomllib.load(f)

        defaults = data.get("default", {})
        engines = data.get("engines", {})
        ollama_cfg = engines.get("ollama", {})

        return cls(
            default_engine=defaults.get("engine", cls.default_engine),
            default_model=defaults.get("model"),
            ollama_host=ollama_cfg.get("host", cls.ollama_host),
            bitnet_path=Path(
                engines.get("bitnet", {}).get("path", str(cls.bitnet_path))
            ).expanduser(),
        )
