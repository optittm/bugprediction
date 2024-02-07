import csv
import os
import re
import sys
import json
import logging
import platform
import subprocess
import tempfile
from xmlrpc.client import boolean

import click
import semver
import numpy as np
import pandas as pd
from sklearn import preprocessing
import sqlalchemy as db
from sqlalchemy.exc import ArgumentError
from dependency_injector.wiring import Provide, inject
from dotenv import dotenv_values, load_dotenv
from configuration import Configuration
from connectors.jira import JiraConnector
from sqlalchemy.orm import sessionmaker
from dependency_injector import providers
from exceptions.topsis_configuration import InvalidAlternativeError, InvalidCriterionError, MissingWeightError, NoAlternativeProvidedError, NoCriteriaProvidedError
from utils.alternatives import AlternativesParser

from utils.container import Container
from exceptions.configurationvalidation import ConfigurationValidationException
from models.project import Project
from models.version import Version
from models.issue import Issue
from models.metric import Metric
from models.model import Model
from models.database import setup_database
from connectors.git import GitConnector
from connectors.glpi import GlpiConnector
from utils.criterion import CriterionParser
from utils.metricfactory import MetricFactory
from utils.mlfactory import MlFactory
from utils.database import get_included_and_current_versions_filter
from utils.dirs import TmpDirCopyFilteredWithEnv
from utils.gitfactory import GitConnectorFactory
from utils.restrict_folder import RestrictFolder
import utils.math as mt


def lint_aliases(raw_aliases) -> boolean:
    try:
        aliases = json.loads(raw_aliases)
    except:
        return False

    if not isinstance(aliases, dict):
        return False

    for v in aliases.values():
        if not isinstance(v, list):
            return False

    return True


def check_branch_exists(configuration, repo_dir, branch_name):
    process = subprocess.run(
        [configuration.scm_path, "branch", "-a"], cwd=repo_dir, capture_output=True
    )

    if not f"remotes/origin/{branch_name}" in process.stdout.decode():
        raise ConfigurationValidationException(
            f"Branch {branch_name} doesn't exists in this repository"
        )


def instanciate_git_connector(
    configuration, git_factory_provider, tmp_dir, repo_dir
) -> GitConnector:
    """
    Instanciates a git connector and performs first checks
    """
    # Clone the repository
    process = subprocess.run(
        [configuration.scm_path, "clone", configuration.source_repo_url],
        stdout=subprocess.PIPE,
        cwd=tmp_dir,
    )

    try:
        process.check_returncode()
    except subprocess.CalledProcessError:
        raise ConfigurationValidationException(
            f"Failed to clone {configuration.source_repo_url} repository"
        )
    logging.info("Executed command line: " + " ".join(process.args))

    if not os.path.isdir(repo_dir):
        raise ConfigurationValidationException(
            f"Project {configuration.source_project} doesn't exist in current repository"
        )

    check_branch_exists(configuration, repo_dir, configuration.current_branch)
    process = subprocess.run(
        [configuration.scm_path, "checkout", configuration.current_branch],
        stdout=subprocess.PIPE,
        cwd=repo_dir,
    )

    try:
        git: GitConnector = git_factory_provider(project.project_id, repo_dir)

    except Exception as e:
        raise ConfigurationValidationException(
            f"Error connecting to project {configuration.source_repo} using source code manager: {str(e)}."
        )

    if not lint_aliases(configuration.author_alias):
        raise ConfigurationValidationException(
            f"Value error for aliases: {configuration.author_alias}"
        )

    return git


def source_bugs_check(configuration) -> None:
    if len(configuration.source_bugs) == 0:
        raise ConfigurationValidationException(
            "No synchro because parameter 'OTTM_SOURCE_BUGS' no defined"
        )
    
