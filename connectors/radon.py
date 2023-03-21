
import logging
import os
import timeit

from models.metric import Metric
from radon.complexity import cc_visit, average_complexity
from radon.raw import analyze, Module
from radon.metrics import h_visit, HalsteadReport
from radon.visitors import Function, Class


class RadonConnector:
    """
    Classe qui permet de calculer des métriques de code à l'aide de la bibliothèque Radon.
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
        halstead_h1: List[int]
            Number of distinct operators.
        halstead_h2: List[int]
            Number of distinct operands.
        halstead_n1: List[int]
            Total number of operators.
        halstead_n2: List[int]
            Total number of operands.
        halstead_vocabulary: List[int]
            Vocabulary of the program.
        halstead_length: List[int]
            Program length.
        halstead_calculated_length: List[int]
            Program calculated length.
        halstead_volume: List[int]
            Program volume.
        halstead_difficulty: List[int]
            Program difficulty.
        halstead_effort: List[int]
            Program effort.
        halstead_time: List[float]
            Estimated time to write the program.
        halstead_bugs: List[float]
            Estimated number of bugs.
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
        self.simgle_comment = []                
        self.halstead_h1 = []                   
        self.halstead_h2 = []                   
        self.halstead_n1 = []                   
        self.halstead_n2 = []                   
        self.halstead_vocabulary = []           
        self.halstead_length = []               
        self.halstead_calculated_length = []    
        self.halstead_volume = []               
        self.halstead_difficulty = []           
        self.halstead_effort = []               
        self.halstead_time = []                 
        self.halstead_bugs = []                 
        self.noc = []                           
        self.nom = []                           
        self.nof = []                           
        self.class_loc = []                     
        self.method_loc = []                    
        self.func_loc = []                      

    @timeit
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
        if (self.config.language != "Python"):
            logging.info('RADON is only used for Python language')
        else:
            if (not metric.radon_cc_total):
                self.compute_metrics(metric)

    def compute_metrics(self, metric) -> None:
        """
        Computes the software metrics for the Python codebase.

        Args:
        - metric: The Metric object for the version in the database.

        Returns:
        - None.
        """
        for root, dirs, files in os.walk(self.directory):
            for file in files:
                file_path = os.path.join(root, file)
                if (self.is_python_file(file)):
                    with open(file_path, "r") as file:
                        code = file.read()

                    cc_metrics = cc_visit(code)
                    raw_metrics = analyze(code)
                    h_metrics = h_visit(code)

                    self.avg_cc.append(average_complexity(cc_metrics))
                    self.__compute_cc_metrics(cc_metrics)
                    self.__compute_raw_metrics(raw_metrics)
                    self.__compute_halstead_metrics(h_metrics)
        logging.info('Adding Radon analysis for this version')
        self.__store_metrics(metric)


    def __compute_cc_metrics(self, cc_metrics) -> None:
        """
        Computes the Cyclomatic Complexity metrics using the Radon library.

        Args:
        - cc_metrics: The Cyclomatic Complexity metrics object returned by the Radon library.

        Returns:
        - None.
        """
        if (cc_metrics.len() > 0):
            noc = 0
            nom = 0
            nof = 0
            for metric in cc_metrics:
                if (isinstance(metric, Function)):
                    # is methode metrics
                    if (metric.is_method):
                        nom = nom + 1
                        self.method_loc.add(metric.endline - metric.lineno)
                    # is function metrics
                    else:
                        nof = nof + 1
                        self.func_loc.append(metric.endline - metric.lineno)
                        self.cc.append(metric.complexity)
                # is class metrics
                elif (isinstance(metric, Class)):
                    noc = noc + 1
                    self.class_loc.append(metric.endline - metric.lineno)
                    # compute methodes metrics
                    self.__compute_cc_metrics(metric.methods)
                    # compute inner class metrics
                    self.__compute_cc_metrics(metric.inner_classes)
                    self.cc.append(metric.real_complexity)

            self.noc.append(noc)
            self.nom.append(nom)
            self.nof.append(nof)

    def __compute_raw_metrics(self, raw_metrics: Module) -> None:
        """
        Computes the Raw metrics using the Radon library.

        Args:
        - raw_metrics: The Raw metrics object returned by the Radon library.

        Returns:
        - None.
        """
        self.loc.append(raw_metrics.loc)
        self.lloc.append(raw_metrics.lloc)
        self.sloc.append(raw_metrics.sloc)
        self.comments.append(raw_metrics.comments)
        self.docstring.append(raw_metrics.multi)
        self.blank.append(raw_metrics.blank)
        self.simgle_comment.append(raw_metrics.single_comments)

    def __compute_halstead_metrics(self, h_metrics: HalsteadReport) -> None:
        """
        Computes the Halstead metrics using the Radon library.

        Args:
        - h_metrics: The Halstead metrics object returned by the Radon library.

        Returns:
        - None.
        """
        self.halstead_h1.append(h_metrics.h1)
        self.halstead_h2.append(h_metrics.h2)
        self.halstead_n1.append(h_metrics.N1)
        self.halstead_n2.append(h_metrics.N2)
        self.halstead_vocabulary.append(h_metrics.vocabulary)
        self.halstead_length.append(h_metrics.length)
        self.halstead_calculated_length.append(h_metrics.calculated_length)
        self.halstead_volume.append(h_metrics.volume)
        self.halstead_difficulty.append(h_metrics.difficulty)
        self.halstead_effort.append(h_metrics.effort)
        self.halstead_time.append(h_metrics.time)
        self.halstead_bugs.append(h_metrics.bugs)

    def __store_metrics(self, metric: Metric) -> None:
        """
        Calculates and stores various software metrics for a given `Metric` object.

        Args:
            metric (Metric): An instance of the `Metric` class to store the calculated metrics.

        Returns:
            None
        """
        metric.radon_cc_total = sum(self.cc)
        metric.radon_cc_avg = sum(self.cc) / self.cc.len()
        metric.radon_loc_total = sum(self.loc)
        metric.radon_loc_avg = sum(self.loc) / self.loc.len()
        metric.radon_lloc_total = sum(self.lloc)
        metric.radon_lloc_avg = sum(self.lloc) / self.lloc.len()
        metric.radon_sloc_total = sum(self.sloc)
        metric.radon_sloc_avg = sum(self.sloc) / self.sloc.len()
        metric.radon_comments_total = sum(self.comments)
        metric.radon_comments_avg = sum(self.comments) / self.comments.len()
        metric.radon_docstring_total = sum(self.docstring)
        metric.radon_docstring_avg = sum(self.docstring) / self.docstring.len()
        metric.radon_blank_total = sum(self.blank)
        metric.radon_blank_avg = sum(self.blank) / self.blank.len()
        metric.radon_single_comments_total = sum(self.simgle_comment)
        metric.radon_single_comments_avg = sum(self.simgle_comment) / self.simgle_comment.len()
        metric.radon_halstead_h1_total = sum(self.halstead_h1)
        metric.radon_halstead_h1_avg = sum(self.halstead_h1) / self.halstead_h1.len()
        metric.radon_halstead_h2_total = sum(self.halstead_h2)
        metric.radon_halstead_h2_avg = sum(self.halstead_h2) / self.halstead_h2.len()
        metric.radon_halstead_n1_total = sum(self.halstead_n1)
        metric.radon_halstead_n1_avg = sum(self.halstead_n1) / self.halstead_n1.len()
        metric.radon_halstead_n2_total = sum(self.halstead_n2)
        metric.radon_halstead_n2_avg = sum(self.halstead_n2) / self.halstead_n2.len()
        metric.radon_halstead_vocabulary_total = sum(self.halstead_vocabulary)
        metric.radon_halstead_vocabulary_avg = sum(self.halstead_vocabulary) / self.halstead_vocabulary.len()
        metric.radon_halstead_length_total = sum(self.halstead_length)
        metric.radon_halstead_length_avg = sum(self.halstead_length) / self.halstead_length.len()
        metric.radon_halstead_calculated_length_total = sum(self.halstead_calculated_length)
        metric.radon_halstead_calculated_length_avg = sum(self.halstead_calculated_length) / self.halstead_calculated_length.len()
        metric.radon_halstead_volume_total = sum(self.halstead_volume)
        metric.radon_halstead_volume_avg = sum(self.halstead_volume) / self.halstead_volume.len()
        metric.radon_halstead_difficulty_total = sum(self.halstead_difficulty)
        metric.radon_halstead_difficulty_avg = sum(self.halstead_difficulty) / self.halstead_difficulty.len()
        metric.radon_halstead_effort_total = sum(self.halstead_effort)
        metric.radon_halstead_effort_avg = sum(self.halstead_effort) / self.halstead_effort.len()
        metric.radon_halstead_time_total = sum(self.halstead_time)
        metric.radon_halstead_time_avg = sum(self.halstead_time) / self.halstead_time.len()
        metric.radon_halstead_bugs_total = sum(self.halstead_bugs)
        metric.radon_halstead_bugs_avg = sum(self.halstead_bugs) / self.halstead_bugs.len()
        metric.radon_noc_total = sum(self.noc)
        metric.radon_noc_avg = sum(self.noc) / self.noc.len()
        metric.radon_nom_total = sum(self.nom)
        metric.radon_nom_avg = sum(self.nom) / self.nom.len()
        metric.radon_nof_total = sum(self.nof)
        metric.radon_nof_avg = sum(self.nof) / self.nof.len()
        metric.radon_class_loc_total = sum(self.class_loc)
        metric.radon_class_loc_avg = sum(self.class_loc) / self.class_loc.len()
        metric.radon_method_loc_total = sum(self.method_loc)
        metric.radon_method_loc_avg = sum(self.method_loc) / self.method_loc.len()
        metric.radon_func_loc_total = sum(self.func_loc)
        metric.radon_func_loc_avg = sum(self.func_loc) / self.func_loc.len()
        

    def is_python_file(file_name) -> bool:
        """
        Checks if a given file name corresponds to a Python file.

        Args:
            file_name (str): The name of the file to check.

        Returns:
            bool: `True` if the file name corresponds to a Python file, `False` otherwise.
        """
        extension = file_name.split('.')[-1].lower()
        # Vérifier si l'extension correspond à un fichier Python
        return extension == 'py'
