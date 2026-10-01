import tempfile
import unittest
from pathlib import Path

from ps5_exfat_builder.integrations.osfmount import (
    OsfDismountCommand,
    OsfMountImageCommand,
    find_in_directory,
    find_osfmount,
    first_free_drive_letter,
    prefer_cli_wrapper,
)


class OsfMountTests(unittest.TestCase):
    def test_mount_command_uses_read_write_or_read_only_options(self):
        rw = OsfMountImageCommand(
            executable=Path("osfmount.com"),
            image=Path("game.exfat"),
            mount_point="G:",
            read_only=False,
        )
        ro = OsfMountImageCommand(
            executable=Path("osfmount.com"),
            image=Path("game.exfat"),
            mount_point="H:",
            read_only=True,
        )

        self.assertEqual(
            rw.argv(),
            [
                "osfmount.com",
                "-a",
                "-t",
                "file",
                "-f",
                "game.exfat",
                "-m",
                "G:",
                "-o",
                "rw,rem",
            ],
        )
        self.assertEqual(ro.argv()[-1], "ro,rem")

    def test_dismount_command(self):
        command = OsfDismountCommand(Path("osfmount.com"), "G:")

        self.assertEqual(command.argv(), ["osfmount.com", "-d", "-m", "G:"])

    def test_prefer_cli_wrapper_when_exe_has_com_sibling(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            exe = root / "OSFMount.exe"
            com = root / "osfmount.com"
            exe.write_text("", encoding="utf-8")
            com.write_text("", encoding="utf-8")

            self.assertEqual(prefer_cli_wrapper(exe), str(com))

    def test_find_in_directory_prefers_cli_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "OSFMount.exe").write_text("", encoding="utf-8")
            (root / "osfmount.com").write_text("", encoding="utf-8")

            self.assertEqual(find_in_directory(root), str(root / "osfmount.com"))

    def test_find_osfmount_uses_custom_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            expected = root / "OSFMount.exe"
            expected.write_text("", encoding="utf-8")

            self.assertEqual(find_osfmount(str(root)), str(expected))

    def test_first_free_drive_letter_from_mask(self):
        used = 0
        used |= 1 << (ord("G") - ord("A"))
        used |= 1 << (ord("H") - ord("A"))

        self.assertEqual(first_free_drive_letter(used), "I:")


if __name__ == "__main__":
    unittest.main()