def fct_populate(
       skip_versions,
        session,
        configuration,
        git_factory_provider,
        jira_connector_provider,
        glpi_connector_provider,
        ck_connector_provider,
        pylint_connector_provider,
        file_analyzer_provider,
        jpeek_connector_provider,
        legacy_connector_provider,
        codemaat_connector_provider,
        pdepend_connector_provider,
        radon_connector_provider,
        survey_connector_provider,
):
    """Populate the database with the provided configuration"""
    
    for source_bugs in configuration.source_bugs:
        if source_bugs.strip() == 'jira':
            jira: JiraConnector = jira_connector_provider(project.project_id)
        elif source_bugs.strip() == 'glpi':
            glpi: GlpiConnector = glpi_connector_provider(project.project_id)
    
    # survey = survey_connector_provider()

    # Checkout, execute the tool and inject CSV result into the database
    # with tempfile.TemporaryDirectory() as tmp_dir:
    tmp_dir = tempfile.mkdtemp()
    logging.info("created temporary directory: " + tmp_dir)
    repo_dir = os.path.join(tmp_dir, configuration.source_project)

    git = instanciate_git_connector(configuration, git_factory_provider, tmp_dir, repo_dir)

    for source_bugs in configuration.source_bugs:
        if source_bugs.strip() == "jira":
            # Populate issue table in database with Jira issues
            jira: JiraConnector = jira_connector_provider(project.project_id)
            jira.create_issues()
        elif source_bugs.strip() == "glpi":
            # Populate issue table in database with Glpi issues
            glpi: GlpiConnector = glpi_connector_provider(project.project_id)
            glpi.create_issues()
        elif source_bugs.strip() == "git":
            git.create_issues()
            # if we use code maat git.setup_aliases(configuration.author_alias)

    git.populate_db(skip_versions)
    # survey.populate_comments()

    # List the versions and checkout each one of them
    versions = session.query(Version).filter(Version.project_id == project.project_id).all()
    restrict_folder = RestrictFolder(versions, configuration)
    for version in versions:
        process = subprocess.run([configuration.scm_path, "checkout", version.tag],
                                stdout=subprocess.PIPE,
                                cwd=repo_dir)
        logging.info('Executed command line: ' + ' '.join(process.args))

        with TmpDirCopyFilteredWithEnv(repo_dir, restrict_folder.get_include_folders(version), 
                                       restrict_folder.get_exclude_folders(version)) as tmp_work_dir:
            
            legacy = legacy_connector_provider(project.project_id, tmp_work_dir)
            legacy.get_legacy_files(version)

            # Get statistics from git log with codemaat
            # codemaat = codemaat_connector_provider(repo_dir, version)
            # codemaat.analyze_git_log()

            # Get statistics with lizard
            lizard = file_analyzer_provider(directory=tmp_work_dir, version=version)
            lizard.analyze_source_code()

            if configuration.language.lower() == "java":
                # Get metrics with CK
                ck = ck_connector_provider(directory=tmp_work_dir, version=version)
                ck.analyze_source_code()

                # Get metrics with JPeek
                # jp = jpeek_connector_provider(directory=tmp_work_dir, version=version)
                # jp.analyze_source_code()

            elif configuration.language.lower() == "php":
                # Get metrics with PDepend
                pdepend = pdepend_connector_provider(
                    directory=tmp_work_dir, version=version
                )
                pdepend.analyze_source_code()

            elif configuration.language.lower() == "python":
                # Get metrics with Radon
                radon = radon_connector_provider(
                    directory=tmp_work_dir, version=version
                )
                radon.analyze_source_code()

                # Get metrics with Pylint
                pylint = pylint_connector_provider(
                    directory=tmp_work_dir, version=version
                )
                pylint.analyze_source_code()

            else:
                raise Exception(f"Unsupported language: {configuration.language}")


def create_report(
    output,
    report_name,
    html_exporter_provider,
    ml_html_exporter_provider,
):
    """Create a basic HTML report"""
    MlFactory.create_predicting_ml_model(project.project_id)
    MetricFactory.create_metrics()
    exporter = html_exporter_provider(output)
    os.makedirs(output, exist_ok=True)
    if report_name == "churn":
        exporter.generate_churn_report(project, "churn.html")
    elif report_name == "release":
        exporter.generate_release_report(project, "release.html")
    elif report_name == "bugvelocity":
        exporter.generate_bugvelocity_report(project, "bugvelocity.html")
    elif report_name == "kmeans":
        exporter = ml_html_exporter_provider(output)
        exporter.generate_kmeans_release_report(project, "kmeans.html")
    else:
        click.echo("This report doesn't exist")
    logging.info(f"Created report {output}/{report_name}.html")



