from __future__ import annotations

import asyncio

from lulum import __version__
from lulum.cli import build_parser
from lulum.config import Config
from lulum.engine.apple import AppleEngine
from lulum.engine.mlx import MLXEngine
from lulum.engine.ollama import OllamaEngine
from lulum.shell import Shell
from lulum.updater import run_update


def _print_credits() -> None:
    print(
        f"\n"
        f"  lulum v{__version__}\n"
        f"  https://github.com/rdubar/lulum\n"
        f"\n"
        f"  Built and maintained by Roger Dubar (https://github.com/rdubar)\n"
        f"  Development assistance: Claude (Anthropic), Codex (OpenAI)\n"
        f"  MIT License\n"
    )


async def _run_update() -> int:
    return await run_update()


async def _run() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.update:
        raise SystemExit(await _run_update())

    config = Config.load()

    engines = [
        AppleEngine(),
        OllamaEngine(host=config.ollama_host),
        MLXEngine(),
    ]

    shell = Shell(engines=engines)

    if args.credits:
        _print_credits()
        return

    if args.subcommand == "engines":
        await shell._cmd_engines()
        return

    if args.subcommand == "models":
        await shell._detect_engines()
        await shell._cmd_models()
        return

    model = args.model or config.default_model
    await shell.run(initial_model=model, command=args.command)


def main() -> None:
    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        print("\nBye!")


if __name__ == "__main__":
    main()
