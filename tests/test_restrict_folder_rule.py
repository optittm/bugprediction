
import unittest

import semver

from utils.restrict_folder import BaseRule, BaseSemVer, BornedRule, DefaultRule, DefaultSemVer, OperatorRule, SemVersion

class TestBaseSemVer(unittest.TestCase):
    
    def test_coerce_invalid(self):
        invalid_str = "invalid"
        ver, rest = BaseSemVer.coerce(invalid_str)
        self.assertIsNone(ver)
        self.assertEqual(rest, invalid_str)

    def test_coerce_malformed(self):
        malformed_str = "v1 a"
        ver, rest = BaseSemVer.coerce(malformed_str)
        self.assertIsNotNone(ver)
        self.assertEqual(str(ver), "1.0.0")
        self.assertIsNotNone(rest)

    def test_coerce_valid(self):
        valid_str = "1.0.0"
        ver, rest = BaseSemVer.coerce(valid_str)
        self.assertIsNotNone(ver)
        self.assertEqual(str(ver), valid_str)
        self.assertEqual(rest, "")

    def test_parse_invalid(self):
        invalid_str = "invalid"
        ver = BaseSemVer.parse(invalid_str)
        self.assertIsInstance(ver, DefaultSemVer)
        self.assertEqual(ver.version, "*")

    def test_parse_default(self):
        invalid_str = "*"
        ver = BaseSemVer.parse(invalid_str)
        self.assertIsInstance(ver, DefaultSemVer)
        self.assertEqual(ver.version, "*")
    
    def test_parse_malformed(self):
        invalid_str = "v1 a"
        ver = BaseSemVer.parse(invalid_str)
        self.assertIsInstance(ver, SemVersion)
        self.assertEqual(str(ver.version), "1.0.0")

    def test_parse_valid(self):
        invalid_str = "1.0.0"
        ver = BaseSemVer.parse(invalid_str)
        self.assertIsInstance(ver, SemVersion)
        self.assertEqual(str(ver.version), "1.0.0")

class TestSemVersion(unittest.TestCase):

    def test_init_bad_type(self):
        input = ["1.0.0"]
        with self.assertRaises(TypeError):
            SemVersion(input)

    def test_init_invalid(self):
        input = "invalid"
        with self.assertRaises(ValueError):
            SemVersion(input)

    def test_init_malformed(self):
        input = "v1 a"
        ver = SemVersion(input)
        self.assertEqual(str(ver.version), "1.0.0")

    def test_init_valid(self):
        input = "1.0.0"
        ver = SemVersion(input)
        self.assertEqual(str(ver.version), "1.0.0")
        
class TestDefaultSemVer(unittest.TestCase):
        # No test needded
        pass

class TestBaseRule(unittest.TestCase):

    def test_parse_invalid(self):
        input = "invalid"
        ver = BaseRule.parse(input)
        self.assertIsInstance(ver, DefaultRule)

    def test_parse_default(self):
        input = "*"
        ver = BaseRule.parse(input)
        self.assertIsInstance(ver, DefaultRule)

    def test_parse_malformed(self):
        input = "v1 a"
        ver = BaseRule.parse(input)
        self.assertIsInstance(ver, OperatorRule)

    def test_parse_valid_operator(self):
        input = ">=1.0.0"
        ver = BaseRule.parse(input)
        self.assertIsInstance(ver, OperatorRule)

    def test_parse_ambigous_op_rule(self):
        input = ">=1.0.0,2.0.0"
        ver = BaseRule.parse(input)
        self.assertIsInstance(ver, OperatorRule)
        self.assertEqual(str(ver.version), "1.0.0")

    def test_parse_ambigous_borned_rule(self):
        input = "[[1.0.0,2.0.0"
        ver = BaseRule.parse(input)
        self.assertIsInstance(ver, BornedRule)

class TestOperatorRule(unittest.TestCase):

    def test_init_invalid(self):
        input = "invalid"
        with self.assertRaises(ValueError):
            OperatorRule(input)

    def test_init_malformed_without_op(self):
        input = "v1 a"
        ver = OperatorRule(input)
        self.assertEqual(ver.operator, "==")
        self.assertEqual(str(ver.version), "1.0.0")

    def test_init_malformed_with_op(self):
        input = "<=v1 a"
        ver = OperatorRule(input)
        self.assertEqual(ver.operator, "<=")
        self.assertEqual(str(ver.version), "1.0.0")

    def test_init_valid_without_op(self):
        input = "1.0.0"
        ver = OperatorRule(input)
        self.assertEqual(ver.operator, "==")
        self.assertEqual(str(ver.version), "1.0.0")

    def test_init_valid_with_op(self):
        input = "<=1.0.0"
        ver = OperatorRule(input)
        self.assertEqual(ver.operator, "<=")
        self.assertEqual(str(ver.version), "1.0.0")

    def test_match_false(self):
        rule = OperatorRule("<1.0.0")
        ver = SemVersion("1.0.0")
        self.assertFalse(rule.match(ver))

    def test_match_True(self):
        rule = OperatorRule("<1.0.0")
        ver = SemVersion("0.9.0")
        self.assertTrue(rule.match(ver))

class TestBornedRule(unittest.TestCase):

    def test_init_invalid(self):
        input = "invalid"
        with self.assertRaises(ValueError):
            BornedRule(input)

    def test_init_malformed_without_op(self):
        input = "v3 a, v1 b"
        rule = BornedRule(input)
        self.assertEqual(str(rule.lower), "1.0.0")
        self.assertEqual(str(rule.upper), "3.0.0")
        self.assertEqual(rule.operator, "[]")

    def test_init_malformed_with_op(self):
        input = "][v3 a, v1 b"
        rule = BornedRule(input)
        self.assertEqual(str(rule.lower), "1.0.0")
        self.assertEqual(str(rule.upper), "3.0.0")
        self.assertEqual(rule.operator, "][")

    def test_init_valid_without_op(self):
        input = "1.0.0, 3.0.0"
        rule = BornedRule(input)
        self.assertEqual(str(rule.lower), "1.0.0")
        self.assertEqual(str(rule.upper), "3.0.0")
        self.assertEqual(rule.operator, "[]")

    def test_init_valid_with_op(self):
        input = "][1.0.0, 3.0.0"
        rule = BornedRule(input)
        self.assertEqual(str(rule.lower), "1.0.0")
        self.assertEqual(str(rule.upper), "3.0.0")
        self.assertEqual(rule.operator, "][")

    def test_match_false(self):
        rule = BornedRule("]]1.0.0, 2.0.0")
        ver = SemVersion("1.0.0")
        self.assertFalse(rule.match(ver))

    def test_match_True(self):
        rule = BornedRule("[]1.0.0, 2.0.0")
        ver = SemVersion("1.0.0")
        self.assertTrue(rule.match(ver))