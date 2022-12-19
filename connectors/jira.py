import logging
from jira import JIRA
import requests

from configuration import Configuration

requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

class JiraConnector():
    """
    Connector to Jira
    """
    def __init__(self, base_url, emailAddress, token) -> None:
        self.__client = JIRA(server=base_url, basic_auth=(emailAddress, token))
        self.configuration = Configuration()
  
    def _get_projects(self, raw = False):

        logging.info(self.__client)
        projects = []
        for project in self.__client.projects():
            if raw:
                projects.append(project)
            else:
                projects.append({ 'Name':project.key, 'Description': project.name })
        return projects
