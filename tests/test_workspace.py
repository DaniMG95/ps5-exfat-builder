import unittest

from ps5_exfat_builder.services.workspace import create_workspace


class WorkspaceTests(unittest.TestCase):
    def test_workspace_creates_and_cleans_temp_dir(self):
        with create_workspace("ps5_builder_test_") as workspace:
            root = workspace.root
            nested = workspace.mkdir("stage", "game")
            self.assertTrue(root.exists())
            self.assertTrue(nested.exists())

        self.assertFalse(root.exists())


if __name__ == "__main__":
    unittest.main()
