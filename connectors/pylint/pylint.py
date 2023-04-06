
import glob
from io import StringIO
import logging

from connectors.pylint.custom_ast_checker import CustomAstChecker
from connectors.pylint.custom_linter import CustomLinter
from connectors.pylint.custom_reporter import CustomReporter
from connectors.pylint.cheacker_metrics_model import CheckerData

from models.metric import Metric

class PylintConnector:
    """
    The PylintConnector class is used to analyze Python source code using the PyLint library, and retrieve various metrics related to the code quality. 
    """

    def __init__(self, directory, version, session, config) -> None:
        """
        The PylintConnector class is used to analyze Python source code using the PyLint library, and retrieve various metrics related to the code quality. 

        Attributes:
            directory (str): the path to the directory containing the Python source code to analyze.
            version (str): the version of the Python source code.
            session: the current database session.
            config: the current configuration.
        """

        # Global config
        self.directory = directory
        self.version = version
        self.session = session
        self.config = config

        # Metrics
        self.score = 0
        self.code = 0
        self.code_avg = 0
        self.docstring = 0
        self.docstring_avg = 0
        self.comment = 0
        self.comment_avg = 0
        self.blank = 0
        self.blank_avg = 0
        self.nmodule = 0
        self.noc = 0
        self.nom = 0
        self.nof = 0
        self.dup_line = 0
        self.num_msg = 0
        self.module_comment_avg = 0
        self.class_comment_avg = 0
        self.methode_comment_avg = 0
        self.function_comment_avg = 0

    def analyze_source_code(self) -> None:
        """
        Analyzes the source code of the repository using PyLint to calculate code quality metrics.

        Args: 
            None

        Returns:
            None
        """
        logging.info('PyLint::analyze_repo')
        metric = self.session.query(Metric).filter(Metric.version_id == self.version.version_id).first()
        if (not metric):
            metric = Metric()
        
        # TODO it will maybe need to be updated
        if (self.config.language.lower() != "python"):
            logging.info('PyLint is only used for Python language')
        else:
            if (not metric.pylint_score):
                self.compute_metrics(metric)
            else:
                logging.info('PyLint analysis already done for this version, version: ' + str(self.version.version_id))

    def compute_metrics(self, metric: Metric) -> None:
        """
        Calculates code quality metrics for the source code using PyLint.

        Args: 
            metric (Metric): A Metric object representing the current version's metrics.

        Returns:
            None
        """
        # Create a custom reporter
        reporter = CustomReporter()
        # Create a custom linter
        linter = CustomLinter(reporter=reporter)
        # Bind the checkers to the linter
        linter.register_checker(CustomAstChecker(linter=linter))

        python_files = glob.glob(self.directory + '/**/*.py', recursive=True)

        # Start the analyse
        linter.check(python_files)
        # Generate the report
        linter.generate_reports()

        # Store the metrics
        self.__store_metrics(metric, linter.metrics)

    def __store_metrics(self, metric: Metric, data: CheckerData) -> None:
        """
        Stores the pylint metrics in the given Metric object and adds it to the current session.

        Args:
            metric (Metric): The Metric object to store the pylint metrics in.

        Returns:
            None.
        """
        metric.pylint_cbo = data.cbo
        metric.pylint_fan_out = data.fan_out
        metric.pylint_dit = data.dit
        metric.pylint_noc = data.noc
        metric.pylint_nom = data.nom
        metric.pylint_nof = data.nof
        metric.pylint_num_field = data.num_field
        metric.pylint_num_returns = data.num_returns
        metric.pylint_num_loops = data.num_loops
        metric.pylint_num_comparisons = data.num_comparisons
        metric.pylint_num_try_except = data.num_try_except
        metric.pylint_num_str_literals = data.num_str_literals
        metric.pylint_num_numbers = data.num_numbers
        metric.pylint_num_math_op = data.num_math_op
        metric.pylint_num_variable = data.num_variable
        metric.pylint_num_inner_cls_and_lambda = data.num_inner_cls_and_lambda
        metric.pylint_num_docstring = data.num_docstring
        metric.pylint_num_import = data.num_import
        metric.pylint_lcc = data.lcc

        self.session.add(metric)
        self.session.commit()