@click.group()
@click.pass_context
@inject
def cli(ctx):
    """Datamining on git repository to predict the risk of releasing next version"""
    pass


@cli.command()
@click.option(
    "--output", default=".", help="Destination folder", envvar="OTTM_OUTPUT_FOLDER"
)
@click.option(
    "--format",
    default="csv",
    help="Output format (csv,parquet)",
    envvar="OTTM_OUTPUT_FORMAT",
)
@click.pass_context
@inject
def export(
    ctx,
    output,
    format,
    flat_file_exporter_provider=Provide[Container.flat_file_exporter_provider.provider],
):
    """Export the database to a flat format"""
    logging.info("export")
    if output is None:
        logging.error("Parameter output is mandatory")
        sys.exit("Parameter output is mandatory")
    if format is None:
        logging.error("Parameter format is mandatory")
        sys.exit("Parameter format is mandatory")
    else:
        format = format.lower()
        if format not in ["csv", "parquet"]:
            logging.error("Unsupported output format")
            sys.exit("Unsupported output format")
    os.makedirs(output, exist_ok=True)
    exporter = flat_file_exporter_provider(project.project_id, output)
    if format == "csv":
        exporter.export_to_csv("metrics.csv")
    elif format == "parquet":
        exporter.export_to_parquet("metrics.parquet")
    logging.info(f"Created export {output}/metrics.{format}")


@cli.command()
@click.option(
    "--output", default=".", help="Destination folder", envvar="OTTM_OUTPUT_FOLDER"
)
@click.option(
    "--report-name",
    default="release",
    help="Name of the report (release, churn, bugvelocity)",
)
@click.pass_context
@inject
def report(
    ctx,
    output,
    report_name,
    html_exporter_provider=Provide[Container.html_exporter_provider.provider],
    ml_html_exporter_provider=Provide[Container.ml_html_exporter_provider.provider],
):
    """Create a basic HTML report"""
    create_report(
        output,
        report_name,
        html_exporter_provider,
        ml_html_exporter_provider,
    )

@cli.command(name="import")
@click.option(
    "--target-table", is_flag=True, help="Target table in database for the import"
)
@click.option("--file-path", is_flag=True, help="Path of file")
@click.option(
    "--overwrite", is_flag=True, default=False, help="Overwrite database table"
)
@click.pass_context
@inject
def import_file(
    ctx,
    target_table,
    file_path,
    overwrite,
    flat_file_importer_provider=Provide[Container.flat_file_importer_provider.provider],
):
    """Import file into tables"""
    importer = flat_file_importer_provider(file_path, target_table, overwrite)
    importer.import_from_csv()


@cli.command()
@click.option("--model-name", default="bugvelocity", help="Name of the model")
@click.pass_context
@inject
def train(
    ctx, model_name, ml_factory_provider=Provide[Container.ml_factory_provider.provider]
):
    """Train a model"""
    MlFactory.create_training_ml_model(model_name)
    MetricFactory.create_metrics()
    model = ml_factory_provider(project.project_id)
    model.train()
    click.echo("Model was trained")


@cli.command()
@click.option("--model-name", default="bugvelocity", help="Name of the model")
@click.pass_context
@inject
def predict(
    ctx, model_name, ml_factory_provider=Provide[Container.ml_factory_provider.provider]
):
    """Predict next value with a trained model"""
    MlFactory.create_training_ml_model(model_name)
    MetricFactory.create_metrics()
    model = ml_factory_provider(project.project_id)
    value = model.predict()
    click.echo("Predicted value : " + str(value))


