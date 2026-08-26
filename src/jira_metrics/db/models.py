from sqlalchemy import TIMESTAMP, Boolean, Column, Integer, Numeric, String, Text
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class JiraIssue(Base):
    __tablename__ = "jira_issues"

    id = Column(Integer, primary_key=True, autoincrement=True)
    issue_key = Column(String, unique=True, nullable=False)
    parent = Column(String, nullable=True)
    issue_type = Column(String, nullable=True)
    summary = Column(Text, nullable=True)
    status = Column(String, nullable=True)
    story_points = Column(Numeric, nullable=True, default=0)
    created = Column(TIMESTAMP, nullable=True)
    started = Column(TIMESTAMP, nullable=True)
    resolved = Column(TIMESTAMP, nullable=True)
    release = Column(String, nullable=True)
    assignee = Column(String, nullable=True)
    sprint_name = Column(String, nullable=True)
    priority_id = Column(String, nullable=True)
    priority_name = Column(String, nullable=True)
    has_team_label = Column(Boolean, nullable=True)
