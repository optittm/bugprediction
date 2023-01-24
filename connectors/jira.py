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

        for issue in self.__client.search_issues('project=%s AND labels IN (%s)' % (self.config.jira_project, labels) if len(labels) > 0
                                                 else 'project=%s' % (self.config.jira_project)):

            if issue.fields.reporter not in self.config.exclude_issuers:
                issueFiltered = Issue(
                                        project_id=self.project_id,
                                        number=issue.key,
                                        title=issue.fields.summary,
                                        created_at=datetime.strptime(issue.fields.created, '%Y-%m-%dT%H:%M:%S.%f%z'),
                                        updated_at=datetime.strptime(
                                                                    issue.fields.created if len(issue.fields.worklog.worklogs) == 0 
                                                                    else issue.fields.worklog.worklogs[-1].updated, '%Y-%m-%dT%H:%M:%S.%f%z')
                                     )

                issues.append(issueFiltered)

        self.session.add_all(issues)
        self.session.commit()