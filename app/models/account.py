import settings
from . import BaseModel, Session
from .user import User
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy import or_, orm
from datetime import datetime, timedelta

session = Session()


class AccountStatus:
    NOT_INIT = 0
    NORMAL = 1
    WAIT_FOR_UPDATE = 2
    UPDATING = 3
    UPDATE_ERROR = 4
    ACCOUNT_ERROR = 5


class Account(BaseModel):
    __tablename__ = 'account'

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
    user = orm.relationship('User', backref=orm.backref('account', lazy='dynamic'))

    def __init__(self):
        pass

    def __repr__(self):
        return '<Account %s %s>' % (self.oj_name, self.nickname)

    def set_updating(self):
        self.update_status = AccountStatus.UPDATING

    def set_normal(self):
        self.update_status = AccountStatus.NORMAL

    def set_error(self):
        self.update_status = AccountStatus.UPDATE_ERROR

    def set_account_error(self):
        self.update_status = AccountStatus.ACCOUNT_ERROR

    def save(self):
        session.add(self)
        session.commit()

    def delete(self):
        session.delete(self)
        session.commit()


def init_all():
    session.query(Account).filter(Account.update_status == AccountStatus.UPDATING)\
        .update({Account.update_status: AccountStatus.NOT_INIT})
    session.commit()


def get_available_account():
    # 最近更新的忽略掉
    deadline = datetime.now() - timedelta(hours=settings.FETCH_TIMEDELTA)
    cur_account = session.query(Account).filter(Account.update_status != AccountStatus.UPDATING)\
        .filter(Account.update_status != AccountStatus.ACCOUNT_ERROR)\
        .filter(or_(Account.last_update_time < deadline,
                    Account.update_status != AccountStatus.NORMAL))\
        .order_by(Account.last_update_time.asc())\
        .with_for_update(nowait=True)\
        .first()
    if not cur_account:
        session.commit()
        return

    cur_account.set_updating()
    cur_account.save()
    return cur_account

