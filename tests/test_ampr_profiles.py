import tempfile
import unittest
from pathlib import Path

from ps5_exfat_builder.integrations.ampr import (
    AmprBuildInput,
    AmprTool,
    build_ampr_args,
    discover_profiles,
    find_tool,
    load_profile,
    profile_candidates,
    tool_candidates,
)


class AmprProfileTests(unittest.TestCase):
    def test_profile_candidates_are_sorted_toml_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "b.toml").write_text("name = 'B'\n", encoding="utf-8")
            (root / "a.toml").write_text("name = 'A'\n", encoding="utf-8")
            (root / "ignore.txt").write_text("", encoding="utf-8")

            self.assertEqual(
                [path.name for path in profile_candidates(root)],
                ["a.toml", "b.toml"],
            )

    def test_load_profile_uses_name_or_stem(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            named = root / "profile.toml"
            unnamed = root / "fallback.toml"
            named.write_text("name = 'Default AMPR'\n", encoding="utf-8")
            unnamed.write_text("[compression]\nlevel = 9\n", encoding="utf-8")

            self.assertEqual(load_profile(named).name, "Default AMPR")
            self.assertEqual(load_profile(unnamed).name, "fallback")

    def test_discover_profiles_loads_all_candidates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.toml").write_text("name = 'A'\n", encoding="utf-8")
            (root / "b.toml").write_text("name = 'B'\n", encoding="utf-8")

            self.assertEqual(
                [profile.name for profile in discover_profiles(root)],
                ["A", "B"],
            )

    def test_find_tool_accepts_file_or_known_launcher_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            launcher = root / "run.bat"
            launcher.write_text("@echo off\n", encoding="utf-8")

            self.assertEqual(tool_candidates(root), (launcher,))
            self.assertEqual(find_tool(root), launcher)
            self.assertEqual(find_tool(launcher), launcher)

    def test_build_args_support_route_flags_style(self):
        args = build_ampr_args(
            AmprTool(Path("lazy_ampr.exe"), default_args=("convert",)),
            AmprBuildInput(
                source=Path("game.ampr"),
                output=Path("game.exfat"),
                mode="unpack",
                source_format="ampr",
                target_format="exfat",
                extra_args=("--fast",),
            ),
            style="route-flags",
        )

        self.assertEqual(
            args,
            [
                "lazy_ampr.exe",
                "convert",
                "--mode",
                "unpack",
                "--source-format",
                "ampr",
                "--target-format",
                "exfat",
                "--input",
                "game.ampr",
                "--output",
                "game.exfat",
                "--fast",
            ],
        )

    def test_build_args_support_positional_style(self):
        args = build_ampr_args(
            AmprTool(Path("lazy_ampr.exe")),
            AmprBuildInput(
                source=Path("game"),
                output=Path("out.ampr"),
                mode="pack",
                source_format="folder",
                target_format="ampr",
            ),
            style="positional",
        )

        self.assertEqual(args, ["lazy_ampr.exe", "pack", "game", "out.ampr"])

    def test_build_args_reject_unknown_style(self):
        with self.assertRaises(ValueError):
            build_ampr_args(
                AmprTool(Path("lazy_ampr.exe")),
                AmprBuildInput(source=Path("game"), output=Path("out.ampr")),
                style="unknown",  # type: ignore[arg-type]
            )


if __name__ == "__main__":
    unittest.main()
