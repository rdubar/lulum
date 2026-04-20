# lulum

A unified shell for running local LLM inference across multiple engines.

On **macOS 26+ with Apple Silicon**, lulum works out of the box — no model downloads, no setup — using the built-in Apple Intelligence model via the `FoundationModels` framework.

lulum provides a single interactive CLI that wraps Apple Intelligence, Ollama, MLX, and other local inference backends behind a common interface. Switch between engines and models with a single command.

## Install

Requires [uv](https://docs.astral.sh/uv/).

**Permanent install** — run `lulum` from anywhere:

```bash
uv tool install lulum
lulum
```

**Update to latest:**

```bash
uv tool upgrade lulum
```

**Try without installing:**

```bash
uvx lulum
```

**Uninstall:**

```bash
uv tool uninstall lulum
```

## Development setup

```bash
git clone https://github.com/rdubar/lulum
cd lulum
uv sync
uv run lulum
```

## Requirements

- [uv](https://docs.astral.sh/uv/) — Python package manager
- At least one inference engine installed:
  - **Apple Intelligence** — zero setup on macOS 26+ with Apple Silicon (auto-detected)
  - [Ollama](https://ollama.com) — easiest cross-platform option
  - [MLX](https://github.com/ml-explore/mlx-lm) — Apple Silicon optimized (`uv sync --extra mlx`)

## Usage

### Interactive shell

```
$ lulum

  lulum v0.1.0
  Engines: ollama (ready), mlx (not available)
  No model loaded — use /use engine:model

lulum [no model]> /use ollama:llama3.2:1b
Loading ollama:llama3.2:1b...
Ready.

lulum [ollama:llama3.2:1b]> Hello!
Hi there! How can I help you today?
```

### One-shot mode

```bash
lulum -m ollama:llama3.2:1b -c "Explain quicksort in one sentence"
```

### CLI commands

```bash
lulum                          # interactive shell
lulum -m ollama:llama3.2       # start with a model loaded
lulum -c "prompt"              # one-shot (requires -m)
lulum engines                  # list available engines
lulum models                   # list available models
```

### Shell commands

| Command              | Description                |
|----------------------|----------------------------|
| `/use engine:model`  | Load a model               |
| `/engines`           | List engines and status    |
| `/models`            | List available models      |
| `/history`           | Show conversation history  |
| `/clear`             | Clear conversation         |
| `/help`              | Show help                  |
| `/quit`              | Exit                       |

## Popular models

Via Ollama — install a model with `ollama pull <name>`, then load it in lulum with `/use ollama:<name>`:

| Model | Command | Notes |
|-------|---------|-------|
| **Gemma 3** (Google) | `ollama pull gemma3` | Free, open-source, strong general performance |
| **Llama 3.2** (Meta) | `ollama pull llama3.2` | Good all-rounder; 1b/3b/11b sizes |
| **Mistral** | `ollama pull mistral` | Fast, efficient 7B model |
| **Phi-4** (Microsoft) | `ollama pull phi4` | Small but capable reasoning model |
| **Qwen 2.5** (Alibaba) | `ollama pull qwen2.5` | Strong coding and multilingual |
| **Apple Intelligence** | built-in | macOS 26+ with Apple Silicon, no download |

Browse the full catalogue at [ollama.com/library](https://ollama.com/library).

## Engines

| Engine  | Status      | Platform        | Notes                                          |
|---------|-------------|-----------------|------------------------------------------------|
| Apple   | Working     | macOS 26+ / AS  | Built-in Apple Intelligence, no setup needed   |
| Ollama  | Working     | macOS/Linux/Win | Requires `ollama` installed and running        |
| MLX     | Scaffolded  | Apple Silicon   | `uv sync --extra mlx`                          |
| BitNet  | Planned     | macOS/Linux     | 1-bit LLM inference                            |

Engines degrade gracefully — lulum auto-detects what's available at startup and skips engines that aren't installed or supported on the current platform.

## Architecture

```
src/lulum/
├── __main__.py          # entry point
├── cli.py               # argument parsing
├── shell.py             # interactive REPL
├── config.py            # settings (TOML)
└── engine/
    ├── base.py          # abstract Engine interface
    ├── apple.py         # Apple Intelligence (FoundationModels, macOS 26+)
    ├── ollama.py        # Ollama backend
    └── mlx.py           # MLX backend
```

All engines implement a common async interface — `generate()` returns an `AsyncIterator[str]` for streaming tokens. Adding a new engine means implementing one class with five methods.

## Configuration

Optional config file at `~/.config/lulum/config.toml`:

```toml
[default]
engine = "ollama"
model = "llama3.2:1b"

[engines.ollama]
host = "http://localhost:11434"

[engines.bitnet]
path = "~/dev/lulum/engine/bitnet"
```

## License

MIT
