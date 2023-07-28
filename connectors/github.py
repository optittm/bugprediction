import logging
from time import sleep, time
from typing import List, Union
import github

from sqlalchemy import desc, update

import models
from models.issue import Issue
from models.version import Version
from github import Github
from github.GitRelease import GitRelease
from github.Tag import Tag
from github.PaginatedList import PaginatedList
import datetime
from connectors.git import GitConnector
from utils.timeit import timeit


class GitHubConnector(GitConnector):
    """
    Connector to Github
    """

    def __init__(self, project_id, directory, token, repo, current, session, config):
        GitConnector.__init__(
            self, project_id, directory, token, repo, current, session, config
        )
        self.api = Github(self.token)
        self.remote = self.api.get_repo(self.repo)

    def _get_issues(self, since=None, labels=None):
        if not since:
            since = github.GithubObject.NotSet
        if not labels:
            labels = github.GithubObject.NotSet

        try:
            return self.remote.get_issues(state="all", since=since, labels=labels)
        except github.GithubException.RateLimitExceededException:
            sleep(self.configuration.retry_delay)
            self._get_issues(since, labels)

    def _get_git_versions(
        self, all=None, order_by=None, sort=None
    ) -> List[Union[GitRelease, Tag]]:
        if not all:
            all = None
        if not order_by:
            order_by = None
        if not sort:
            sort = None

        try:
            if self.configuration.use_all_tags:
                return self.remote.get_tags()
            else:
                return self.remote.get_releases()
        except github.GithubException.RateLimitExceededException:
            sleep(self.configuration.retry_delay)
            self._get_git_versions(all, order_by, sort)

    @timeit
    def create_issues(self):
        """
        Create issues into the database from GitHub Issues
        """
        logging.info("GitHubConnector: create_issues")

        # Check if a database already exist
        last_issue = (
            self.session.query(Issue)
            .filter(Issue.project_id == self.project_id)
            .filter(Issue.source == "git")
            .order_by(desc(models.issue.Issue.updated_at))
            .first()
        )
        if last_issue is not None:
            # Update existing database by fetching new issues
            if not self.configuration.issue_tags:
                git_issues = self._get_issues(
                    since=last_issue.updated_at + datetime.timedelta(seconds=1)
                )
            else:
                git_issues = self._get_issues(
                    since=last_issue.updated_at + datetime.timedelta(seconds=1),
                    labels=self.configuration.issue_tags,
                )  # e.g. Filter by labels=['bug']
        else:
            # Create a database with all issues
            if not self.configuration.issue_tags:
                git_issues = self._get_issues()
            else:
                git_issues = self._get_issues(
                    labels=self.configuration.issue_tags
                )  # e.g. Filter by labels=['bug']

        # versions = self.session.query(Version).all()
        logging.info("Syncing " + str(git_issues.totalCount) + " issue(s) from GitHub")

        new_bugs = []
        # for version in versions:
        for issue in git_issues:
            # Check if the issue is linked to a selected version (included or not excluded)
            # if version.end_date > issue.created_at > version.start_date:
            if issue.user.login not in self.configuration.exclude_issuers:
                existing_issue_id = self._get_existing_issue_id(issue.number)

                if existing_issue_id:
                    logging.info(
                        "Issue %s already exists, updating it", existing_issue_id
                    )
                    self.session.execute(
                        update(Issue)
                        .where(Issue.issue_id == existing_issue_id)
                        .values(title=issue.title, updated_at=issue.updated_at)
                    )
                else:
                    new_bugs.append(
                        Issue(
                            project_id=self.project_id,
                            title=issue.title,
                            number=issue.number,
                            source="git",
                            created_at=issue.created_at,
                            updated_at=issue.updated_at,
                        )
                    )

        # Remove potential duplicated values
        # list(dict.fromkeys(bugs))
        self.session.add_all(new_bugs)
        self.session.commit()

    @timeit
    def create_versions(self):
        """
        Create versions into the database from GitHub tags
        """
        logging.info("GitHubConnector: create_versions")
        git_versions = self._get_git_versions()
        self._clean_project_existing_versions()

        versions = []
        previous_release_published_at = self._get_first_commit_date()

        stars = list(self.remote.get_stargazers_with_dates())
        forks = list(self.remote.get_forks())
        subscribers = list(self.remote.get_subscribers())

        for v in git_versions.reversed:
            if type(v) is GitRelease:
                v_name = v.title
                v_tag = v.tag_name
                v_end_date = v.published_at
            elif type(v) is Tag:
                v_name = v.name
                v_tag = v.name
                v_end_date = v.commit.commit.committer.date

            # Set UTC Timezone for previous release and release published_at when they are None
            if previous_release_published_at.tzinfo is None:
                previous_release_published_at = (
                    previous_release_published_at.astimezone(datetime.timezone.utc)
                )

            if v_end_date.tzinfo is None:
                release_published_at_timezone = v_end_date.astimezone(
                    datetime.timezone.utc
                )

            versions.append(
                Version(
                    project_id=self.project_id,
                    name=v_name,
                    tag=v_tag,
                    start_date=previous_release_published_at,
                    end_date=v_end_date,
                    stars=len(
                        list(
                            filter(
                                # Set timezone of star starred_at to UTC
                                lambda star: star.starred_at.astimezone(
                                    datetime.timezone.utc
                                )
                                >= previous_release_published_at
                                and star.starred_at.astimezone(datetime.timezone.utc)
                                <= release_published_at_timezone,
                                stars,
                            )
                        )
                    ),
                    forks=len(
                        list(
                            filter(
                                # Set timezone of fork created_at to UTC
                                lambda fork: fork.created_at.astimezone(
                                    datetime.timezone.utc
                                )
                                >= previous_release_published_at
                                and fork.created_at.astimezone(datetime.timezone.utc)
                                <= release_published_at_timezone,
                                forks,
                            )
                        )
                    ),
                    subscribers=len(
                        list(
                            filter(
                                # Set timezone of subscriber created_at to UTC
                                lambda subscriber: subscriber.created_at.astimezone(
                                    datetime.timezone.utc
                                )
                                >= previous_release_published_at
                                and subscriber.created_at.astimezone(
                                    datetime.timezone.utc
                                )
                                <= release_published_at_timezone,
                                subscribers,
                            )
                        )
                    ),
                )
            )
            previous_release_published_at = v_end_date

        # Put current branch at the end of the list
        # Set UTC Timezone for previous release published_at when it's None
        if previous_release_published_at.tzinfo is None:
            previous_release_published_at = previous_release_published_at.astimezone(
                datetime.timezone.utc
            )

        versions.append(
            Version(
                project_id=self.project_id,
                name=self.configuration.next_version_name,
                tag=self.current,
                start_date=previous_release_published_at,
                end_date=datetime.datetime.now(
                    datetime.timezone.utc
                ),  # Set timezone of star starred_at to UTC
                stars=len(
                    list(
                        filter(
                            lambda star: star.starred_at.astimezone(
                                datetime.timezone.utc
                            )
                            >= previous_release_published_at,
                            stars,
                        )
                    )
                ),
                forks=len(
                    list(
                        filter(
                            lambda fork: fork.created_at.astimezone(
                                datetime.timezone.utc
                            )
                            >= previous_release_published_at,
                            forks,
                        )
                    )
                ),
                subscribers=len(
                    list(
                        filter(
                            lambda subscriber: subscriber.created_at.astimezone(
                                datetime.timezone.utc
                            )
                            >= previous_release_published_at,
                            subscribers,
                        )
                    )
                ),
            )
        )
        self.session.add_all(versions)
        self.session.commit()
