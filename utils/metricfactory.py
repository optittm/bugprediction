import logging

from dependency_injector import providers
from dependency_injector.wiring import Provide, inject

from ml.bugvelocity import BugVelocity
from ml.codemetrics import CodeMetrics
from models.metric_java import MetricJava
from models.model import Model
from utils.container import Container


class MetricFactory:

    @staticmethod
    @inject
    def create_metrics(session = Provide[Container.session], 
                        config = Provide[Container.configuration],
                        metric_factory_provider = Provide[Container.metric_factory_provider.provider]) -> None:
        if config.language.lower() == "java":
            # logging.info("Using BugVelocity Model")
            metric_factory_provider.override(
                providers.Factory(
                    MetricJava,
                    session = session,
                    config = config
                )
            )
        elif model_name == "codemetrics":
            logging.info("Using CodeMetrics Model")
            ml_factory_provider.override(
                providers.Factory(
                    CodeMetrics,
                    session = session,
                    config = config
                )
            )
        else:
            logging.error(f"Unknown ml model: {model_name}")
            raise Exception('Unknown ml model')
