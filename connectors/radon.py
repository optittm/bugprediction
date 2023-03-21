
import logging

from models.metric import Metric
from radon.complexity import cc_visit, average_complexity
from radon.raw import analyze
from radon.metrics import h_visit


class RadonConnector:

    def __init__(self, version, session, config) -> None:
        self.version = version
        self.session = session
        self.config = config

    def analyze_source_code(self) -> None:
        
        logging.info('RADON::analyze_repo')
        metric = self.session.query(Metric).filter(Metric.version_id == self.version.version_id).first()
        if (not metric):
            metric = Metric()
        
        # TODO it will maybe need to be updated
        if (self.config.language != "Python"):
            logging.info('RADON is only used for Python language')

        if (not metric.radon_cc_total):
            self.compute_metrics(metric)

    def compute_metrics(self, metric):
        
