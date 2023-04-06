import logging
import sys

from dependency_injector import providers
from dependency_injector.wiring import Provide, inject

from ml.bugvelocity import BugVelocity
from ml.codemetrics import CodeMetrics
from models.model import Model
from utils.container import Container
from utils.nullml import NullML


class MlFactory:
    @staticmethod
    @inject
    def is_model_trained(project_id):
        try:
            ml_factory = MlFactory(project_id)
            return ml_factory.is_model_trained()
        except Exception as e:
            print(f"Error while checking if model is trained: {e}")
            return False
    
    @staticmethod
    @inject
    def create_training_ml_model(model_name: str,
                        session = Provide[Container.session], 
                        config = Provide[Container.configuration],
                        ml_factory_provider = Provide[Container.ml_factory_provider.provider]) -> None:
        if model_name == "bugvelocity":
            logging.info("Using BugVelocity Model")
            ml_factory_provider.override(
                providers.Factory(
                    BugVelocity,
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
            sys.exit('Unknown ml model')
    
    @staticmethod
    @inject
    def create_predicting_ml_model(project_id,
                                   session = Provide[Container.session],
                                   config = Provide[Container.configuration],
                                   ml_factory_provider = Provide[Container.ml_factory_provider.provider]) -> None:
        
        trained_models = session.query(Model.name).filter(Model.project_id == project_id).all()
        trained_models = [r for r, in trained_models]

        if 'bugvelocity' in trained_models:
            logging.info("Using BugVelocity Model")
            ml_factory_provider.override(
                providers.Factory(
                    BugVelocity,
                    session = session,
                    config = config,
                    project_id=project_id
                )
            )
            
        elif 'codemetrics' in trained_models:
            logging.info("Using CodeMetrics Model")
            ml_factory_provider.override(
                providers.Factory(
                    CodeMetrics,
                    session = session,
                    config = config,
                    project_id=project_id
                )
            )
        else:
            ml_factory_provider.override(
                providers.Factory(NullML,
                )
            )
            logging.warning("No trained model found for the given project.")