@cli.command()
@click.pass_context
@inject
def info(
    ctx,
    configuration=Provide[Container.configuration],
    session=Provide[Container.session],
):
    """Provide information about the current configuration
    If these values are not populated, the tool won't work.
    """

    excluded_versions = configuration.exclude_versions
    included_and_current_versions = get_included_and_current_versions_filter(
        session, configuration
    )
    filtered_version_count = (
        session.query(Version)
        .filter(Version.project_id == project.project_id)
        .filter(Version.include_filter(included_and_current_versions))
        .filter(Version.exclude_filter(excluded_versions))
        .count()
    )

    total_versions_count = (
        session.query(Version).filter(Version.project_id == project.project_id).count()
    )
    issues_count = (
        session.query(Issue).filter(Issue.project_id == project.project_id).count()
    )
    metrics_count = (
        session.query(Metric)
        .join(Version)
        .filter(Version.project_id == project.project_id)
        .count()
    )
    trained_models = (
        session.query(Model.name).filter(Model.project_id == project.project_id).all()
    )
    trained_models = [r for r, in trained_models]

    out = """ -- OTTM Bug Predictor --
    Project  : {project}
    Language : {language}
    SCM      : {scm} / {repo}
    Release  : {release}
    
    Versions : {versions} ({excluded_versions} filtered)
    Issues   : {issues}
    Metrics  : {metrics}

    Trained models : {models}
    """.format(
        project=configuration.source_project,
        language=configuration.language,
        scm=configuration.source_repo_scm,
        repo=configuration.source_repo_url,
        release=configuration.current_branch,
        versions=filtered_version_count,
        excluded_versions=total_versions_count - filtered_version_count,
        issues=issues_count,
        metrics=metrics_count,
        models=", ".join(trained_models),
    )
    click.echo(out)


@cli.command()
@click.pass_context
@inject
def check(ctx, configuration = Provide[Container.configuration],
          git_factory_provider = Provide[Container.git_factory_provider.provider],
          jira_connector_provider = Provide[Container.jira_connector_provider.provider],
          glpi_connector_provider = Provide[Container.glpi_connector_provider.provider],
          survey_connector_provider = Provide[Container.survey_connector_provider.provider]):
    """Check the consistency of the configuration and perform basic tests"""
    tmp_dir = tempfile.mkdtemp()
    logging.info("created temporary directory: " + tmp_dir)
    repo_dir = os.path.join(tmp_dir, configuration.source_project)

    for source_bugs in configuration.source_bugs:
        if source_bugs.strip() == 'jira':
            jira: JiraConnector = jira_connector_provider(project.project_id)
        elif source_bugs.strip() == 'glpi':
            glpi: GlpiConnector = glpi_connector_provider(project.project_id)

    survey = survey_connector_provider()

    source_bugs_check(configuration)
    instanciate_git_connector(configuration, git_factory_provider, tmp_dir, repo_dir)

    logging.info("Check OK")


@cli.command()
@click.option(
    "--skip-versions",
    is_flag=True,
    default=False,
    help="Skip the step <populate Version table>",
)
@click.pass_context
@inject
def populate(
    ctx,
    skip_versions,
    session=Provide[Container.session],
    configuration=Provide[Container.configuration],
    git_factory_provider=Provide[Container.git_factory_provider.provider],
    jira_connector_provider=Provide[Container.jira_connector_provider.provider],
    glpi_connector_provider=Provide[Container.glpi_connector_provider.provider],
    ck_connector_provider=Provide[Container.ck_connector_provider.provider],
    pylint_connector_provider=Provide[Container.pylint_connector_provider.provider],
    file_analyzer_provider=Provide[Container.file_analyzer_provider.provider],
    jpeek_connector_provider=Provide[Container.jpeek_connector_provider.provider],
    legacy_connector_provider=Provide[Container.legacy_connector_provider.provider],
    codemaat_connector_provider=Provide[Container.codemaat_connector_provider.provider],
    pdepend_connector_provider=Provide[Container.pdepend_connector_provider.provider],
    radon_connector_provider=Provide[Container.radon_connector_provider.provider],
    survey_connector_provider=Provide[Container.survey_connector_provider.provider],
):
    
    fct_populate(
        skip_versions,
        session,
        configuration,
        git_factory_provider,
        jira_connector_provider,
        glpi_connector_provider,
        ck_connector_provider,
        pylint_connector_provider,
        file_analyzer_provider,
        jpeek_connector_provider,
        legacy_connector_provider,
        codemaat_connector_provider,
        pdepend_connector_provider,
        radon_connector_provider,
        survey_connector_provider,
    )


