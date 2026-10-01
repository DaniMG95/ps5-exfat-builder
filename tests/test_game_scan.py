import json
import tempfile
import unittest
from pathlib import Path

from ps5_exfat_builder.domain.game_scan import (
    build_exfat_name,
    get_game_info,
    parse_param_json,
    sanitize_filename,
)


class GameScanTests(unittest.TestCase):
    def test_sanitize_filename_removes_windows_and_shell_hazards(self):
        self.assertEqual(
            sanitize_filename('Ratchet & Clank: Rift/Apart™'),
            "Ratchet Clank RiftApart",
        )

    def test_build_exfat_name_uses_id_title_and_version(self):
        self.assertEqual(
            build_exfat_name("Game Name", "PPSA12345", "01.002.000"),
            "PPSA12345 Game Name (01.002.000).exfat",
        )

    def test_parse_param_json_prefers_default_language(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "param.json"
            path.write_text(
                json.dumps(
                    {
                        "titleId": "PPSA99999",
                        "version": "01.00",
                        "localizedParameters": {
                            "defaultLanguage": "es-ES",
                            "es-ES": {"titleName": "Titulo ES"},
                            "en-US": {"titleName": "Title EN"},
                        },
                    }
                ),
                encoding="utf-8",
            )

            self.assertEqual(
                parse_param_json(path),
                ("Titulo ES", "PPSA99999", "01.00"),
            )

    def test_get_game_info_uses_param_json_and_pfs_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sce_sys = root / "sce_sys"
            sce_sys.mkdir()
            (root / "param.json").write_text(
                json.dumps(
                    {
                        "titleId": "PPSA00001",
                        "version": "01.00",
                        "titleName": "Sample Game",
                    }
                ),
                encoding="utf-8",
            )
            (sce_sys / "pfs-version.dat").write_text("1.007.000\n", encoding="utf-8")

            self.assertEqual(
                get_game_info(root),
                ("Sample Game", "PPSA00001", "01.007.000"),
            )


if __name__ == "__main__":
    unittest.main()
