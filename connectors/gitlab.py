import logging
from time import sleep
from typing import List, Union
import gitlab

from sqlalchemy import desc, update

from models.issue import Issue
from models.version import Version
from utils.date import date_iso_8601_to_datetime
from utils.timeit import timeit
from connectors.git import GitConnector
from gitlab import Gitlab
from gitlab.v4.objects.tags import ProjectTag
from gitlab.v4.objects.releases import ProjectRelease
from datetime import datetime, timedelta

class GitLabConnector(GitConnector):
    """
    Connector to GitLab

    Attributes:
    -----------
     - base_url     URL to GitLab, empty if gitlab.com
    """
    def __init__(self, project_id, directory, base_url, token, repo, current, session, config):
        GitConnector.__init__(self, project_id, directory, token, repo, current, session, config)
        if not base_url and not self.token:
            logging.info("anonymous read-only access for public resources (GitLab.com)")
            self.api = Gitlab()
        if base_url and self.token:
            logging.info("private token or personal token authentication (self-hosted GitLab instance)")
            self.api = Gitlab(url=base_url, private_token=self.token)
        if not base_url and self.token:
            logging.info("private token or personal token authentication (GitLab.com)")
            self.api = Gitlab(private_token=self.token)
        
        # Check the authentification. Doesn't work for public read only access
        if base_url or self.token:
            self.api.auth()

        self.remote = self.api.projects.get(self.repo)

    def _get_issues(self, since=None, labels=None):
        if not since:
            since = None
        if not labels:
            labels = None

        try:
            return self.remote.issues.list(state="all", since=since, with_labels_details=labels, get_all=True)
        except gitlab.GitlabJobRetryError:
            sleep(self.configuration.retry_delay)
            self._get_issues(since, labels)
    
    def _get_git_versions(self, all=None, order_by=None, sort=None) -> List[Union[ProjectRelease, ProjectTag]]:
        if not all:
            all = None
        if not order_by:
            order_by = None
        if not sort:
            sort = None
        
        try:
            if self.configuration.use_all_tags:
                return self.remote.tags.list(all=all, order_by=order_by, sort=sort)
            else:
                return self.remote.releases.list(all=all, order_by=order_by, sort=sort)
        except gitlab.GitlabJobRetryError:
            sleep(self.configuration.retry_delay)
            self._get_git_versions(all, order_by, sort)
        
    @timeit
    def create_issues(self):
        """
        Create issues into the database from GitLab Issues
        """
        logging.info('GitLabConnector: create_issues')

        # Check if a database already exist
        last_issue = self.session.query(Issue) \
                         .filter(Issue.project_id == self.project_id) \
                         .filter(Issue.source == 'git') \
                         .order_by(desc(Issue.updated_at)).first()
        if last_issue is not None:
            # Update existing database by fetching new issues
            if not self.configuration.issue_tags:
                git_issues = self._get_issues(since=last_issue.updated_at + timedelta(seconds=1), labels=None)
            else:
                git_issues = self._get_issues(since=last_issue.updated_at + timedelta(seconds=1),
                                                    labels=self.configuration.issue_tags)  # e.g. Filter by labels=['bug']
        else:
            # Create a database with all issues
            if not self.configuration.issue_tags:
                git_issues = self._get_issues(since=None, labels=None)
            else:
                git_issues = self._get_issues(labels=self.configuration.issue_tags)    # e.g. Filter by labels=['bug']
        
        # versions = self.session.query(Version).all
        logging.info('Syncing ' + str(len(git_issues)) + ' issue(s) from GitLab')

        new_bugs = []
        # for version in versions:
        for issue in git_issues:
            # Check if the issue is linked to a selected version (included or not +IN?.§ .?NBVCXd)
            # if version.end_date > issue.created_at > version.start_date:
            if issue.author['username'] not in self.configuration.exclude_issuers:
                
                updated_issue_date = date_iso_8601_to_datetime(issue.updated_at)
                existing_issue_id = self._get_existing_issue_id(issue.iid)

                if existing_issue_id:
                    logging.info("Issue %s already exists, updating it", existing_issue_id)
                    self.session.execute(
                        update(Issue).where(Issue.issue_id == existing_issue_id) \
                                     .values(title=issue.title, updated_at=updated_issue_date)
                    )
                else:
                    new_bugs.append(
                        Issue(
                            project_id=self.project_id,
                            title=issue.title,
                            number=issue.iid,
                            source="git",
                            created_at=date_iso_8601_to_datetime(issue.created_at),
                            updated_at=updated_issue_date,
                        )
                    )

        self.session.add_all(new_bugs)
        self.session.commit()
    
    @timeit
    def create_versions(self):
        """
        Create versions into the database from GitLab releases
        """
        logging.info('GitLabConnector: create_versions')
        if self.configuration.use_all_tags:
            git_versions = self._get_git_versions(all=True, order_by="updated", sort="asc")
        else:
            git_versions = self._get_git_versions(all=True, order_by="released_at", sort="asc")
        self._clean_project_existing_versions()

        versions = []
        previous_release_published_at = self._get_first_commit_date()

        for v in git_versions:
            if type(v) is ProjectRelease:
                release_published_at = date_iso_8601_to_datetime(v.released_at)
                versions.append(
                    Version(
                        project_id=self.project_id,
                        name=v.name,
                        tag=v.tag_name,
                        start_date=previous_release_published_at,
                        end_date=release_published_at,
                    )
                )
                previous_release_published_at = release_published_at
            elif type(v) is ProjectTag:
                release_published_at = date_iso_8601_to_datetime(v.commit["committed_date"])
                versions.append(
                    Version(
                        project_id=self.project_id,
                        name=v.name,
                        tag=v.name,
                        start_date=previous_release_published_at,
                        end_date=release_published_at,
                    )
                )
                previous_release_published_at = release_published_at

        # Put current branch at the end of the list
        versions.append(
            Version(
                project_id=self.project_id,
                name=self.configuration.next_version_name,
                tag=self.current,
                start_date=previous_release_published_at,
                end_date=datetime.now(),
            )
        )
        self.session.add_all(versions)
        self.session.commit()
