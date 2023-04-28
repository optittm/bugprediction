from sqlalchemy import Column, Integer, String, ForeignKey
from models.database import Base


class Comment(Base):
    """
    Comment
    """
    __tablename__ = "comment"
    comment_id = Column(Integer, primary_key=True)
    project_name = Column(Integer, ForeignKey("project.name"))
    user_id = Column(String)
    timestamp = Column(String)
    feature_url = Column(String)
    rating = Column(Integer)
    comment = Column(String)


