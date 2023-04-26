import logging
import requests

from models.comment import Comment

class SurveyAPIConnector:
    def __init__(self, config, session):
        self.configuration=config
        self.session=session

    def get_comments(self):
        response=requests.get(f"{self.configuration.survey_back_api_url}/comments")
        response.raise_for_status()
        comments_json=response.json()
        comments = []
        for comment_json in comments_json:
            
            comment=Comment(
                comment_id=comment_json['id'],
                project_name=comment_json['project_name'],
                user_id=comment_json['user_id'],
                timestamp=comment_json['timestamp'],
                feature_url=comment_json['feature_url'],
                rating=comment_json['rating'],
                comment=comment_json['comment']
            )
           
            if comment.project_name==self.configuration.survey_project_name or self.configuration.survey_project_name=="":

                comments.append(comment)


        return comments

    def save_comments_to_db(self, comments):
        try:
            for comment in comments:
            # Check if comment already exists in the database
                if not self.session.query(Comment).filter_by(comment_id=comment.comment_id).first():
                    self.session.add(comment)
            self.session.commit()
            logging.info("Comments added to database")
        except Exception as e:
            logging.error("An error occurred while saving Comments")
            logging.error(str(e))