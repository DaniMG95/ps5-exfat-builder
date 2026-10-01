import unittest
from pathlib import Path

from ps5_exfat_builder.integrations.pkg import (
    PkgBuilderTool,
    PkgBuildInput,
    generic_pkg_builder_args,
)


class PkgIntegrationTests(unittest.TestCase):
    def test_generic_pkg_builder_args_include_input_output_and_options(self):
        args = generic_pkg_builder_args(
            PkgBuilderTool(Path("pkg-builder.exe"), ("build",)),
            PkgBuildInput(
                staged_game_dir=Path("stage/game"),
                output_pkg=Path("out/game.pkg"),
                sdk="9.00",
                verify_sha256=True,
            ),
        )

        self.assertEqual(
            args,
            [
                "pkg-builder.exe",
                "build",
                "--input",
                "stage\\game" if "\\" in str(Path("stage/game")) else "stage/game",
                "--output",
                "out\\game.pkg" if "\\" in str(Path("out/game.pkg")) else "out/game.pkg",
                "--sdk",
                "9.00",
                "--verify-sha256",
            ],
        )


if __name__ == "__main__":
    unittest.main()