#####################################################################
# For test purposes only                                            #
#####################################################################
@cli.command()
@click.option(
    "--skip-versions",
    is_flag=True,
    default=False,
    help="Skip the step <populate Version table>",
)
@click.pass_context
@inject
def testingtraining(
    ctx,
    skip_versions,
    session=Provide[Container.session],
    configuration=Provide[Container.configuration],
    git_factory_provider=Provide[Container.git_factory_provider.provider],
    jira_connector_provider=Provide[Container.jira_connector_provider.provider],
    glpi_connector_provider=Provide[Container.glpi_connector_provider.provider],
    ck_connector_provider=Provide[Container.ck_connector_provider.provider],
    pylint_connector_provider=Provide[Container.pylint_connector_provider.provider],
    file_analyzer_provider=Provide[Container.file_analyzer_provider.provider],
    jpeek_connector_provider=Provide[Container.jpeek_connector_provider.provider],
    legacy_connector_provider=Provide[Container.legacy_connector_provider.provider],
    codemaat_connector_provider=Provide[Container.codemaat_connector_provider.provider],
    pdepend_connector_provider=Provide[Container.pdepend_connector_provider.provider],
    radon_connector_provider=Provide[Container.radon_connector_provider.provider],
    survey_connector_provider=Provide[Container.survey_connector_provider.provider],
    ml_factory_provider=Provide[Container.ml_factory_provider.provider],
    html_exporter_provider=Provide[Container.html_exporter_provider.provider],
    ml_html_exporter_provider=Provide[Container.ml_html_exporter_provider.provider]
):
    fct_populate(
        skip_versions,
        session,
        configuration,
        git_factory_provider,
        jira_connector_provider,
        glpi_connector_provider,
        ck_connector_provider,
        pylint_connector_provider,
        file_analyzer_provider,
        jpeek_connector_provider,
        legacy_connector_provider,
        codemaat_connector_provider,
        pdepend_connector_provider,
        radon_connector_provider,
        survey_connector_provider,
    )
    # train(ctx, "bugvelocity", ml_factory_provider=Provide[Container.ml_factory_provider.provider])
    #   """Predict next value with a trained model"""
    MlFactory.create_training_ml_model("bugvelocity")
    MetricFactory.create_metrics()
    model = ml_factory_provider(project.project_id)
    value = model.predict()
    click.echo("Predicted value : " + str(value))

    # train(ctx, "codemetrics", ml_factory_provider=Provide[Container.ml_factory_provider.provider])
    #   """Predict next value with a trained model"""
    MlFactory.create_training_ml_model("codemetrics")
    MetricFactory.create_metrics()
    model = ml_factory_provider(project.project_id)
    value = model.predict()
    click.echo("Predicted value : " + str(value))
  
    # predict(ctx, "bugvelocity", ml_factory_provider=Provide[Container.ml_factory_provider.provider])
    #  """Predict next value with a trained model"""
    MlFactory.create_training_ml_model("bugvelocity")
    MetricFactory.create_metrics()
    model = ml_factory_provider(project.project_id)
    value = model.predict()
    click.echo("Predicted value : " + str(value))

    # predict(ctx, "codemetrics", ml_factory_provider=Provide[Container.ml_factory_provider.provider])
    #  """Predict next value with a trained model"""
    MlFactory.create_training_ml_model("codemetrics")
    MetricFactory.create_metrics()
    model = ml_factory_provider(project.project_id)
    value = model.predict()
    click.echo("Predicted value : " + str(value))

    # report(ctx,
    # ".",
    # "release",
    # html_exporter_provider=Provide[Container.html_exporter_provider.provider],
    # ml_html_exporter_provider=Provide[Container.ml_html_exporter_provider.provider])
    create_report(
        ".",
        "release",
        html_exporter_provider,
        ml_html_exporter_provider,
    )


