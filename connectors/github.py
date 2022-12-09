import logging

from sqlalchemy import desc
from unicodedata import name

import models
from models.issue import Issue
from models.version import Version
from models.commit import Commit
from github import Github
import datetime
from sqlalchemy.sql import func
from connectors.git import GitConnector
from utils.timeit import timeit

class GitHubConnector(GitConnector):
    """
    Connector to Github
    """

    def __init__(self, token, repo, current, session, project_id, directory):
        GitConnector.__init__(self, token, repo, current, session, project_id, directory)
        self.api = Github(self.token)
        self.remote = self.api.get_repo(self.repo)

    @timeit
    def create_issues(self):
        """
        Create issues into the database from GitHub Issues
        """
        logging.info('GitHubConnector: create_issues')

        # Check if a database already exist
        last_issue = self.session.query(Issue) \
                         .filter(Issue.project_id == self.project_id) \
                         .order_by(desc(models.issue.Issue.updated_at)).get(1)
        if last_issue is not None:
            # Update existing database by fetching new issues
            if not self.configuration.issue_tags:
                git_issues = self.remote.get_issues(state="all", since=last_issue.updated_at + datetime.timedelta(seconds=1))
            else:
                git_issues = self.remote.get_issues(state="all", since=last_issue.updated_at + datetime.timedelta(seconds=1),
                                            labels=self.configuration.issue_tags)  # e.g. Filter by labels=['bug']
        else:
            # Create a database with all issues
            if not self.configuration.issue_tags:
                git_issues = self.remote.get_issues(state="all")
            else:
                git_issues = self.remote.get_issues(state="all", labels=self.configuration.issue_tags)  # e.g. Filter by labels=['bug']

        # versions = self.session.query(Version).all()
        logging.info('Syncing ' + str(git_issues.totalCount) + ' issue(s) from GitHub')

        bugs = []
        # for version in versions:
        for issue in git_issues:
            # Check if the issue is linked to a selected version (included or not excluded)
            # if version.end_date > issue.created_at > version.start_date:
            if issue.user.login not in self.configuration.exclude_issuers:
                bugs.append(
                    Issue(
                        project_id=self.project_id,
                        title=issue.title,
                        number=issue.number,
                        created_at=issue.created_at,
                        updated_at=issue.updated_at
                    )
                )
        
        # Remove potential duplicated values
        # list(dict.fromkeys(bugs))
        self.session.add_all(bugs)
        self.session.commit()

    @timeit
    def create_versions(self):
        """
        Create versions into the database from GitHub tags
        """
        logging.info('GitHubConnector: create_versions')
        releases = self.remote.get_releases()
        self._clean_project_existing_versions()

        versions = []
        previous_release_published_at = self._get_first_commit_date()

        for release in releases.reversed:
            versions.append(
                Version(
                    project_id=self.project_id,
                    name=release.title,
                    tag=release.tag_name,
                    start_date=previous_release_published_at,
                    end_date=release.published_at,
                )
            )
            previous_release_published_at = release.published_at

        # Put current branch at the end of the list
        versions.append(
            Version(
                project_id=self.project_id, 
                name="Next Release",
                tag=self.current, 
                start_date=previous_release_published_at,
                end_date=datetime.datetime.now(),
            )
        )
        self.session.add_all(versions)
        self.session.commit()