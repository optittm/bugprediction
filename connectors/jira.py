import logging
from jira import JIRA
import requests

from configuration import Configuration
from models.issue import Issue

requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

class JiraConnector():
    """
    Connector to Jira
    """
    def __init__(self, base_url, emailAddress, token) -> None:
        self.__client = JIRA(server=base_url, basic_auth=(emailAddress, token))
        self.configuration = Configuration()

    def _get_issues(self, labels=["bug","enhancement"]):
        issues = []

        for issue in self.__client.search_issues(f"project={self.configuration.jira_project}"):
            for label in labels:
                issueFiltered = {"number":issue.key, "title":issue.fields.summary, "created_at":issue.fields.created}
                
                if label in issue.fields.labels and issueFiltered not in issues:
                    project_id = issue.fields.project.name #KO

                    issues.append(issueFiltered)

        return issues