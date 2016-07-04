from . import BaseModel, Session
from sqlalchemy import Column, Integer, String, Boolean, DateTime

session = Session()


class User(BaseModel):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    username = Column(String(25), unique=True, index=True, nullable=False)
    name = Column(String(25))
    password_hash = Column(String(128))
    stu_id = Column(String(20))
    gender = Column(Boolean)
    email = Column(String(65))
    phone = Column(String(15))
    remark = Column(String(50))
    school = Column(String(20), nullable=False)
    situation = Column(String(50))
    score = Column(Integer, default=0)
    current_week_submit = Column(Integer, default=0)
    current_week_solved = Column(Integer, default=0)
    last_week_submit = Column(Integer, default=0)
    last_week_solved = Column(Integer, default=0)
    create_time = Column(DateTime)
    rights = Column(Integer)
    active = Column(Integer, default=1)

    def __init__(self):
        pass

    def __repr__(self):
        return '<User %s>' % self.name

    def save(self):
        session.add(self)
        session.commit()

    def delete(self):
        session.delete(self)
        session.commit()
