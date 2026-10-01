import unittest

from ps5_exfat_builder.formats import default_registry


class FormatRegistryTests(unittest.TestCase):
    def test_default_registry_knows_planned_formats(self):
        registry = default_registry()

        self.assertEqual(registry.get_format("exfat").extensions, (".exfat",))
        self.assertTrue(registry.get_format("ampr").can_build)
        self.assertEqual(registry.get_format("pkg").extensions, (".pkg",))

    def test_registry_starts_without_wired_converters(self):
        registry = default_registry()

        self.assertFalse(registry.can_convert("exfat", "pkg"))
        self.assertFalse(registry.can_convert("folder", "ampr"))

    def test_registry_can_include_experimental_ampr_converters(self):
        registry = default_registry(include_experimental=True)

        self.assertTrue(registry.can_convert("folder", "ampr"))
        self.assertTrue(registry.can_convert("exfat", "ampr"))
        self.assertTrue(registry.can_convert("ffpkg", "ampr"))
        self.assertTrue(registry.can_convert("ffpfs", "ampr"))
        self.assertTrue(registry.can_convert("ffpfsc", "ampr"))
        self.assertTrue(registry.can_convert("pkg", "ampr"))
        self.assertTrue(registry.can_convert("ampr", "folder"))
        self.assertTrue(registry.can_convert("ampr", "exfat"))
        self.assertTrue(registry.can_convert("ampr", "ffpkg"))
        self.assertTrue(registry.can_convert("ampr", "ffpfs"))
        self.assertTrue(registry.can_convert("ampr", "ffpfsc"))
        self.assertTrue(registry.can_convert("ampr", "pkg"))
        self.assertTrue(registry.can_convert("exfat", "pkg"))
        self.assertTrue(registry.can_convert("ffpfsc", "pkg"))

    def test_registry_detects_known_extensions(self):
        registry = default_registry()

        self.assertEqual(registry.detect_path_format("game.exfat"), "exfat")
        self.assertEqual(registry.detect_path_format("game.ffpfsc"), "ffpfsc")
        self.assertEqual(registry.detect_path_format("game.pkg"), "pkg")
        self.assertIsNone(registry.detect_path_format("game.bin"))


if __name__ == "__main__":
    unittest.main()
