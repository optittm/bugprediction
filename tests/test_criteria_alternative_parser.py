import unittest
from exceptions.topsis_configuration import InvalidAlternativeError, InvalidCriterionError, MissingWeightError, NoAlternativeProvidedError, NoCriteriaProvidedError

# Import the classes to test
from utils.criterion import CriterionParser
from utils.alternatives import AlternativesParser

class TestCriterionParser(unittest.TestCase):

    def setUp(self):
        self.parser = CriterionParser()

    def test_parse_criteria_valid(self):
        criteria_names = ['bugs']
        weights = [0.5]
        parsed_criteria = self.parser.parse_criteria(criteria_names, weights)

        # Ensure the correct number of criteria are parsed
        self.assertEqual(len(parsed_criteria), 1)
        # Ensure the parsed criterion has the correct weight
        self.assertEqual(parsed_criteria[0].get_weight(), 0.5)

    def test_parse_criteria_invalid_name(self):
        criteria_names = ['bugs', 'invalid_criterion']
        weights = [0.5, 0.7]
        
        with self.assertRaises(InvalidCriterionError):
            self.parser.parse_criteria(criteria_names, weights)

    def test_parse_criteria_missing_weight(self):
        criteria_names = ['bugs']
        weights = []
        
        with self.assertRaises(MissingWeightError):
            self.parser.parse_criteria(criteria_names, weights)

    def test_parse_criteria_no_criteria_provided(self):
        criteria_names = []
        weights = []
        
        with self.assertRaises(NoCriteriaProvidedError):
            self.parser.parse_criteria(criteria_names, weights)

class TestAlternativesParser(unittest.TestCase):

    def setUp(self):
        self.parser = AlternativesParser()

    def test_parse_alternatives_valid(self):
        alternatives_names = ['bug_velocity', 'changes', 'legacy_files']
        parsed_alternatives = self.parser.parse_alternatives(alternatives_names)

        # Ensure the correct number of alternatives are parsed
        self.assertEqual(len(parsed_alternatives), 3)

    def test_parse_alternatives_invalid_name(self):
        alternatives_names = ['bug_velocity', 'invalid_alternative', 'changes']
        
        with self.assertRaises(InvalidAlternativeError):
            self.parser.parse_alternatives(alternatives_names)

    def test_parse_alternatives_no_alternatives_provided(self):
        alternatives_names = []
        
        with self.assertRaises(NoAlternativeProvidedError):
            self.parser.parse_alternatives(alternatives_names)

if __name__ == '__main__':
    unittest.main()