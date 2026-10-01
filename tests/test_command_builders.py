import unittest

from ps5_exfat_builder.integrations.ufs2tool import extract_args, newfs_args
from ps5_exfat_builder.integrations.windows_volume import (
    format_exfat_args,
    robocopy_tree_args,
)


class CommandBuilderTests(unittest.TestCase):
    def test_ufs2_newfs_args_match_existing_defaults(self):
        self.assertEqual(
            newfs_args("UFS2Tool.exe", "G:\\", "out.ffpkg"),
            [
                "UFS2Tool.exe",
                "newfs",
                "-O",
                "2",
                "-b",
                "32768",
                "-f",
                "4096",
                "-S",
                "512",
                "-D",
                "G:\\",
                "out.ffpkg",
            ],
        )

    def test_ufs2_extract_args_support_root_retry(self):
        self.assertEqual(
            extract_args("UFS2Tool.exe", "in.ffpkg", "dump", root="/"),
            ["UFS2Tool.exe", "extract", "in.ffpkg", "dump", "/"],
        )

    def test_format_exfat_args(self):
        self.assertEqual(
            format_exfat_args("G:", label=""),
            ["cmd.exe", "/c", "format", "G:", "/FS:exFAT", "/Q", "/Y", "/V:"],
        )

    def test_robocopy_tree_args(self):
        self.assertEqual(
            robocopy_tree_args("dump", "G:\\"),
            [
                "robocopy.exe",
                "dump",
                "G:\\",
                "/E",
                "/COPY:DAT",
                "/DCOPY:DAT",
                "/R:1",
                "/W:1",
                "/NP",
                "/ETA",
            ],
        )


if __name__ == "__main__":
    unittest.main()
