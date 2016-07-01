from . import BaseModel, Session
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship, backref

session = Session()


class AccountStatus:
    NORMAL = 0
    NOT_INIT = 1
    WAIT_FOR_UPDATE = 2
    UPDATING = 3
    UPDATE_ERROR = 4
    ACCOUNT_ERROR = 5


class Account(BaseModel):
    id = Column(Integer, primary_key=True)
    nickname = Column(String(20), nullable=False)
    password_hash = Column(String(128))
    solved_or_rating = Column(Integer, nullable=False, default=0)
    submitted_or_max_rating = Column(Integer, nullable=False, default=0)
    update_status = Column(Integer, default=1, index=True)
    oj_name = Column(String(20), nullable=False)
    last_update_time = Column(DateTime)

    # connect to User
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship('User', backref=backref('account', lazy='dynamic'))

    def __init__(self):
        pass

    def __repr__(self):
        return '<%s Account %s>: %d / %d' % (self.oj_name, self.nickname,
                                             self.solved_or_rating,
                                             self.submitted_or_max_rating)

    def save(self):
        session.add(self)
        session.commit()

    def delete(self):
        session.delete(self)
        session.commit()
