import json
import logging
import requests
from urllib.parse import urljoin

class OttmApiServerConnector:
    """
    Connector class for retrieving OTTM Api Server infos and storing them in a database.
    """

    def __init__(self, configuration, session):
        """
        Initialize a new OttmApiServerConnector instance.

        Args:
            configuration: The api_server configuration object.
            session: The database session object.
        """
        self.configuration = configuration
        self.session = session

        self.verify_connection()


    def send_request(self, url):
        """
        Send an HTTP GET request to the specified URL.

        Args:
            url: The URL to send the request to.

        Returns:
            The JSON response as a dictionary, or None if the request fails.
        """
        try:
            # separator = '&' if '?' in url else '?'
            response = requests.get(f"{url}/projects")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"An error occurred while sending a request to {url}: {str(e)}")
            return None
        

    def send_post_request(self, url, data):
        """
        Send an HTTP POST request to the specified URL.

        Args:
            url: The URL to send the request to.

        Returns:
            The JSON response as a dictionary, or None if the request fails.
        """
        try:
            json_data = json.dumps(data)
            response = requests.post(f"{url}/bugprediction", data=json_data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"An error occurred while sending a request to {url}: {str(e)}")
            return None
        

    def get_projects(self):
        """
        Retrieve projects
        """
        if self.configuration.ottm_api_server_url != "":
            projects_reponse = self.send_request(self.configuration.ottm_api_server_url)
            projects = [p for p in projects_reponse if p['is_active']]
            return projects

    
    def post_data(self, data):
        """
        Retrieve projects
        """
        if self.configuration.ottm_api_server_url != "":
            response = self.send_post_request(self.configuration.ottm_api_server_url, data)


    def verify_connection(self):
        try:
            response = requests.get(f"{self.configuration.ottm_api_server_url}/projects")
            response.raise_for_status()
        except requests.HTTPError as e:
            # This error occurs when the method is not allowed for the called route
            # It means the server is reachable
            # So we don't raise the status error
            if e.response.status_code != 405:
                raise e
        except requests.ConnectionError:
            logging.error("OTTM API Server is unreachable.")
            raise ConnectionError("OTTM API Server is unreachable.")
    

    def map_api_response_to_toolsource(self, ottm_api_response: dict):
        if not ottm_api_response:
            return None

        if ottm_api_response["connectors"]:
            connector = ottm_api_response["connectors"][0]

            return {
                "id" : ottm_api_response["id"],
                "category": connector["category"],
                "tool_name": connector["tool_name"],
                "project_name": connector["project_name"],
                "api": connector["api"],
                "synced": connector["synced"],
                "auth_mode": connector["auth_mode"],
                "token": connector["auth_data"]["token"]
            }
        
        return None
    
    def get_tool_by_project(self, project_id: str):
        try:
            url = urljoin(self.configuration.ottm_api_server_url, "/".join(("tools", "projects", project_id, "secret")))
            url = urljoin(url, "?tool_name=bugprediction")

            response = requests.get(url)
            response.raise_for_status()
            return self.map_api_response_to_toolsource(response.json())
        except requests.exceptions.RequestException as e:
            logging.error(f"An error occurred while sending a request to {url}: {str(e)}")
            return None
