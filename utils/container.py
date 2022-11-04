from dependency_injector import containers, providers
from configuration import Configuration
from dotenv import load_dotenv

class Container(containers.DeclarativeContainer):
    # config
    load_dotenv()
    #config = providers.Configuration()

    configuration: Configuration = providers.Factory(Configuration)

    # database

