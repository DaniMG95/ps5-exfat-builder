import contextlib
import io
import unittest

from ps5_exfat_builder.cli import main


class CliTests(unittest.TestCase):
    def test_formats_command_lists_ampr(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = main(["formats"])

        self.assertEqual(rc, 0)
        self.assertIn("ampr", output.getvalue())

    def test_routes_command_lists_pkg_route(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = main(["routes"])

        self.assertEqual(rc, 0)
        self.assertIn("exfat->pkg", output.getvalue())

    def test_ampr_dry_run_outputs_command(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = main([
                "ampr-dry-run",
                "--source",
                "game",
                "--target",
                "out.ampr",
                "--tool",
                "lazy_ampr.exe",
                "--default-arg",
                "pack",
                "--extra-arg=--fast",
            ])

        self.assertEqual(rc, 0)
        self.assertIn("lazy_ampr.exe pack --input game", output.getvalue())

    def test_ampr_dry_run_supports_target_format(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = main([
                "ampr-dry-run",
                "--source",
                "game.ampr",
                "--target",
                "game.exfat",
                "--tool",
                "lazy_ampr.exe",
                "--source-format",
                "ampr",
                "--target-format",
                "exfat",
                "--default-arg",
                "unpack",
            ])

        self.assertEqual(rc, 0)
        self.assertIn("lazy_ampr.exe unpack --input game.ampr", output.getvalue())

    def test_ampr_dry_run_supports_route_flags_and_performance(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = main([
                "ampr-dry-run",
                "--source",
                "game.ampr",
                "--target",
                "game.pkg",
                "--tool",
                "lazy_ampr.exe",
                "--source-format",
                "ampr",
                "--target-format",
                "pkg",
                "--command-style",
                "route-flags",
                "--performance-preset",
                "max",
                "--worker-count",
                "16",
            ])

        self.assertEqual(rc, 0)
        self.assertIn("--mode unpack --source-format ampr --target-format pkg", output.getvalue())

    def test_ampr_dry_run_rejects_unsupported_route(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = main([
                "ampr-dry-run",
                "--source",
                "game",
                "--target",
                "out.pkg",
                "--tool",
                "lazy_ampr.exe",
                "--source-format",
                "folder",
                "--target-format",
                "pkg",
            ])

        self.assertEqual(rc, 2)
        self.assertIn("Unsupported AMPR route", output.getvalue())

    def test_pkg_dry_run_outputs_command(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = main([
                "pkg-dry-run",
                "--source",
                "game.exfat",
                "--target",
                "out.pkg",
                "--tool",
                "pkg-builder.exe",
                "--default-arg",
                "build",
                "--sdk",
                "9.00",
                "--verify-sha256",
            ])

        self.assertEqual(rc, 0)
        self.assertIn("pkg-builder.exe build --input game.exfat", output.getvalue())
        self.assertIn("--sdk 9.00 --verify-sha256", output.getvalue())


if __name__ == "__main__":
    unittest.main()
