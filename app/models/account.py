import base64
from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy import or_, orm
from app.helpers.logger import logger
from app.helpers.redis_client import get_all_open_spider
from app.models import BaseModel, session
from app.models.user import User
from app.models.submit import Submit
from config import settings


class AccountStatus:
    NOT_INIT = 0
    NORMAL = 1
    QUEUE = 2
    UPDATING = 3
    UPDATE_ERROR = 4
    ACCOUNT_ERROR = 5
    RESET = 100


class Account(BaseModel):
    __tablename__ = 'accounts'

    id = Column(Integer, primary_key=True)
    nickname = Column(String(255), nullable=False)
    password_digest = Column(String(1024))
    solved = Column(Integer)
    submitted = Column(Integer)
    status = Column(Integer)
    oj_name = Column(String(32))
    user_id = Column(Integer)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)

    def __init__(self):
        pass

    def __repr__(self):
        return '<Account {} {}>'.format(self.oj_name, self.nickname)

    @property
    def password(self):
        return base64.b64decode(self.password_digest)

    @property
    def user(self):
        return session.query(User).filter_by(id=self.user_id).first()

    @property
    def submits(self):
        return session.query(Submit)\
            .filter_by(user_id=self.user_id, oj_name=self.oj_name) \
            .all()

    def set_status(self, new_status):
        self.status = new_status

    def set_general(self, solved, submitted):
        self.solved = solved
        self.submitted = submitted
        logger.info('{} 更新 solved: {} / submitted: {}'.format(self, solved, submitted))


    def save(self):
        self.updated_at = datetime.now()
        session.add(self)
        session.commit()


def init_all():
    logger.info("[AccountInit] all account which is UPDATING has changed into NOT_INIT")
    session.query(Account).filter(Account.status != AccountStatus.RESET)\
        .update({Account.status: AccountStatus.NOT_INIT})
    session.commit()


def get_available_account():
    # 最近更新的忽略掉
    all_open = get_all_open_spider()
    if len(all_open) == 0:
        return
    deadline = datetime.now() - timedelta(hours=settings.FETCH_TIMEDELTA)
    cur_account = session.query(Account)\
        .filter(Account.oj_name.in_(all_open))\
        .filter(Account.status != AccountStatus.UPDATING)\
        .filter(Account.status != AccountStatus.ACCOUNT_ERROR)\
        .filter(or_(Account.updated_at < deadline,
                    Account.status != AccountStatus.NORMAL))\
        .order_by(Account.updated_at.asc())\
        .with_for_update(nowait=True)\
        .first()
    if not cur_account:
        session.commit()
        return

    cur_account.set_status(AccountStatus.UPDATING)
    cur_account.save()
    return cur_account
