from sqlalchemy import Column, Integer, String, ForeignKey
from models.database import Base


class Comment(Base):
    """
    Comment
    """
    __tablename__ = "comments"
    comment_id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("project.project_id"))
    user_id = Column(String)
    timestamp = Column(String)
    feature_url = Column(String)
    rating = Column(Integer)
    comment = Column(String)
    