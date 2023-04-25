import logging
import requests

class SurveyAPIConnector:
    def __init__(self, config, session):
        self.configuration = config
        self.session=session

    def get_comments(self):
       
        response= requests.get(f"{self.configuration.survey_back_api_url}/comments")
        response.raise_for_status()
        print ("---------------------ici---------------------------",response.json())
        return response.json()

    def save_comments_to_db(self, comments):
        try:
            # Save comments into the database
            self.session.add(comments)
            self.session.commit()
            logging.info("Comments added to database")
        except Exception as e:
            logging.error("An error occurred while saving Comments")
            logging.error(str(e))
