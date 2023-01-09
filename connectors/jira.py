import logging
import requests
from jira import JIRA


from models.issue import Issue
from datetime import datetime

requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

class JiraConnector:
    
    def __init__(self, project_id, session, config) -> None:
        self.config = config
        self.session = session
        self.project_id = project_id
        self.__client = JIRA(
                                server=self.config.jira_base_url,
                                basic_auth=(self.config.jira_email, self.config.jira_token))

    def create_issues(self, labels):
        """Populate the database from the Jira API"""
        logging.info('JiraConnector: create_issues')

        issues = []

        for issue in self.__client.search_issues(f"project={self.config.jira_project}"):
            issueFiltered = Issue(
                                    project_id=self.project_id,
                                    number=issue.key,
                                    title=issue.fields.summary,
                                    created_at=datetime.strptime(issue.fields.created, '%Y-%m-%dT%H:%M:%S.%f%z'))

            if len(labels) == 0:
                issues.append(issueFiltered)
            else:
                for label in labels.split(","):
                    if label.strip() in issue.fields.labels and issueFiltered not in issues:
                        issues.append(issueFiltered)

        self.session.add_all(issues)
        self.session.commit()