@click.command()
@inject
def main():
    pass

#####################################################################
# For research purposes only                                        #
#####################################################################

@cli.command()
@click.option("--dataset-dir", default="./data/dataset", help="The path to the dataset directory.")
@click.option("--output-file", default="./data/research/topsis_output.csv", help="The name of the output CSV file.")
@inject
def datasetgen(dataset_dir, output_file, configuration: Configuration = Provide[Container.configuration]):
    """
    Generate datasets for TOPSIS analysis from multiple projects in the dataset directory.

    Args:
        dataset_dir (str): The path to the dataset directory.
        output_file (str): The name of the output CSV file.
        configuration (Configuration, optional): The configuration settings for TOPSIS analysis. Defaults to the provided container configuration.

    Note:
        This command iterates through the projects in the dataset directory and loads the corresponding .env configuration files.
        It uses the configuration from the .env files and constructs a SQLite database path for each project.
        The TOPSIS analysis is then performed for each project using the specific configuration, and the results are written to CSV files.
        The output CSV files are saved in the respective project folders.

    Raises:
        None.
    """
    for project_folder in os.listdir(dataset_dir):
        # print(project_folder)
        project_path = os.path.join(dataset_dir, project_folder)

        # Check if it's a directory and contains .env file
        if os.path.isdir(project_path) and ".env" in os.listdir(project_path):
            # Load the .env configuration for this project
            env_file_path = os.path.join(project_path, ".env")
            env_var = dotenv_values(env_file_path)

            configuration.source_repo_scm = env_var.get("OTTM_SOURCE_REPO_SCM")
            configuration.source_repo_url = env_var.get("OTTM_SOURCE_REPO_URL")
            configuration.current_branch = env_var.get("OTTM_CURRENT_BRANCH")
            configuration.source_bugs = env_var.get("OTTM_SOURCE_BUGS")
            configuration.source_repo = env_var.get("OTTM_SOURCE_REPO")
            configuration.source_project = env_var.get("OTTM_SOURCE_PROJECT")
            configuration.target_database = f"sqlite:///{project_path}/{configuration.source_project}.sqlite3"
            print(configuration.target_database)

            # Créer un nouveau moteur SQLAlchemy
            new_engine = db.create_engine(configuration.target_database)

            # Créer une nouvelle session à partir du nouveau moteur
            Session = sessionmaker()
            Session.configure(bind=new_engine)
            session = Session()

            # Query to get the id of the version with the name "Next Release"
            next_release_version = (
                session.query(Version)
                .filter(Version.project_id == project.project_id)
                .filter(Version.name == "Next Release")
                .first()
            )

            # Check if "Next Release" version exists for this project
            if next_release_version is not None:
                next_release_version_id = next_release_version.version_id
                num_lines_query = session.query(Metric.lizard_total_nloc).filter(Metric.version_id == next_release_version_id)
                num_lines = num_lines_query.scalar()
            else:
                # Handle case when "Next Release" version does not exist
                num_lines = np.nan
            print(num_lines)

            # Remplacer l'ancienne session par la nouvelle dans le conteneur
            container.session.override(providers.Singleton(Session))
            
            # Call the topsis command with the project-specific configuration
            topsis_output = topsis()

            # Write topsis_output to CSV file
            write_output_to_csv(configuration.source_repo, num_lines, topsis_output, output_file)

