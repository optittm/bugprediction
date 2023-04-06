import unittest
from unittest.mock import MagicMock
from models.metric import Metric
from utils.config import Config
from connectors.pylint_connector import PylintConnector

class TestPylintConnector(unittest.TestCase):

    def setUp(self):
        self.config = Config("config_test.json")
        self.version = MagicMock()
        self.version.version_id = 1234
        self.metric = Metric()
        self.metric.version_id = self.version.version_id
        self.metric.pylint_score = 0
        self.session = MagicMock()
        self.session.query.return_value.filter.return_value.first.return_value = None
        self.pylint_connector = PylintConnector("test_directory", self.version, self.session, self.config)

    def test_init(self):
        self.assertEqual(self.pylint_connector.directory, "test_directory")
        self.assertEqual(self.pylint_connector.version, self.version)
        self.assertEqual(self.pylint_connector.session, self.session)
        self.assertEqual(self.pylint_connector.config, self.config)
        self.assertEqual(self.pylint_connector.score, 0)
        self.assertEqual(self.pylint_connector.code, 0)
        self.assertEqual(self.pylint_connector.code_avg, 0)
        self.assertEqual(self.pylint_connector.docstring, 0)
        self.assertEqual(self.pylint_connector.docstring_avg, 0)
        self.assertEqual(self.pylint_connector.comment, 0)
        self.assertEqual(self.pylint_connector.comment_avg, 0)
        self.assertEqual(self.pylint_connector.blank, 0)
        self.assertEqual(self.pylint_connector.blank_avg, 0)
        self.assertEqual(self.pylint_connector.nmodule, 0)
        self.assertEqual(self.pylint_connector.noc, 0)
        self.assertEqual(self.pylint_connector.nom, 0)
        self.assertEqual(self.pylint_connector.nof, 0)
        self.assertEqual(self.pylint_connector.dup_line, 0)
        self.assertEqual(self.pylint_connector.num_msg, 0)
        self.assertEqual(self.pylint_connector.module_comment_avg, 0)
        self.assertEqual(self.pylint_connector.class_comment_avg, 0)
        self.assertEqual(self.pylint_connector.methode_comment_avg, 0)
        self.assertEqual(self.pylint_connector.function_comment_avg, 0)

    def test_analyze_source_code_language_not_python(self):
        self.pylint_connector.config.language = "java"
        self.pylint_connector.analyze_source_code()
        self.assertEqual(self.session.query.call_count, 0)
        self.assertEqual(self.pylint_connector.score, 0)

    def test_analyze_source_code_metric_not_calculated(self):
        self.session.query.return_value.filter.return_value.first.return_value = None
        self.pylint_connector.compute_metrics = MagicMock()
        self.pylint_connector.analyze_source_code()
        self.pylint_connector.compute_metrics.assert_called_once_with(self.metric)
        self.session.add.assert_called_once_with(self.metric)
        self.session.commit.assert_called_once()
        self.assertEqual(self.pylint_connector.score, self.metric.pylint_score)

    def test_analyze_source_code_metric_already_calculated(self):
        self.session.query.return_value.filter.return_value.first.return_value = self.metric
        self.pylint_connector.compute_metrics = MagicMock()
        self.pylint_connector.analyze_source_code()
        self.pylint_connector.compute_metrics.assert_not_called()
        self.assertEqual(self.pylint_connector.score, self.metric.pylint_score)