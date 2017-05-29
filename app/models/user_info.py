from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime

from app.models import BaseModel, session


class UserInfo(BaseModel):
    __tablename__ = 'user_infos'

    id = Column(Integer, primary_key=True)
    email = Column(String(255))
    stu_id = Column(String(255))
    phone = Column(String(255))
    school = Column(String(255))
    college = Column(String(255))
    major = Column(String(255))
    grade = Column(String(255))
    situation = Column(String(255))


    user_id = Column(Integer)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)

    def __init__(self):
        pass

    def __repr__(self):
        return '<UserInfo user {}>'.format(self.user_id)

    def save(self):
        self.updated_at = datetime.now()
        session.add(self)
        session.commit()
