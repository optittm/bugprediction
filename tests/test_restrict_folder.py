import unittest
from unittest.mock import MagicMock, Mock
from utils.restrict_folder import RestrictFolder
from configuration import Configuration
from models.version import Version

class TestRestrictFolder(unittest.TestCase):

    def setUp(self):
        self.v1 = MagicMock(spec=Version)
        self.v1.name = "1.0.0"
        self.v1.tag = "v1.0.0"
        self.v2 = MagicMock(spec=Version)
        self.v2.name = "2.0.0"
        self.v2.tag = "v2.0.0"
        self.v3 = MagicMock(spec=Version)
        self.v3.name = "2.1.0"
        self.v3.tag = "v2.1.0"
        self.versions = [
            self.v1, self.v2, self.v3
        ]
        self.configuration = MagicMock(
            include_folders={
                "*": [],
                ">1.0.0": ["foo", "bar"],
                "==2.1.0": ["baz"]
            },
            exclude_folders={
                "*": [],
                "<2.1.0": ["qux"]
            }
        )
        self.rf = RestrictFolder(self.versions, self.configuration)

    def test_get_include_folders(self):
        self.assertListEqual(self.rf.get_include_folders(self.v1), [])
        self.assertListEqual(sorted(self.rf.get_include_folders(self.v2)), sorted(["foo", "bar"]))
        self.assertListEqual(sorted(self.rf.get_include_folders(self.v3)), sorted(["foo", "bar", "baz"]))

    def test_get_exclude_folders(self):
        print(self.rf.exclude_folders)
        self.assertListEqual(self.rf.get_exclude_folders(self.v1), ["qux"])
        self.assertListEqual(self.rf.get_exclude_folders(self.v2), ["qux"])
        self.assertListEqual(self.rf.get_exclude_folders(self.v3), [])