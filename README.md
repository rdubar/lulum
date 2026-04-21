# lulum

`lulum` is a lightweight local LLM shell with one interface for multiple engines.

On **macOS 26+ with Apple Silicon**, it can work out of the box with the built-in
Apple Intelligence model via `FoundationModels`. It can also talk to engines like
Ollama and MLX behind the same interactive CLI.

The goal is simple: one terminal-first chat shell, one command style, and easy
switching between local backends.

## Install

Requires [uv](https://docs.astral.sh/uv/).

Install globally:

```bash
uv tool install lulum
lulum                         # then run it
```

Upgrade:

```bash
uv tool upgrade lulum   # or: lulum --update
```

Try without installing:

```bash
uvx lulum
```

Uninstall:

```bash
uv tool uninstall lulum
```

## Development

```bash
git clone https://github.com/rdubar/lulum
cd lulum
uv sync
uv run lulum
```

`uv sync` commands only work from inside a cloned `lulum` project directory that
contains `pyproject.toml`. If you run `uv sync --extra mlx` from `~` or another
unrelated folder, `uv` will fail because there is no project there.

## Requirements

- [uv](https://docs.astral.sh/uv/) — Python package manager
- At least one inference engine installed:
  - **Apple Intelligence** — zero setup on macOS 26+ with Apple Silicon (auto-detected)
  - [Ollama](https://ollama.com) — easiest cross-platform option
  - [MLX](https://github.com/ml-explore/mlx-lm) — Apple Silicon optimized; for a repo checkout, run `uv sync --extra mlx` from inside `~/dev/lulum`

## Quick Start

```bash
lulum
```

Then inside the shell:

```text
/models
/use ollama:llama3.2
Hello!
```

## Usage

### Interactive shell

```text
$ lulum

  Restored 6 saved messages. Use /clear to start fresh.

  lulum v0.1.2
  Engines: apple (ready), ollama (ready), mlx (not available)
  Active: apple:on-device

> /use ollama:llama3.2:1b
Loading ollama:llama3.2:1b...
Ready.

> Hello!
Hi there! How can I help you today?
```

### One-shot mode

```bash
lulum -m ollama:llama3.2:1b -c "Explain quicksort in one sentence"
```

### MLX setup

If you cloned the repo and want MLX support in the local development environment:

```bash
cd ~/dev/lulum   # or wherever you installed/cloned lulum
uv sync --extra mlx
uv run lulum
```

If you are using the globally installed `lulum` tool, `uv sync --extra mlx` is
not the right command, because it only works inside the repo. In that case,
reinstall or upgrade the global tool with MLX support separately.

### CLI commands

```bash
lulum                          # interactive shell
lulum --update                 # upgrade the installed tool via uv
lulum -m ollama:llama3.2       # start with a model loaded
lulum -c "prompt"              # one-shot (requires -m)
lulum engines                  # list available engines
lulum models                   # list available models
lulum --credits                # show credits and project info
```

### Maintenance and info

```bash
lulum --update                 # upgrade the globally installed lulum tool
lulum --credits                # show version, project URL, author, and license
```

### Shell commands

| Command | Description |
|---------|-------------|
| `/use engine:model` | Load a model |
| `/engine` | Show the active engine and model |
| `/engines` | List engines and status |
| `/models` | List available models |
| `/update` | Upgrade the installed tool via `uv` |
| `/history` | Show saved conversation history |
| `/clear` | Clear saved chat + input history |
| `/clear chat`        | Clear only saved chat history |
| `/clear input` | Clear only prompt history |
| `/version` | Show version |
| `/credits` | Show credits, repo URL, and license |
| `/help` | Show help |
| `/quit` | Exit |

Inside the interactive shell:

```text
/update                        # upgrade lulum via uv
/credits                       # show version, project URL, author, and license
```

## Local History

`lulum` stores history locally per user in `~/.local/state/lulum/`.

- `chat_history.json` stores the conversation that `/history` shows and that can
  be restored when you reopen the shell. Saved chat history is restored only when
  it matches the active model.
- `input_history.txt` stores prompt history so the up/down arrow keys can recall
  previous lines across launches.

Use `/clear` to wipe both, `/clear chat` to remove only conversation history, or
`/clear input` to remove only prompt history.

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

| Engine | Status | Platform | Notes |
|--------|--------|----------|-------|
| Apple | Working | macOS 26+ / AS | Built-in Apple Intelligence, no setup needed |
| Ollama | Working | macOS/Linux/Win | Requires `ollama` installed and running |
| MLX | Scaffolded | Apple Silicon | `uv sync --extra mlx` |
| BitNet | Planned | macOS/Linux | 1-bit LLM inference |

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

## Credits

Use either `/credits` inside the shell or `lulum --credits` in your terminal to
show the project URL, maintainer, and license.

Use either `/update` inside the shell or `lulum --update` in your terminal to
upgrade the tool.

## License

MIT