@cli.command()
@inject
def display_topsis_weight():
    """
    Perform TOPSIS analysis on a dataset.

    Args:
        session (Session, optional): The database session. Defaults to the provided container session.
        configuration (Configuration, optional): The configuration settings for TOPSIS analysis. Defaults to the provided container configuration.

    Returns:
        dict: A dictionary containing the weights of alternatives after TOPSIS analysis.

    Note:
        This command performs the TOPSIS (Technique for Order of Preference by Similarity to Ideal Solution) analysis on a given dataset to determine the weights of alternatives based on criteria and their corresponding weights provided in the configuration.

    Raises:
        Various exceptions from CriterionParser and AlternativesParser classes:
        - InvalidCriterionError: If an invalid criterion name is encountered.
        - MissingWeightError: If some criteria are missing weights.
        - NoCriteriaProvidedError: If no criteria are provided.
        - InvalidAlternativeError: If an invalid alternative name is encountered.
        - NoAlternativeProvidedError: If no alternatives are provided.
    """
    output = topsis()

    # Display the weights of alternatives
    print("**********************")
    print("* ALTERNATIVES WEIGHTS *")
    print("**********************")
    for key, value in output.items():
        print("* " + key + " : ", value)
    print("**********************")

    return output

@inject
def topsis( 
    session = Provide[Container.session], 
    configuration: Configuration = Provide[Container.configuration]
):
    """
    Perform TOPSIS analysis on a dataset.

    Args:
        session (Session, optional): The database session. Defaults to the provided container session.
        configuration (Configuration, optional): The configuration settings for TOPSIS analysis. Defaults to the provided container configuration.

    Returns:
        dict: A dictionary containing the weights of alternatives after TOPSIS analysis.

    Note:
        This command performs the TOPSIS (Technique for Order of Preference by Similarity to Ideal Solution) analysis on a given dataset to determine the weights of alternatives based on criteria and their corresponding weights provided in the configuration.

    Raises:
        Various exceptions from CriterionParser and AlternativesParser classes:
        - InvalidCriterionError: If an invalid criterion name is encountered.
        - MissingWeightError: If some criteria are missing weights.
        - NoCriteriaProvidedError: If no criteria are provided.
        - InvalidAlternativeError: If an invalid alternative name is encountered.
        - NoAlternativeProvidedError: If no alternatives are provided.
    """
    excluded_versions = configuration.exclude_versions
    included_and_current_versions = get_included_and_current_versions_filter(
        session, configuration
    )

    # Get the version metrics and the average cyclomatic complexity
    metrics_statement = (
        session.query(Version, Metric)
        .filter(Version.project_id == project.project_id)
        .filter(Version.include_filter(included_and_current_versions))
        .filter(Version.exclude_filter(excluded_versions))
        .join(Metric, Metric.version_id == Version.version_id)
        .order_by(Version.start_date.asc())
        .statement
    )
    logging.debug(metrics_statement)
    df = pd.read_sql(metrics_statement, session.get_bind())

    # Prepare data for topsis
    criteria_parser = CriterionParser()
    alternative_parser = AlternativesParser()

    criteria_names = configuration.topsis_criteria
    criteria_weights = configuration.topsis_weigths

    try:
        criteria = criteria_parser.parse_criteria(criteria_names, criteria_weights)
    except (InvalidCriterionError, MissingWeightError, NoCriteriaProvidedError) as e:
        print(f"Error: {e}")
        return

    alternative_names = configuration.topsis_alternatives

    try:
        alternatives = alternative_parser.parse_alternatives(alternative_names)
    except (InvalidAlternativeError, NoAlternativeProvidedError) as e:
        print(f"Error: {e}")
        return

    # Prepare data for alternatives
    alternative_data = {}
    for alternative in alternatives:
        data = alternative.get_data(df)
        alternative_data[alternative.get_name()] = preprocessing.normalize(data)

    # Create the decision matrix
    decision_matrix_builder = mt.Math.DecisionMatrixBuilder()

    # Add criteria to the decision matrix
    for criterion in criteria:
        decision_matrix_builder.add_criteria(criterion.get_data(df), criterion.get_name())

    # Add alternatives to the decision matrix
    for alternative in alternatives:
        decision_matrix_builder.add_alternative(alternative.get_data(df), alternative.get_name())

    # Set correlation methods if provided in the configuration
    methods = []
    for method in configuration.topsis_corr_method:
        methods.append(mt.Math.get_correlation_methods_from_name(method))
    if len(methods) > 0:
        decision_matrix_builder.set_correlation_methods(methods)

    # Build the decision matrix
    decision_matrix = decision_matrix_builder.build()

    # Compute topsis
    ts = mt.Math.TOPSIS(
        decision_matrix,
        [criterion.get_weight() for criterion in criteria], 
        [criterion.get_direction() for criterion in criteria]
    )
    ts.topsis()


    # Calculate the weights of alternatives after TOPSIS analysis
    weight = ts.get_closeness()
    total_weight = sum(weight)
    
    if total_weight != 0:
        weight = weight / total_weight
    else:
        weight = np.full(len(weight), np.nan)

    # Prepare the output dictionary containing the weights of alternatives
    output = {}
    for key, value in decision_matrix_builder.alternatives_dict.items():
        output[key] = weight[value]

    return output


