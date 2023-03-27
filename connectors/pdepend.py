import logging
import os
import subprocess
import tempfile
from os.path import exists
import xml.etree.ElementTree as ET

from models.metric import Metric
from utils.math import Math
from utils.timeit import timeit


class PDependConnector:
    """
    Connector to PHP Depend CLI tool
    https://github.com/pdepend/pdepend

    Attributes:
    -----------
        - directory   Full path to a cloned GIT repository
        - session     Connection to a database managed by sqlalchemy
        - version     Sqlalchemy object representing a Version
    """
    def __init__(self, directory, version, session, config):
        self.directory = directory
        self.session = session
        self.version = version
        self.configuration = config

    def analyze_source_code(self):
        """
        Analyze the repository by using PHP Depend analysis tool
        """
        logging.info('PDepend::analyze_repo')
        # Test if metrics have been already generated for this version
        metric = self.session.query(Metric).filter(Metric.version_id == self.version.version_id).first()
        if not metric:
            metric = Metric()
        if self.configuration.language != "PHP":
            logging.info('PDepend is only used for PHP language')
        elif not metric.pdepend_wmc:
            self.compute_metrics(metric)
        else:
            logging.info('PDepend analysis already done for this version')

    def _xml_get_nodes_atribute(self, root, node_name, attribute_name):
        nodes = root.findall(f".//{node_name}[@{attribute_name}]")
        return [node.attrib[attribute_name] for node in nodes]
    
    def _list_str_to_int(self, list_):
        return list(map(int, list_))
    
    def __compute_mean(self, xml_root, metric, mean_divide):
        return Math.get_rounded_mean(
            self._list_str_to_int(
                self._xml_get_nodes_atribute(xml_root, mean_divide, metric)
            )
        )
    
    @timeit
    def compute_metrics(self, metric):
        """
        Compute PDepend metrics. As the metrics were computed at the file or function level,
        we need to compute the average for the repository.
        """
        logging.info('PDepend::compute_metrics')
        # Read xml files

        with tempfile.TemporaryDirectory() as tmp_dir:
            # Launch the PDepend utility and output values into a temporary directory
            logging.info('PDepend::generate_pdepend_xml_file')

            process = subprocess.run([self.configuration.php_path,
                                      # Prevents deprecation warnings within PDepend from showing on console
                                      "-d error_reporting='E_ALL & ~E_DEPRECATED'",
                                      self.configuration.code_pdepend_path,
                                      f"--summary-xml={os.path.join(tmp_dir, 'summary.xml')}",
                                      self.directory])
            logging.info('Executed command line: ' + ' '.join(process.args))
            logging.info('Command return code ' + str(process.returncode))

            if exists(os.path.join(tmp_dir, "summary.xml")):
                try:
                    logging.info('PDepend file generated correctly')
                    metric.version_id = self.version.version_id

                    # Read xml file
                    xml_tree = ET.parse(os.path.join(tmp_dir, "summary.xml"))
                    xml_root = xml_tree.getroot()

                    # Intermediate values to calculate means
                    total_nb_classes = int(xml_root.attrib["noc"])
                    total_nb_methods = int(xml_root.attrib["nom"])

                    # Calculate mean PDepend values
                    metric.pdepend_cbo = self.__compute_mean(xml_root, "cbo", "class")
                                                                                                # Checking if nb_classes is 0 to avoid null division
                    metric.pdepend_fan_out = Math.get_rounded_divide(int(xml_root.attrib["fanout"]), (total_nb_classes if total_nb_classes else 1))
                    metric.pdepend_dit = self.__compute_mean(xml_root, "dit", "class")
                    metric.pdepend_nof = self.__compute_mean(xml_root, "nof", "package")
                    metric.pdepend_noc = self.__compute_mean(xml_root, "noc", "package")
                    metric.pdepend_nom = self.__compute_mean(xml_root, "nom", "class")
                    metric.pdepend_nopm = self.__compute_mean(xml_root, "npm", "class")
                    metric.pdepend_vars = self.__compute_mean(xml_root, "vars", "class")
                    metric.pdepend_wmc = self.__compute_mean(xml_root, "wmc", "class")
                                                                                            # Checking if nb_methods is 0 to avoid null division
                    metric.pdepend_calls = Math.get_rounded_divide(int(xml_root.attrib["calls"]), (total_nb_methods if total_nb_methods else 1))
                    metric.pdepend_nocc = self.__compute_mean(xml_root, "nocc", "class")
                    metric.pdepend_noom = self.__compute_mean(xml_root, "noom", "class")
                    metric.pdepend_noi = self.__compute_mean(xml_root, "noi", "package")
                    metric.pdepend_nop = int(xml_root.attrib["nop"])

                    # Save metrics values into the database
                    self.session.add(metric)
                    self.session.commit()
                    logging.info("PDepend metrics added to database for version " + self.version.tag)
                except ET.ParseError:
                    logging.error("Unable to parse PDepend XML report / version " + self.version.tag)
                except Exception as e:
                    logging.error("An error occurred while reading PDepend report for version " + self.version.tag)
                    logging.error(str(e))