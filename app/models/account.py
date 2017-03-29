import base64
from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, DateTime
from tornado import gen

from app.helpers.logger import logger
from app.helpers.redis_utils import get_all_open_spider
from app.helpers.thread_pool import ThreadPool
from app.models import BaseModel, session
from app.models.submit import Submit
from app.models.user import User
from config import settings
from app.models.user_info import UserInfo


def update_train_rank(user_id):
    logger.info('[Account] update_train_rank <User #{}>'.format(user_id))
    user_info = session.query(UserInfo).filter_by(user_id=user_id).first()
    if user_info is None:
        logger.warn("[Account] update_train_rank => UserInfo of User #{} does't exists".format(user_id))
        return
    accounts = session.query(Account).filter_by(user_id=user_id)
    ranks = []
    for account in accounts:
        solved, submitted = account.solved, account.submitted
        oj_name = account.oj_name
        top_account = session.query(Account).filter_by(oj_name=oj_name)\
            .order_by(Account.solved.desc(), Account.submitted.desc())\
            .first()
        max_solved = max(top_account.solved, solved)
        if max_solved == 0:
            this_rank = 1000
        else:
            this_rank = (solved / max_solved) * 1000
        ranks.append(this_rank)
        logger.debug("[Account] update_train_rank <User #{}> {} => {}".format(user_id, oj_name, this_rank))
    end_rank = sum(ranks) / len(ranks)
    user_info.train_rank = end_rank
    user_info.save()
    logger.info("[Account] update_train_rank success <User #{}> => {}".format(user_id, end_rank))



class AccountStatus:
    NOT_INIT = 0
    NORMAL = 1
    QUEUE = 2
    UPDATING = 3
    UPDATE_ERROR = 4
    ACCOUNT_ERROR = 5
    STOP = 100


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

    @property
    def should_throttle(self):
        deadline = datetime.now() - timedelta(minutes=settings.FETCH_TIMEDELTA)
        return self.updated_at >= deadline and self.status != AccountStatus.NOT_INIT

    def set_status(self, new_status):
        self.status = new_status

    @gen.coroutine
    def set_general(self, solved, submitted):
        self.solved = solved
        self.submitted = submitted
        self.save()
        yield ThreadPool.submit(update_train_rank, self.user_id)
        logger.info('{} 更新 solved: {} / submitted: {}'.format(self, solved, submitted))

    def save(self):
        self.updated_at = datetime.now()
        session.add(self)
        session.commit()


def init_all():
    logger.info("[AccountInit] 所有非 [NOT_INIT, STOP] 账号已经重置为 NORMAL")
    session.query(Account)\
        .filter(~Account.status.in_([AccountStatus.NOT_INIT, AccountStatus.STOP]))\
        .update({Account.status: AccountStatus.NORMAL}, synchronize_session=False)
    session.commit()


def get_available_account():
    # 最近更新的忽略掉
    all_open = get_all_open_spider()
    if len(all_open) == 0:
        return

    deadline = datetime.now() - timedelta(minutes=settings.FETCH_TIMEDELTA)
    cur_account = session.query(Account)\
        .filter(Account.oj_name.in_(all_open))\
        .filter(~Account.status.in_([AccountStatus.QUEUE,
                                     AccountStatus.STOP,
                                     AccountStatus.UPDATING,
                                     AccountStatus.ACCOUNT_ERROR]))\
        .filter(Account.updated_at < deadline)\
        .order_by(Account.updated_at.asc())\
        .with_for_update(nowait=True)\
        .first()
    if not cur_account:
        session.commit()
        return

    cur_account.set_status(AccountStatus.QUEUE)
    cur_account.save()
    return cur_account
