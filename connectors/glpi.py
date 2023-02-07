import logging

from glpi_api import GLPI
from sqlalchemy import update

from models.issue import Issue
from utils.date import date_to_datetime
from utils.timeit import timeit

class GlpiConnector:

    def __init__(self, project_id, session, config) -> None:
        self.config = config
        self.session = session
        self.project_id = project_id
        self.glpi = GLPI(url=self.config.glpi_base_url,
                         apptoken=self.config.glpi_app_token,
                         auth=(self.config.glpi_username, self.config.glpi_password))
    
    @timeit
    def create_issues(self):
        """
        Create issues into the database from Glpi Issues
        """
        logging.info('GlpiConnector: create_issues')

        glpi_issues = self._get_issues()

        logging.info('Syncing ' + str(len(glpi_issues)) + ' issue(s) from Glpi')

        self.__save_issues(glpi_issues)

    def _get_issues(self):
        return self.glpi.get_all_items('Ticket')
    
    def __save_issues(self, glpi_issues) -> None:
        new_ottm_issues = []

        for issue in glpi_issues:
            if issue['users_id_recipient'] not in self.config.exclude_issuers:
                existing_issue_id = self.__get_existing_issue_id(issue['id'])

                if existing_issue_id:
                    logging.info("Issue %s already exists, updating it", existing_issue_id)
                    self.session.execute(
                        update(Issue).where(Issue.issue_id == existing_issue_id) \
                                    .values(title=issue['name'], updated_at=date_to_datetime(issue['date_mod']))
                    )
                else:
                    ottm_issue = Issue(
                        project_id=self.project_id,
                        number=issue['id'],
                        title=issue['name'],
                        source="glpi",
                        created_at=date_to_datetime(issue['date']),
                        updated_at=date_to_datetime(issue['date_mod']),
                    )
                    new_ottm_issues.append(ottm_issue)
        
        self.session.add_all(new_ottm_issues)
        self.session.commit()

    def __get_existing_issue_id(self, issue_number) -> int:
        existing_issue_id = None

        existing_issue = self.session.query(Issue) \
                    .filter(Issue.project_id == self.project_id) \
                    .filter(Issue.number == issue_number) \
                    .filter(Issue.source == "glpi") \
                    .first()
        
        if existing_issue:
            existing_issue_id = existing_issue.issue_id
        
        return existing_issue_id