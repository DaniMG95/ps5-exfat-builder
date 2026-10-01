import tempfile
import unittest
from pathlib import Path
from unittest import mock

from ps5_exfat_builder.domain import TransformRequest
from ps5_exfat_builder.formats.pkg import (
    ExfatToPkgConverter,
    FfpfscToPkgConverter,
    PkgConversionError,
)


class PkgConverterTests(unittest.TestCase):
    def test_exfat_to_pkg_requires_tool_path(self):
        converter = ExfatToPkgConverter()

        result = converter.convert(
            TransformRequest(
                source=Path("game.exfat"),
                target=Path("game.pkg"),
                source_format="exfat",
                target_format="pkg",
            )
        )

        self.assertFalse(result.ok)
        self.assertIn("tool_path", result.message)

    def test_exfat_to_pkg_dry_run_builds_command(self):
        converter = ExfatToPkgConverter()

        result = converter.convert(
            TransformRequest(
                source=Path("game.exfat"),
                target=Path("game.pkg"),
                source_format="exfat",
                target_format="pkg",
                options={
                    "tool_path": "pkg-builder.exe",
                    "default_args": "build",
                    "sdk": "9.00",
                    "verify_sha256": True,
                    "extra_args": ["--fast"],
                    "dry_run": True,
                },
            )
        )

        self.assertTrue(result.ok)
        self.assertEqual(
            result.details["args"],
            [
                "pkg-builder.exe",
                "build",
                "--input",
                "game.exfat",
                "--output",
                "game.pkg",
                "--sdk",
                "9.00",
                "--verify-sha256",
                "--fast",
            ],
        )

    def test_ffpfsc_to_pkg_dry_run_is_available(self):
        converter = FfpfscToPkgConverter()

        result = converter.convert(
            TransformRequest(
                source=Path("game.ffpfsc"),
                target=Path("game.pkg"),
                source_format="ffpfsc",
                target_format="pkg",
                options={"tool_path": "pkg-builder.exe", "dry_run": True},
            )
        )

        self.assertTrue(result.ok)
        self.assertIn("game.ffpfsc", result.details["args"])

    def test_real_run_validates_source_timeout_and_reports_details(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tool = root / "pkg-builder.exe"
            source = root / "game.exfat"
            target = root / "out" / "game.pkg"
            tool.write_text("", encoding="utf-8")
            source.write_bytes(b"exfat")
            converter = ExfatToPkgConverter()
            fake_result = mock.Mock(
                args=("pkg-builder.exe", "--input", "game.exfat"),
                returncode=0,
                output="done",
            )

            with mock.patch(
                "ps5_exfat_builder.formats.pkg.run_command",
                return_value=fake_result,
            ) as run:
                result = converter.convert(
                    TransformRequest(
                        source=source,
                        target=target,
                        source_format="exfat",
                        target_format="pkg",
                        options={"tool_path": tool, "timeout": "30"},
                    )
                )
            output_parent_created = target.parent.is_dir()

        self.assertTrue(result.ok)
        self.assertTrue(output_parent_created)
        self.assertEqual(result.details["tool"], str(tool))
        run.assert_called_once()
        self.assertEqual(run.call_args.kwargs["timeout"], 30.0)

    def test_converter_rejects_wrong_route(self):
        converter = ExfatToPkgConverter()

        with self.assertRaises(PkgConversionError):
            converter.convert(
                TransformRequest(
                    source=Path("game.ffpfsc"),
                    target=Path("game.pkg"),
                    source_format="ffpfsc",
                    target_format="pkg",
                    options={"tool_path": "pkg-builder.exe", "dry_run": True},
                )
            )


if __name__ == "__main__":
    unittest.main()
