import tempfile
import unittest
from unittest import mock
from pathlib import Path

from ps5_exfat_builder.domain import TransformRequest
from ps5_exfat_builder.formats.ampr import (
    AMPR_ROUTES,
    AmprConversionError,
    AmprConverter,
    ExfatToAmprConverter,
    FolderToAmprConverter,
    ampr_converters,
)


class AmprConverterTests(unittest.TestCase):
    def test_folder_to_ampr_requires_tool_path(self):
        converter = FolderToAmprConverter()

        result = converter.convert(
            TransformRequest(
                source=Path("game"),
                target=Path("out.ampr"),
                source_format="folder",
                target_format="ampr",
            )
        )

        self.assertFalse(result.ok)
        self.assertIn("tool_path", result.message)

    def test_folder_to_ampr_dry_run_builds_command_with_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = root / "default.toml"
            profile.write_text("name = 'Default'\n", encoding="utf-8")
            converter = FolderToAmprConverter()
            events = []

            result = converter.convert(
                TransformRequest(
                    source=Path("game"),
                    target=Path("out.ampr"),
                    source_format="folder",
                    target_format="ampr",
                    options={
                        "tool_path": "lazy_ampr.exe",
                        "profile_path": profile,
                        "default_args": ["pack"],
                        "extra_args": ["--fast"],
                        "dry_run": True,
                    },
                ),
                events.append,
            )

        self.assertTrue(result.ok)
        self.assertEqual(
            result.details["args"],
            [
                "lazy_ampr.exe",
                "pack",
                "--input",
                "game",
                "--output",
                "out.ampr",
                "--profile",
                str(profile),
                "--fast",
            ],
        )
        self.assertEqual(events[0].step, "ampr")

    def test_exfat_to_ampr_dry_run_is_available(self):
        converter = ExfatToAmprConverter()

        result = converter.convert(
            TransformRequest(
                source=Path("game.exfat"),
                target=Path("out.ampr"),
                source_format="exfat",
                target_format="ampr",
                options={"tool_path": "lazy_ampr.exe", "dry_run": True},
            )
        )

        self.assertTrue(result.ok)
        self.assertIn("game.exfat", result.details["args"])
        self.assertEqual(result.details["route"], "exfat->ampr")
        self.assertEqual(result.details["mode"], "pack")

    def test_ampr_to_exfat_dry_run_is_available(self):
        converter = AmprConverter(source_format="ampr", target_format="exfat")

        result = converter.convert(
            TransformRequest(
                source=Path("game.ampr"),
                target=Path("game.exfat"),
                source_format="ampr",
                target_format="exfat",
                options={"tool_path": "lazy_ampr.exe", "dry_run": True},
            )
        )

        self.assertTrue(result.ok)
        self.assertIn("game.ampr", result.details["args"])
        self.assertEqual(result.details["route"], "ampr->exfat")
        self.assertEqual(result.details["mode"], "unpack")

    def test_converter_supports_route_flags_command_style(self):
        converter = AmprConverter(source_format="ampr", target_format="pkg")

        result = converter.convert(
            TransformRequest(
                source=Path("game.ampr"),
                target=Path("game.pkg"),
                source_format="ampr",
                target_format="pkg",
                options={
                    "tool_path": "lazy_ampr.exe",
                    "command_style": "route-flags",
                    "dry_run": "true",
                },
            )
        )

        self.assertTrue(result.ok)
        self.assertEqual(result.details["command_style"], "route-flags")
        self.assertEqual(
            result.details["args"],
            [
                "lazy_ampr.exe",
                "--mode",
                "unpack",
                "--source-format",
                "ampr",
                "--target-format",
                "pkg",
                "--input",
                "game.ampr",
                "--output",
                "game.pkg",
            ],
        )

    def test_converter_rejects_unknown_command_style(self):
        converter = FolderToAmprConverter()

        result = converter.convert(
            TransformRequest(
                source=Path("game"),
                target=Path("out.ampr"),
                source_format="folder",
                target_format="ampr",
                options={
                    "tool_path": "lazy_ampr.exe",
                    "command_style": "unknown",
                    "dry_run": True,
                },
            )
        )

        self.assertFalse(result.ok)
        self.assertIn("command_style", result.message)

    def test_converter_supports_maximum_performance_preset(self):
        converter = FolderToAmprConverter()

        result = converter.convert(
            TransformRequest(
                source=Path("game"),
                target=Path("out.ampr"),
                source_format="folder",
                target_format="ampr",
                options={
                    "tool_path": "lazy_ampr.exe",
                    "performance_preset": "max",
                    "worker_count": "8",
                    "dry_run": True,
                },
            )
        )

        self.assertTrue(result.ok)
        self.assertEqual(
            result.details["performance"],
            {"priority": "high", "use_all_cpus": True, "worker_count": 8},
        )

    def test_converter_rejects_invalid_worker_count(self):
        converter = FolderToAmprConverter()

        result = converter.convert(
            TransformRequest(
                source=Path("game"),
                target=Path("out.ampr"),
                source_format="folder",
                target_format="ampr",
                options={
                    "tool_path": "lazy_ampr.exe",
                    "worker_count": "0",
                    "dry_run": True,
                },
            )
        )

        self.assertFalse(result.ok)
        self.assertIn("worker_count", result.message)

    def test_factory_exposes_every_ampr_route(self):
        self.assertEqual(
            {converter.route for converter in ampr_converters()},
            set(AMPR_ROUTES),
        )

    def test_generic_converter_rejects_non_ampr_route(self):
        with self.assertRaises(AmprConversionError):
            AmprConverter(source_format="folder", target_format="pkg")

    def test_dry_run_keeps_string_args_whole(self):
        converter = FolderToAmprConverter()

        result = converter.convert(
            TransformRequest(
                source=Path("game"),
                target=Path("out.ampr"),
                source_format="folder",
                target_format="ampr",
                options={
                    "tool_path": "lazy_ampr.exe",
                    "default_args": "pack",
                    "extra_args": "--fast",
                    "dry_run": True,
                },
            )
        )

        self.assertTrue(result.ok)
        self.assertEqual(
            result.details["args"],
            [
                "lazy_ampr.exe",
                "pack",
                "--input",
                "game",
                "--output",
                "out.ampr",
                "--fast",
            ],
        )

    def test_invalid_profile_returns_failure_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "broken.toml"
            profile.write_text("name = [\n", encoding="utf-8")
            converter = FolderToAmprConverter()

            result = converter.convert(
                TransformRequest(
                    source=Path("game"),
                    target=Path("out.ampr"),
                    source_format="folder",
                    target_format="ampr",
                    options={
                        "tool_path": "lazy_ampr.exe",
                        "profile_path": profile,
                        "dry_run": True,
                    },
                )
            )

        self.assertFalse(result.ok)
        self.assertIn("profile", result.message)

    def test_real_run_rejects_missing_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tool = root / "lazy_ampr.exe"
            tool.write_text("", encoding="utf-8")
            converter = FolderToAmprConverter()

            result = converter.convert(
                TransformRequest(
                    source=root / "missing",
                    target=root / "out" / "game.ampr",
                    source_format="folder",
                    target_format="ampr",
                    options={"tool_path": tool},
                )
            )

        self.assertFalse(result.ok)
        self.assertIn("source not found", result.message)

    def test_real_run_rejects_invalid_timeout(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tool = root / "lazy_ampr.exe"
            source = root / "game"
            tool.write_text("", encoding="utf-8")
            source.mkdir()
            converter = FolderToAmprConverter()

            result = converter.convert(
                TransformRequest(
                    source=source,
                    target=root / "out" / "game.ampr",
                    source_format="folder",
                    target_format="ampr",
                    options={"tool_path": tool, "timeout": "soon"},
                )
            )

        self.assertFalse(result.ok)
        self.assertIn("timeout", result.message)

    def test_real_run_creates_output_parent_and_reports_details(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tool = root / "lazy_ampr.exe"
            source = root / "game"
            target = root / "out" / "game.ampr"
            tool.write_text("", encoding="utf-8")
            source.mkdir()
            converter = FolderToAmprConverter()

            fake_result = mock.Mock(
                args=("lazy_ampr.exe", "--input", "game"),
                returncode=0,
                output="done",
            )
            with mock.patch(
                "ps5_exfat_builder.formats.ampr.run_command",
                return_value=fake_result,
            ) as run:
                result = converter.convert(
                    TransformRequest(
                        source=source,
                        target=target,
                        source_format="folder",
                        target_format="ampr",
                        options={"tool_path": tool, "timeout": "12.5"},
                    )
                )
            output_parent_created = target.parent.is_dir()

        self.assertTrue(result.ok)
        self.assertTrue(output_parent_created)
        self.assertEqual(result.details["tool"], str(tool))
        run.assert_called_once()
        self.assertEqual(run.call_args.kwargs["timeout"], 12.5)

    def test_converter_rejects_wrong_route(self):
        converter = FolderToAmprConverter()

        with self.assertRaises(AmprConversionError):
            converter.convert(
                TransformRequest(
                    source=Path("game.exfat"),
                    target=Path("out.ampr"),
                    source_format="exfat",
                    target_format="ampr",
                    options={"tool_path": "lazy_ampr.exe", "dry_run": True},
                )
            )


if __name__ == "__main__":
    unittest.main()
