
import glob
import logging
import os
import re
import subprocess

from models.metric import Metric
from utils.proglang import is_python_file

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
        # We need to extract each file
        python_files = glob.glob(self.directory + '/**/*.py', recursive=True)

        # We need to use subprocess or we cannot retrive the output
        # We need the output to be in text format or we cannot retrive the raw metrics
        output = subprocess.run(['pylint', "--output-format=text", "--report=yes"] + python_files, capture_output=True, text=True)
        
        # Parse the pylint output to a dictionnary
        output_dict = self.__parse(output.stdout)
        # Compute the metrics
        self.__compute_metrics(output_dict)

        # Store the metrics
        self.__store_metrics(metric)

    def __parse(self, output):
        """
        Parses the output of pylint and extracts relevant data. The output is expected to be in a specific format with various sections separated by headers.

        Args:
            output (str): The output of a code analysis tool.

        Returns:
            dict: A dictionary containing the extracted data. The dictionary has the following keys:
                - "messages": a list of dictionaries containing information about each code analysis message.
                - "statistics": a dictionary containing various statistics about the code, organized by category.
                - "raw_metrics": a dictionary containing raw metrics about the code, organized by code type.
                - "messages_by_category": a dictionary containing information about the number of messages in each category.
                - "duplication": a dictionary containing information about code duplication.
                - "other": a dictionary containing miscellaneous data such as the number of statements, the number of lines of code, and the code's score.
        """
        messages = []
        stats = {}
        raw_metrics = {}
        messages_by_category = {}
        duplication = {}
        other = {}
        
        # Extract messages
        message_regex = r"^(.+?):(\d+):\d+: (\S+): (.+)$"
        for line in output.splitlines():
            match = re.match(message_regex, line)
            if match:
                filepath, lineno, category, message = match.groups()
                messages.append({
                    "filepath": filepath,
                    "lineno": int(lineno),
                    "category": category,
                    "message": message
                })
        
        # Extract statistics
        stats_regex = r"\|(\w*)\s*\|(\d*)\s*\|(\S*)\s*\|(\S*)\s*\|(\S*)\s*\|(\S*)\s*\|"
        stats_started = False
        for line in output.splitlines():
            if stats_started:
                match = re.match(stats_regex, line)
                if match:
                    category, number, old_number, difference, pct_documented, pct_badname = match.groups()
                    stats[category] = {
                        "number": int(number),
                        "old_number": old_number,
                        "difference": difference,
                        "%documented": float(pct_documented),
                        "%badname": float(pct_badname)
                    }
            elif line == "Statistics by type":
                stats_started = True
        
        # Extract raw metrics
        raw_metrics_regex = r"\|(\w*)\s*\|(\d*)\s*\|(\S*)\s*\|(\S*)\s*\|(\S*)\s*\|"
        raw_metrics_started = False
        for line in output.splitlines():
            if raw_metrics_started:
                match = re.match(raw_metrics_regex, line)
                if match:
                    code_type, number, pct, previous, difference = match.groups()
                    raw_metrics[code_type] = {
                        "number": int(number),
                        "%": float(pct),
                        "previous": previous,
                        "difference": difference
                    }
            elif line == "Raw metrics":
                raw_metrics_started = True

        # Extract duplication
        duplication_regex = r"\|(\w+\s\w+\s\w+)\s*\|(\S*)\s*\|(\S*)\s*\|(\S*)\s*\|"
        duplication_started = False
        for line in output.splitlines():
            if duplication_started:
                match = re.match(duplication_regex, line)
                if (match):
                    code, now, prev, diff = match.groups()
                    duplication[code[0:len(code) - 1].replace(" ", "_")] = {
                        "now": now,
                        "previous": prev,
                        "difference": diff
                    }
            elif line == "Duplication":
                duplication_started = True


        # Extract messages by category
        messages_by_category_regex = r"\|(\w*)\s*\|(\d*)\s*\|(\d*)\s*\|(\d*)\s*\|"
        messages_by_category_started = False
        for line in output.splitlines():
            if messages_by_category_started:
                match = re.match(messages_by_category_regex, line)
                if match:
                    category, number, previous, difference = match.groups()
                    messages_by_category[category] = {
                        "number": int(number),
                        "previous": int(previous),
                        "difference": int(difference)
                    }
            elif line == "Messages by category":
                messages_by_category_started = True

        # Extract statements, nloc, score
        statements_regex = r"(\d*)\sstatements\sanalysed"
        nloc_regex = r"(\d*)\slines\shave"
        score_regex = r"Your\scode\shas\sbeen\srated\sat\s(\S*)/10\s(?:\(previous\srun:\s(\S*)/10,\s([+|-]\S*)\))?"
        for line in output.splitlines():
            match = re.match(statements_regex, line)
            if (match):
                statements = match.groups()
                other["statements"] = statements[0]
            match = re.match(nloc_regex, line)
            if (match):
                nloc = match.groups()
                other["nloc"] = nloc[0]
            match = re.match(score_regex, line)
            if (match):
                now, prev, diff = match.groups()
                other["score"] = {
                    "now": now,
                    "previous": prev,
                    "difference": diff
                }

        
        # Construct object
        result = {
            "messages": messages,
            "statistics": stats,
            "raw_metrics": raw_metrics,
            "messages_by_category": messages_by_category,
            "duplication": duplication,
            "other": other
        }
        return result
    
    def __compute_metrics(self, output_dict) -> None:
        """
        Compute various metrics from the given output dictionary and store them as attributes of the current object.

        Args:
            output_dict (dict): A dictionary containing various metrics computed by some external tool.

        Returns:
            None
        """
        self.score = output_dict["other"]["score"]["now"]
        self.code = output_dict["raw_metrics"]["code"]["number"]
        self.code_avg = output_dict["raw_metrics"]["code"]["%"]
        self.docstring = output_dict["raw_metrics"]["docstring"]["number"]
        self.docstring_avg = output_dict["raw_metrics"]["docstring"]["%"]
        self.comment = output_dict["raw_metrics"]["comment"]["number"]
        self.comment_avg = output_dict["raw_metrics"]["comment"]["%"]
        self.blank = output_dict["raw_metrics"]["empty"]["number"]
        self.blank_avg = output_dict["raw_metrics"]["empty"]["%"]
        self.nmodule = output_dict["statistics"]["module"]["number"]
        self.noc = output_dict["statistics"]["class"]["number"]
        self.nom = output_dict["statistics"]["method"]["number"]
        self.nof = output_dict["statistics"]["function"]["number"]
        self.dup_line = output_dict["duplication"]["nb_duplicated_line"]["now"]
        self.num_msg = len(output_dict["messages"])
        self.module_comment_avg = output_dict["statistics"]["module"]["%documented"]
        self.class_comment_avg = output_dict["statistics"]["class"]["%documented"]
        self.methode_comment_avg = output_dict["statistics"]["method"]["%documented"]
        self.function_comment_avg = output_dict["statistics"]["function"]["%documented"]

    def __store_metrics(self, metric: Metric) -> None:
        """
        Stores the pylint metrics in the given Metric object and adds it to the current session.

        Args:
            metric (Metric): The Metric object to store the pylint metrics in.

        Returns:
            None.
        """
        metric.pylint_score = self.score
        metric.pylint_code = self.code
        metric.pylint_code_avg = self.code_avg
        metric.pylint_docstring = self.docstring
        metric.pylint_docstring_avg = self.docstring_avg
        metric.pylint_comment = self.comment
        metric.pylint_comment_avg = self.comment_avg
        metric.pylint_blank = self.blank
        metric.pylint_nmodule = self.nmodule
        metric.pylint_noc = self.noc
        metric.pylint_nom = self.nom
        metric.pylint_nof = self.nof
        metric.pylint_dup_line = self.dup_line
        metric.pylint_num_msg = self.num_msg
        metric.pylint_module_comment_avg = self.module_comment_avg
        metric.pylint_mclass_comment_avg = self.class_comment_avg
        metric.pylint_methode_comment_avg = self.methode_comment_avg
        metric.pylint_function_comment_avg = self.function_comment_avg

        self.session.add(metric)
        self.session.commit()