def write_output_to_csv(project_name, num_lines, output_dict, output_file_path):
    """
    Write the dictionary and project name to a CSV file.

    Args:
        project_name (str): The name of the project.
        output_dict (dict): The dictionary to be saved in CSV.
        output_file_path (str): The file path for the CSV output.

    Returns:
        None.
    """
    # Create the directory if it does not exist
    os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

    # Check if the file already exists
    file_exists = os.path.isfile(output_file_path)

    # Open the file in 'a' mode (append mode) to create if it doesn't exist
    with open(output_file_path, mode="a", newline="") as output_file:
        fieldnames = ["Project", "num_lines"] + list(output_dict.keys())
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)

        # Write header only if the file is newly created
        if not file_exists:
            writer.writeheader()

        # Create a new row with the project name and dictionary values
        row = {"Project": project_name, "num_lines": num_lines}
        row.update(output_dict)
        writer.writerow(row)

#####################################################################


@inject
def configure_logging(config=Provide[Container.configuration]) -> None:
    logging.basicConfig(level=config.log_level)


@inject
def configure_session(
    container: Container, config=Provide[Container.configuration]
) -> None:
    try:
        engine = db.create_engine(config.target_database)
    except ArgumentError as e:
        raise ConfigurationValidationException(f"Error from sqlalchemy : {str(e)}")

    Session = sessionmaker()
    Session.configure(bind=engine)
    setup_database(engine)

    container.session.override(providers.Singleton(Session))


@inject
def instanciate_project(
    config=Provide[Container.configuration], session=Provide[Container.session]
) -> Project:
    project = (
        session.query(Project).filter(Project.name == config.source_project).first()
    )
    if not project:
        project = Project(
            name=config.source_project,
            repo=config.source_repo,
            language=config.language,
        )
        session.add(project)
        session.commit()
    return project


if __name__ == "__main__":
    try:
        PATH_ENV_FILE1 = './.env'
        PATH_ENV_FILE2 = './data/.env'
        if os.path.isfile(PATH_ENV_FILE1) and os.access(PATH_ENV_FILE1, os.R_OK):
            # print("File PATH_ENV_FILE1 exists and is readable")
            ENV_FILE = PATH_ENV_FILE1
        elif os.path.isfile(PATH_ENV_FILE2) and os.access(PATH_ENV_FILE2, os.R_OK):
            # print("File PATH_ENV_FILE2 exists and is readable")
            ENV_FILE = PATH_ENV_FILE2
        else:
            print("Either the file .env is missing or not readable in directory ./ or ./data/ ")
            exit(2)
            
        load_dotenv(ENV_FILE)

        container = Container()
        container.init_resources()
        container.wire(
            modules=[
                __name__,
                "utils.gitfactory",
                "utils.mlfactory",
                "utils.metricfactory",
            ]
        )

        configure_logging()
        configure_session(container)
        project = instanciate_project()
        GitConnectorFactory.create_git_connector()

        logging.info("python: " + platform.python_version())
        logging.info("system: " + platform.system())
        logging.info("machine: " + platform.machine())

        # Setup command line options
        cli(obj={})
    except ConfigurationValidationException as e:
        logging.error("CONFIGURATIONS ERROR")
        logging.error(e.message)
