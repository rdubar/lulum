from __future__ import annotations

import json
from pathlib import Path

try:
    import readline
except ImportError:  # pragma: no cover - readline is platform-dependent
    readline = None

type Message = dict[str, str]
type ChatHistoryPayload = tuple[str | None, list[Message]]

STATE_DIR = Path.home() / ".local" / "state" / "lulum"
CHAT_HISTORY_PATH = STATE_DIR / "chat_history.json"
INPUT_HISTORY_PATH = STATE_DIR / "input_history.txt"


class LocalHistory:
    def __init__(
        self,
        chat_history_path: Path = CHAT_HISTORY_PATH,
        input_history_path: Path = INPUT_HISTORY_PATH,
    ) -> None:
        self.chat_history_path = chat_history_path
        self.input_history_path = input_history_path

    def load_chat_history(self) -> ChatHistoryPayload:
        if not self.chat_history_path.exists():
            return None, []

        try:
            data = json.loads(self.chat_history_path.read_text())
        except (OSError, json.JSONDecodeError):
            return None, []

        if isinstance(data, list):
            return None, self._normalize_messages(data)

        if not isinstance(data, dict):
            return None, []

        model = data.get("model")
        messages = data.get("messages")
        if not isinstance(model, str):
            model = None
        if not isinstance(messages, list):
            return model, []

        return model, self._normalize_messages(messages)

    def save_chat_history(
        self,
        history: list[Message],
        model: str | None = None,
    ) -> None:
        payload = {
            "model": model,
            "messages": history,
        }

        self._ensure_state_dir()
        temp_path = self.chat_history_path.with_suffix(".tmp")
        temp_path.write_text(json.dumps(payload, indent=2))
        temp_path.replace(self.chat_history_path)

    def clear_chat_history(self) -> None:
        if self.chat_history_path.exists():
            self.chat_history_path.unlink()

    def initialize_input_history(self) -> bool:
        if readline is None:
            return False

        self._ensure_state_dir()
        readline.set_history_length(1000)
        if hasattr(readline, "set_auto_history"):
            readline.set_auto_history(True)

        if self.input_history_path.exists():
            try:
                readline.read_history_file(self.input_history_path)
            except OSError:
                return False
        return True

    def save_input_history(self) -> bool:
        if readline is None:
            return False

        self._ensure_state_dir()
        try:
            readline.write_history_file(self.input_history_path)
        except OSError:
            return False
        return True

    def clear_input_history(self) -> bool:
        if readline is None:
            return False

        readline.clear_history()
        return self.save_input_history()

    def _ensure_state_dir(self) -> None:
        self.chat_history_path.parent.mkdir(parents=True, exist_ok=True)

    def _normalize_messages(self, data: list[object]) -> list[Message]:
        history: list[Message] = []
        for item in data:
            if not isinstance(item, dict):
                continue
            role = item.get("role")
            content = item.get("content")
            if isinstance(role, str) and isinstance(content, str):
                history.append({"role": role, "content": content})
        return history
