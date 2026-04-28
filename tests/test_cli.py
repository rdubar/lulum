from __future__ import annotations

import unittest

from lulum.cli import build_parser


class ParserTests(unittest.TestCase):
    def test_model_and_command_flags_parse(self) -> None:
        parser = build_parser()

        args = parser.parse_args(["-m", "ollama:llama3.2:1b", "-c", "hello"])

        self.assertEqual(args.model, "ollama:llama3.2:1b")
        self.assertEqual(args.command, "hello")
        self.assertIsNone(args.subcommand)

    def test_credits_flag_parses_without_subcommand(self) -> None:
        parser = build_parser()

        args = parser.parse_args(["--credits"])

        self.assertTrue(args.credits)
        self.assertIsNone(args.subcommand)

    def test_models_subcommand_parses(self) -> None:
        parser = build_parser()

        args = parser.parse_args(["models"])

        self.assertEqual(args.subcommand, "models")


if __name__ == "__main__":
    unittest.main()
