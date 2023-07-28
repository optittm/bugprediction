import json
import os
import shutil
import logging
from typing import List

from exceptions.configurationvalidation import ConfigurationValidationException

AVAILABLE_SCM = ["github", "gitlab"]


class Configuration:
    next_version_name = "Next Release"

    def __init__(self):
        self.log_level = self.__get_log_level("OTTM_LOG_LEVEL")

        self.code_maat_path = self.__get_external_tool("OTTM_CODE_MAAT_PATH")
        self.code_ck_path = self.__get_external_tool("OTTM_CODE_CK_PATH")
        self.code_jpeek_path = self.__get_external_tool("OTTM_CODE_JPEEK_PATH")
        self.code_pdepend_path = self.__get_external_tool("OTTM_CODE_PDEPEND_PATH")

        self.language = os.getenv("OTTM_LANGUAGE", "")

        self.scm_path = self.__get_executable("OTTM_SCM_PATH")
        if self.language.lower() == "java":
            self.java_path = self.__get_executable("OTTM_JAVA_PATH")
        elif self.language.lower() == "php":
            self.php_path = self.__get_executable("OTTM_PHP_PATH")

        self.target_database = self.__get_required_value("OTTM_TARGET_DATABASE")

        self.source_repo_scm = self.__get_repo_scm("OTTM_SOURCE_REPO_SCM")
        self.source_project = self.__get_required_value("OTTM_SOURCE_PROJECT")
        self.source_repo = self.__get_required_value("OTTM_SOURCE_REPO")
        self.current_branch = self.__get_required_value("OTTM_CURRENT_BRANCH")
        self.source_repo_url = self.__get_required_value("OTTM_SOURCE_REPO_URL")
        self.source_bugs = self.__get_str_list("OTTM_SOURCE_BUGS")

        self.survey_back_api_url = os.getenv("SURVEY_BACK_API_URL", "")
        self.survey_project_name = self.__get_str_list("SURVEY_PROJECT_NAME")
        self.scm_base_url = os.getenv("OTTM_SCM_BASE_URL", "")
        self.scm_token = os.getenv("OTTM_SCM_TOKEN", "")
        self.scm_issues_labels = os.getenv("OTTM_SCM_ISSUES_LABELS", "")

        self.jira_base_url = os.getenv("OTTM_JIRA_BASE_URL", "")
        self.jira_project = os.getenv("OTTM_JIRA_PROJECT", "")
        self.jira_email = os.getenv("OTTM_JIRA_EMAIL", "")
        self.jira_token = os.getenv("OTTM_JIRA_TOKEN", "")
        self.jira_issue_type = self.__get_str_list("OTTM_JIRA_ISSUE_TYPE")

        self.glpi_categories = self.__get_str_list("OTTM_GLPI_CATEGORIES")
        self.glpi_base_url = os.getenv("OTTM_GLPI_BASE_URL", "")
        self.glpi_app_token = os.getenv("OTTM_GLPI_APP_TOKEN", "")
        self.glpi_user_token = os.getenv("OTTM_GLPI_USER_TOKEN", "")
        self.glpi_username = os.getenv("OTTM_GLPI_USERNAME", "")
        self.glpi_password = os.getenv("OTTM_GLPI_PASSWORD", "")

        self.issue_tags = self.__get_str_list("OTTM_ISSUE_TAGS")
        self.exclude_issuers = self.__get_str_list("OTTM_EXCLUDE_ISSUERS")

        self.include_folders = self.__get_path_list("OTTM_INCLUDE_FOLDERS")
        self.exclude_folders = self.__get_path_list("OTTM_EXCLUDE_FOLDERS")

        self.exclude_versions = self.__get_str_list("OTTM_EXCLUDE_VERSIONS")
        self.include_versions = self.__get_str_list("OTTM_INCLUDE_VERSIONS")

        self.author_alias = os.getenv("OTTM_AUTHOR_ALIAS", "")
        self.exclude_authors = self.__get_str_list("OTTM_EXCLUDE_AUTHORS")

        self.insignificant_commits_message = self.__get_str_list("OTTM_COMMIT_BAD_MSG")

        self.retry_delay = self.__get_retry_delay("OTTM_RETRY_DELAY")

        self.legacy_percent = self.__get_float("OTTM_LEGACY_PERCENT", 20)

        self.legacy_minimum_days = self.__get_int("OTTM_LEGACY_MINIMUM_DAYS", 365)

        self.topsis_corr_method = self.__get_str_list("OTTM_CORR_METHOD")

    @staticmethod
    def __get_log_level(env_var):
        log_level = logging.INFO

        if env_var in os.environ:
            required_level = os.environ["OTTM_LOG_LEVEL"].upper()
            if required_level == "CRITICAL":
                log_level = logging.CRITICAL
            elif required_level == "ERROR":
                log_level = logging.ERROR
            elif required_level == "WARNING":
                log_level = logging.WARNING
            elif required_level == "INFO":
                log_level = logging.INFO
            elif required_level == "DEBUG":
                log_level = logging.DEBUG
            elif required_level == "NOTSET":
                log_level = logging.NOTSET
            else:
                raise ConfigurationValidationException(
                    f"Invalid value for log level: {required_level}"
                )

        return log_level

    @staticmethod
    def __get_external_tool(env_var):
        if env_var not in os.environ:
            raise ConfigurationValidationException(
                f"No external tool specified for ${env_var}"
            )
        file_path = os.environ[env_var]
        if not os.path.exists(file_path):
            raise ConfigurationValidationException(
                f"The following external tool was not found: {file_path}"
            )
        return file_path

    @staticmethod
    def __get_executable(env_var):
        if env_var not in os.environ:
            raise ConfigurationValidationException(
                f"No executable specified for ${env_var}"
            )
        executable = os.environ[env_var]
        executable_found = shutil.which(executable)
        if not executable_found:
            raise ConfigurationValidationException(
                f"The following executable was not found: {executable}"
            )
        return executable

    @staticmethod
    def __get_repo_scm(env_var) -> str:
        repo_scm = os.environ[env_var]
        if env_var not in os.environ:
            raise ConfigurationValidationException(f"No source code manager specified")
        if repo_scm not in AVAILABLE_SCM:
            raise ConfigurationValidationException(
                f"The following source code manager is not handled by OTTM : {repo_scm}."
                + f" Availables SCM are : {AVAILABLE_SCM}"
            )
        return repo_scm

    @staticmethod
    def __get_path_list(env_var) -> List[str]:
        path_list = {"*": []}
        if env_var in os.environ and os.environ[env_var]:
            path_list.update(json.loads(os.environ[env_var]))
        if isinstance(path_list, list):
            path_list["*"] = path_list
        return path_list

    @staticmethod
    def __get_str_list(env_var) -> List[str]:
        str_list = []
        if env_var in os.environ and os.environ[env_var]:
            str_list = os.environ[env_var].split(",")
        return str_list

    @staticmethod
    def __get_float(env_var, default):
        parsed_value = os.getenv(env_var)
        if parsed_value is None:
            return default
        try:
            parsed_float = float(parsed_value)
        except ValueError:
            raise ConfigurationValidationException(
                f"Incorrect value : {parsed_value}, {env_var} should be a float number (percentage)"
            )
        return parsed_float

    @staticmethod
    def __get_int(env_var, default):
        parsed_value = os.getenv(env_var)
        if parsed_value is None:
            return default
        try:
            parsed_int = int(parsed_value)
        except ValueError:
            raise ConfigurationValidationException(
                f"Incorrect value : {parsed_value}, {env_var} should be an int"
            )
        return parsed_int

    @staticmethod
    def __get_retry_delay(env_var):
        retry_delay_str = os.getenv(env_var, "3600")
        try:
            retry_delay = int(retry_delay_str)
        except ValueError:
            raise ConfigurationValidationException(
                f"Incorrect value : {retry_delay_str}, OTTM_RETRY_DELAY should be an integer number of seconds"
            )
        return retry_delay

    @staticmethod
    def __get_required_value(env_var):
        value = os.getenv(env_var)
        if not value:
            raise ConfigurationValidationException(f"Value for {env_var} is required")
        return value
