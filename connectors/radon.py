
import logging
import os

from models.metric import Metric
from radon.complexity import cc_visit, average_complexity
from radon.raw import analyze, Module
from radon.visitors import Function, Class
from statistics import mean

from utils.math import Math
from utils.proglang import is_python_file


class RadonConnector:
    """
    Class that allows calculating code metrics using the Radon library.
    """

    def __init__(self, directory, version, session, config) -> None:
        """
        Connector to Radon library to compute metrics.
    
        Attributes:
        -----------
        directory: str
            Directory path containing source code files.
        version: str
            Version number of the code.
        session: requests.Session
            Session object to use to acces the bd.
        config: Dict[str, Any]
            Configuration options for the connector.
        
        Metrics:
        --------
        cc: List[float]
            Cyclomatic complexity.
        avg_cc: List[float]
            Radon's average Cyclomatic complexity.
        loc: List[int]
            Total lines of code.
        lloc: List[int]
            Logical lines of code.
        sloc: List[int]
            Source lines of code.
        comments: List[int]
            Total number of comments.
        docstring: List[int]
            Total number of docstrings.
        blank: List[int]
            Total number of blank lines.
        single_comment: List[int]
            Total number of single-line comments.
        noc: List[int]
            Number of classes.
        nom: List[int]
            Number of methods.
        nof: List[int]
            Number of functions.
        class_loc: List[int]
            Lines of code for classes.
        method_loc: List[int]
            Lines of code for methods.
        func_loc: List[int]
            Lines of code for functions.
        """
        # Global config
        self.directory = directory
        self.version = version
        self.session = session
        self.config = config
        # Metrics
        self.cc = []                            
        self.avg_cc = []                        
        self.loc = []
        self.lloc = []                          
        self.sloc = []                          
        self.comments = []                      
        self.docstring = []                     
        self.blank = []                         
        self.single_comment = []                     
        self.noc = []                           
        self.nom = []                           
        self.nof = []                           
        self.class_loc = []                     
        self.method_loc = []                    
        self.func_loc = []        
        # calcule
        self.calcul_noc = 0
        self.calcul_nom = 0
        self.calcul_nof = 0              

    def analyze_source_code(self) -> None:
        """
        Analyzes the Python source code using the Radon library.

        Args:
        - None.

        Returns:
        - None.
        """
        
        logging.info('RADON::analyze_repo')
        metric = self.session.query(Metric).filter(Metric.version_id == self.version.version_id).first()
        if (not metric):
            metric = Metric()
        
        # TODO it will maybe need to be updated
        logging.info('RADON self.config.language = ' + self.config.language)
        if (self.config.language.lower() != "python"):
            logging.info('RADON is only used for Python language')
        else:
            if (not metric.radon_cc_total):
                self.compute_metrics()
                self.__store_metrics(metric)
            else:
                logging.info('RADON analysis already done for this version, version: ' + str(self.version.version_id))

    def compute_metrics(self) -> None:
        """
        Computes the software metrics for the Python codebase.

        Args:
        - None

        Returns:
        - None.
        """
        for root, dirs, files in os.walk(self.directory):
            for file in files:
                file_path = os.path.join(root, file)
                if (is_python_file(file)):
                    with open(file_path, "r", encoding="utf-8") as file:
                        code = file.read()

                    # Recovery of radon metrics
                    cc_metrics = cc_visit(code)
                    raw_metrics = analyze(code)

                    # Processing of recovered metrics
                    self.avg_cc.append(average_complexity(cc_metrics))
                    self.__compute_cc_metrics(cc_metrics)
                    self.__compute_raw_metrics(raw_metrics)
        logging.info('Adding Radon analysis for this version, version: ' + str(self.version.version_id))


    def __compute_cc_metrics(self, cc_metrics) -> None:

            self.__calcule_cc_metrics(cc_metrics)
            self.noc.append(self.calcul_noc)
            self.nom.append(self.calcul_nom)
            self.nof.append(self.calcul_nof)

    def __calcule_cc_metrics(self, cc_metrics) -> None:
        """
        Computes the Cyclomatic Complexity metrics using the Radon library.

        Args:
        - cc_metrics: The Cyclomatic Complexity metrics object returned by the Radon library.

        Returns:
        - None.
        """
        for metric in cc_metrics:
            if (isinstance(metric, Function)):
                # is methode metrics
                if (metric.is_method):
                    self.calcul_nom = self.calcul_nom + 1
                    self.method_loc.append(metric.endline - metric.lineno)
                # is function metrics
                else:
                    self.calcul_nof = self.calcul_nof + 1
                    self.func_loc.append(metric.endline - metric.lineno)
                    self.cc.append(metric.complexity)
            # is class metrics
            elif (isinstance(metric, Class)):
                self.calcul_noc = self.calcul_noc + 1
                self.class_loc.append(metric.endline - metric.lineno)
                # calcule methodes metrics
                self.__calcule_cc_metrics(metric.methods)
                # calcule inner class metrics
                self.__calcule_cc_metrics(metric.inner_classes)
                self.cc.append(metric.real_complexity)
            else:
                raise TypeError("Unsupported RADON type")

    def __compute_raw_metrics(self, raw_metrics: Module) -> None:
        """
        Computes the Raw metrics using the Radon library.

        Args:
        - raw_metrics: The Raw metrics object returned by the Radon library.

        Returns:
        - None.
        """
        try:
            self.loc.append(raw_metrics.loc)
            self.lloc.append(raw_metrics.lloc)
            self.sloc.append(raw_metrics.sloc)
            self.comments.append(raw_metrics.comments)
            self.docstring.append(raw_metrics.multi)
            self.blank.append(raw_metrics.blank)
            self.single_comment.append(raw_metrics.single_comments)
        except AttributeError:
            raise TypeError("Unsupported RADON type")

    def __store_metrics(self, metric: Metric) -> None:
        """
        Calculates and stores various software metrics for a given `Metric` object.

        Args:
            metric (Metric): An instance of the `Metric` class to store the calculated metrics.

        Returns:
            None
        """
        metric.radon_cc_total = sum(self.cc)
        metric.radon_cc_avg = Math.get_mean_safe(self.cc)
        metric.radon_loc_total = sum(self.loc)
        metric.radon_loc_avg = Math.get_mean_safe(self.loc)
        metric.radon_lloc_total = sum(self.lloc)
        metric.radon_lloc_avg = Math.get_mean_safe(self.lloc)
        metric.radon_sloc_total = sum(self.sloc)
        metric.radon_sloc_avg = Math.get_mean_safe(self.sloc)
        metric.radon_comments_total = sum(self.comments)
        metric.radon_comments_avg = Math.get_mean_safe(self.comments)
        metric.radon_docstring_total = sum(self.docstring)
        metric.radon_docstring_avg = Math.get_mean_safe(self.docstring)
        metric.radon_blank_total = sum(self.blank)
        metric.radon_blank_avg = Math.get_mean_safe(self.blank)
        metric.radon_single_comments_total = sum(self.single_comment)
        metric.radon_single_comments_avg = Math.get_mean_safe(self.single_comment)
        metric.radon_noc_total = sum(self.noc)
        metric.radon_noc_avg = Math.get_mean_safe(self.noc)
        metric.radon_nom_total = sum(self.nom)
        metric.radon_nom_avg = Math.get_mean_safe(self.nom)
        metric.radon_nof_total = sum(self.nof)
        metric.radon_nof_avg = Math.get_mean_safe(self.nof)
        metric.radon_class_loc_total = sum(self.class_loc)
        metric.radon_class_loc_avg = Math.get_mean_safe(self.class_loc)
        metric.radon_method_loc_total = sum(self.method_loc)
        metric.radon_method_loc_avg = Math.get_mean_safe(self.method_loc)
        metric.radon_func_loc_total = sum(self.func_loc)
        metric.radon_func_loc_avg = Math.get_mean_safe(self.func_loc)
        
        # Save metrics values into the database
        self.session.add(metric)
        self.session.commit()
