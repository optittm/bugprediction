
import unittest

import semver

from utils.restrict_folder import Rule

class TestRule(unittest.TestCase):
    
    def test_init_malformed(self):
        r1 = Rule("invalid")
        self.assertEqual(r1.operator, "*")
        self.assertEqual(r1.semver, "*")

    def test_init_semver_wildcard(self):
        r1 = Rule("*")
        self.assertEqual(r1.operator, "*")
        self.assertEqual(r1.semver, "*")

    def test_init_semver_exact(self):
        r1 = Rule(">=1.2.3")
        self.assertEqual(r1.operator, ">=")
        self.assertEqual(r1.semver.major, 1)
        self.assertEqual(r1.semver.minor, 2)
        self.assertEqual(r1.semver.patch, 3)

    def test_match(self):
        r1 = Rule(">1.2.3")
        r2 = Rule(">=1.2.4")
        r3 = Rule("<1.2.4")
        r4 = Rule("<=1.2.4")
        r5 = Rule("==1.2.4")
        r6 = Rule("!=1.2.4")
        r7 = Rule("*")

        v1 = semver.Version.parse("1.2.3")
        v2 = semver.Version.parse("1.2.4")
        v3 = semver.Version.parse("1.2.5")

        # test >
        self.assertFalse(r1.match(v1))
        self.assertTrue(r1.match(v2))
        self.assertTrue(r1.match(v3))
        # test >=
        self.assertFalse(r2.match(v1))
        self.assertTrue(r2.match(v2))
        self.assertTrue(r2.match(v3))
        # test <
        self.assertTrue(r3.match(v1))
        self.assertFalse(r3.match(v2))
        self.assertFalse(r3.match(v3))
        # test <=
        self.assertTrue(r4.match(v1))
        self.assertTrue(r4.match(v2))
        self.assertFalse(r4.match(v3))
        # test ==
        self.assertFalse(r5.match(v1))
        self.assertTrue(r5.match(v2))
        self.assertFalse(r5.match(v3))
        # test !=
        self.assertTrue(r6.match(v1))
        self.assertFalse(r6.match(v2))
        self.assertTrue(r6.match(v3))
        # test *
        self.assertTrue(r7.match(v1))
        self.assertTrue(r7.match(v2))
        self.assertTrue(r7.match(v3))