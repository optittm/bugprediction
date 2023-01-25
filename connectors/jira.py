import logging
from time import sleep
import requests
from jira import JIRA


from sqlalchemy import desc

from models.issue import Issue
from utils.timeit import timeit
from datetime import datetime, timedelta

requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

class JiraConnector:
    
    def __init__(self, project_id, session, config) -> None:
        self.config = config
        self.session = session
        self.project_id = project_id
        self.__client = JIRA(
                                server=self.config.jira_base_url,
                                basic_auth=(self.config.jira_email, self.config.jira_token))
        
    def _get_issues(self, since=None, labels=None, source='jira'):
        if not since:
            since = None
        if not labels:
            labels = None

        if(source == 'jira'):
            return self.__client.search_issues('project=%s AND labels IN (%s)' % (self.config.jira_project, ','.join(labels)) if labels and len(labels) > 0
                                                else 'project=%s' % (self.config.jira_project))


    @timeit
    def create_issues(self):
        """
        Create issues into the database from Jira Issues
        """
        logging.info('JiraConnector: create_issues')

        # Check if a database already exist
        last_issue = self.session.query(Issue) \
                         .filter(Issue.project_id == self.project_id and Issue.source == 'jira') \
                         .order_by(desc(Issue.updated_at)).first()
        
        if last_issue is not None:
            if not self.config.issue_tags:
                jira_issues = self._get_issues(since=last_issue.updated_at + timedelta(seconds=1), labels=None)
            else:
                jira_issues = self._get_issues(since=last_issue.updated_at + timedelta(seconds=1),
                                               labels=self.config.issue_tags)
        else:
            if not self.config.issue_tags:
                jira_issues = self._get_issues()
            else:
                jira_issues = self._get_issues(labels=self.config.issue_tags)

        
        logging.info('Syncing ' + str(len(jira_issues)) + ' issue(s) from Jira')

        bugs = []

        for issue in jira_issues:

            if issue.fields.reporter not in self.config.exclude_issuers:
                bugs.append(
                    Issue(
                        project_id=self.project_id,
                        number=issue.key,
                        title=issue.fields.summary,
                        source="jira",
                        created_at=datetime.strptime(issue.fields.created, '%Y-%m-%dT%H:%M:%S.%f%z'),
                        updated_at=datetime.strptime(
                            issue.fields.created if len(issue.fields.worklog.worklogs) == 0 
                            else issue.fields.worklog.worklogs[-1].updated, '%Y-%m-%dT%H:%M:%S.%f%z')
                    )
                )

        self.session.add_all(bugs)
        self.session.commit()