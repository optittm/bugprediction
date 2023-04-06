from dependency_injector import containers, providers
from configuration import Configuration
from dotenv import load_dotenv
from sqlalchemy.orm import sessionmaker
from exporters.ml_reports import MlHtmlExporter

from ml.ml import ml
from connectors.ck import CkConnector
from connectors.jpeek import JPeekConnector
from connectors.legacy import LegacyConnector
from connectors.pylint.pylint import PylintConnector
from connectors.codemaat import CodeMaatConnector
from connectors.fileanalyzer import FileAnalyzer
from connectors.git import GitConnector
from connectors.jira import JiraConnector
from importers.flatfile import FlatFileImporter
from exporters.html import HtmlExporter
from exporters.flatfile import FlatFileExporter

class Container(containers.DeclarativeContainer):
    load_dotenv()

    configuration: Configuration = providers.Singleton(Configuration)

    Session = sessionmaker()
    session = providers.Singleton(Session)

    legacy_connector_provider = providers.Factory(
        LegacyConnector,
        session = session,
        config = configuration
    )

    ck_connector_provider = providers.Factory(
        CkConnector,
        session = session,
        config = configuration
    )

    codemaat_connector_provider = providers.Factory(
        CodeMaatConnector,
        session = session,
        config = configuration
    )
    
    jpeek_connector_provider = providers.Factory(
        JPeekConnector,
        session = session,
        config = configuration
    )

    pylint_connector_provider = providers.Factory(
        PylintConnector,
        session = session,
        config = configuration
    )

    file_analyzer_provider = providers.Factory(
        FileAnalyzer,
        session = session
    )

    flat_file_importer_provider = providers.Singleton(
        FlatFileImporter,
        session = session,
        config = configuration
    )
    
    jira_connector_provider = providers.Factory(
        JiraConnector,
        session = session,  
        config = configuration
    )

    git_factory_provider = providers.AbstractFactory(
        GitConnector
    )

    ml_factory_provider = providers.AbstractFactory(
        ml
    )

    html_exporter_provider = providers.Singleton(
        HtmlExporter,
        session = session,
        configuration = configuration,
        model = ml_factory_provider
    )

    ml_html_exporter_provider = providers.Singleton(
        MlHtmlExporter,
        session = session,
        config = configuration
    )

    flat_file_exporter_provider = providers.Singleton(
        FlatFileExporter,
        session = session,
        config = configuration
    )
    