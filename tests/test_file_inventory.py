import tempfile
import unittest
from pathlib import Path

from ps5_exfat_builder.services.file_inventory import (
    align_up,
    estimate_exfat_image_size,
    scan_file_inventory,
)


class FileInventoryTests(unittest.TestCase):
    def test_scan_file_inventory_counts_files_and_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.bin").write_bytes(b"abc")
            nested = root / "nested"
            nested.mkdir()
            (nested / "b.bin").write_bytes(b"12345")

            inventory = scan_file_inventory(root)

            self.assertEqual(inventory.file_count, 2)
            self.assertEqual(inventory.total_bytes, 8)

    def test_align_up(self):
        self.assertEqual(align_up(65, 64), 128)
        self.assertEqual(align_up(128, 64), 128)

    def test_estimate_exfat_image_size_has_minimum_alignment(self):
        alignment = 64 * 1024 * 1024

        self.assertEqual(estimate_exfat_image_size(1), alignment)
        self.assertEqual(estimate_exfat_image_size(alignment), 128 * 1024 * 1024)


if __name__ == "__main__":
    unittest.main()
