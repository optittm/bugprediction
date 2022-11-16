from dependency_injector import containers, providers
from configuration import Configuration
from dotenv import load_dotenv
from sqlalchemy.orm import sessionmaker
from models.database import setup_database
import sqlalchemy as db
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import ArgumentError
from models.project import Project
from dependency_injector.wiring import Provide, inject
from exceptions.configurationvalidation import ConfigurationValidationException


class Container(containers.DeclarativeContainer):
    # config
    load_dotenv()
    #config = providers.Configuration()

    configuration: Configuration = providers.Factory(Configuration)
    config = Configuration()
    try:
        engine = db.create_engine(config.target_database)
    except ArgumentError as e:
        raise ConfigurationValidationException(f"Error from sqlalchemy : {str(e)}")

    Session = sessionmaker()
    Session.configure(bind=engine)
    
    session = providers.Factory(Session)

    #setup_database(engine)

    sess = Session()

    setup_database(engine)

    project = sess.query(Project).filter(Project.name == config.source_project).first()
    if not project:
        project = Project(name=config.source_project,
                        repo=config.source_repo,
                        language=config.language)
        sess.add(project)
        sess.commit()

    

    # database

