from abc import ABC, abstractmethod
import logging
import datetime
import json

from pydriller import Repository

from models.issue import Issue
from models.version import Version
from models.commit import Commit
from models.metric import Metric
from models.author import Author
from models.alias import Alias
from utils.timeit import timeit
from metrics.versions import compute_version_metrics

class GitConnector(ABC):
    """Connector to Github
    
    Attributes:
    -----------
     - token        Token for the SCM API
     - repo         Git repository (cloned locally, not bare repo)
     - current      Branch containing the next release (e.g. "devel")
     - session      Database connection managed by sqlachemy
     - project_id   Identifier of the project
     - directory    Folder (temporary) where the project is cloned
    """
    
    def __init__(self, project_id, directory, token, repo, current, session, config):
        self.token = token
        self.repo = repo
        self.current = current
        self.session = session
        self.project_id = project_id
        self.directory = directory
        self.configuration = config

    @timeit
    def setup_aliases(self, aliases):
        """Populate the table of aliases if any alias if defined"""
        logging.info('setup_aliases')
        if aliases:
            aliases = y = json.loads(aliases)
            for alias, alternatives in aliases.items():
                author = self.session.query(Author).filter(Author.name == alias).filter(Version.project_id == self.project_id).first()
                if not author:
                    author = Author(name=alias)
                    self.session.add(author)
                    self.session.commit()
                for alternative in alternatives:
                    syno = self.session.query(Author).filter(Author.name == alternative).filter(Version.project_id == self.project_id).first()
                    if not syno:
                        syno = Author(name=alternative)
                        self.session.add(syno)
                        self.session.commit()
                    author_alias = self.session.query(Alias).filter(Alias.name == alternative).filter(Version.project_id == self.project_id).first()
                    if not author_alias:
                        author_alias = Alias(author_id=author.author_id, name=alternative)
                        self.session.add(author_alias)
                        self.session.commit()

    @timeit
    def create_commits_from_repo(self):
        """
        Create commits into the database from GitHub commits
        Commits are not linked to version
        """
        logging.info('create_commits_from_repo')

        # Check what was the las inserted commit
        last_commit = self.session.query(Commit).filter(Commit.project_id == self.project_id).order_by(Commit.date.desc()).first()
        if last_commit is not None:
            last_synced = last_commit.date + datetime.timedelta(seconds=1)
            logging.info('Update existing database by fetching new commits since ' + str(last_synced))
            git_commits = Repository(self.directory, since=last_synced, only_no_merge=True).traverse_commits()
        else:
            logging.info('Create a database with all commits')
            git_commits = Repository(self.directory, only_no_merge=True).traverse_commits()

        commits = []
        for git_commit in git_commits:
            if git_commit.committer.name not in self.configuration.exclude_authors:

                # Fix issue #35 https://github.com/optittm/bugprediction/issues/35
                try:
                    dmm_unit_size = git_commit.dmm_unit_size
                    dmm_unit_complexity = git_commit.dmm_unit_complexity
                    dmm_unit_interfacing = git_commit.dmm_unit_interfacing
                except ValueError:
                    logging.warning(
                        f"Cannot compute DMM metrics for commit {git_commit.hash}, skipping. Issue is probably from a submodule commit"
                    )
                    dmm_unit_size = None
                    dmm_unit_complexity = None
                    dmm_unit_interfacing = None
                
                commits.append(
                    Commit(
                        project_id=self.project_id,
                        hash=git_commit.hash,
                        committer=git_commit.committer.name,
                        date=git_commit.committer_date,
                        message=git_commit.msg,
                        insertions=git_commit.insertions,
                        deletions=git_commit.deletions,
                        lines=git_commit.lines,
                        files=git_commit.files,
                        dmm_unit_size=dmm_unit_size,
                        dmm_unit_complexity=dmm_unit_complexity,
                        dmm_unit_interfacing=dmm_unit_interfacing
                    )
                )
            
        self.session.add_all(commits)
        self.session.commit()

    def compute_version_metrics(self):
        """Compute version related metics:
        - Rough volume of changes (total lines)
        - Number of issues
        - Bug velocity
        - Average seniorship of the team
        """
        compute_version_metrics(self.session, self.directory, self.project_id)
            
    def clean_next_release_metrics(self):
        """
        Clean the metrics assosciated to the current branch so as to compute them again
        """
        next_release = self.session.query(Version).filter(Version.project_id == self.project_id) \
                                                  .filter(Version.name == self.configuration.next_version_name).first()
        if next_release is None:
            logging.info("No Metrics to clean up")
        else:
            self.session.query(Metric).filter(Metric.version_id == next_release.version_id).delete()
            self.session.commit()
            logging.info("Deleted Metrics associated with version " + next_release.name)

    def populate_db(self, skip_version):
        """Populate the database from the Git API"""
        if skip_version:
            logging.info("Skipping version populate")
        else:
            self.create_versions()
        
        # Preserve the sequence below
        self.clean_next_release_metrics()
        self.create_commits_from_repo()
        self.compute_version_metrics()

    def _clean_project_existing_versions(self):
        if self.session.query(Version).filter(Version.project_id == self.project_id):
            self.session.query(Version).filter(Version.project_id == self.project_id).delete()
        self.session.commit()

    def _get_first_commit_date(self):
        commits_iterator = Repository(self.directory).traverse_commits()
        first_commit = next(commits_iterator)
        return first_commit.committer_date

    def _get_existing_issue_id(self, issue_number) -> int:
        
        existing_issue_id = None
        
        existing_issue = self.session.query(Issue) \
                    .filter(Issue.project_id == self.project_id) \
                    .filter(Issue.number == issue_number) \
                    .filter(Issue.source == "git") \
                    .first() 
        
        if existing_issue: 
            existing_issue_id = existing_issue.issue_id

        return existing_issue_id

    @abstractmethod
    def create_issues(self):
        raise NotImplementedError

    @abstractmethod
    def create_versions(self):
        raise NotImplementedError

    @abstractmethod
    def _get_issues(self, since, labels):
        raise NotImplementedError

    @abstractmethod
    def _get_releases(self, all, order_by, sort):
        raise NotImplementedError
    
    @abstractmethod
    def _get_stars(self):
        raise NotImplementedError
    
    @abstractmethod
    def _get_forks(self):
        raise NotImplementedError
    
    @abstractmethod
    def _get_watches(self):
        raise NotImplementedError