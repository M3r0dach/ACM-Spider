import base64
from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, DateTime, func
from tornado import gen

from app.helpers.logger import logger
from app.helpers.redis_utils import get_all_open_spider
from app.helpers.thread_pool import ThreadPool
from app.models import BaseModel, session
from app.models.submit import Submit
from app.models.user import User
from config import settings


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
        return False

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


def update_train_rank(user_id):
    user = session.query(User).filter_by(id=user_id).first()
    logger.info('[Account] update_train_rank #{}'.format(user))
    if user is None:
        logger.warn("[Account] update_train_rank => UserInfo of #{} does't exists".format(user))
        return

    ranks = []
    # normal_oj => sum(solved) / sum(top_solved)
    normal_oj = ['bnu', 'hdu', 'poj', 'vj']
    accounts = session.query(Account).filter_by(user_id=user_id)\
        .filter(Account.oj_name.in_(normal_oj))
    solved_sum = sum([account.solved for account in accounts])
    top_account = session.query(func.sum(Account.solved), Account.user_id)\
        .filter(Account.oj_name.in_(normal_oj))\
        .group_by(Account.user_id)\
        .order_by(func.sum(Account.solved).desc())\
        .first()
    if top_account:
        top_solved_sum = int(top_account[0])
        this_rank = (solved_sum / top_solved_sum) * 1000 if top_solved_sum > 0 else 1000
        ranks.append(this_rank)
    else:
        ranks.append(1000)

    # rating_oj => sum(rating / top_rating for every account)
    rating_oj = ['cf', 'bc']
    accounts = session.query(Account).filter_by(user_id=user_id) \
        .filter(Account.oj_name.in_(rating_oj))
    for account in accounts:
        rating = account.solved
        oj_name = account.oj_name
        top_account = session.query(Account).filter_by(oj_name=oj_name)\
            .order_by(Account.solved.desc(), Account.submitted.desc())\
            .first()
        if not top_account:
            this_rank = 1000
        else:
            top_rating = max(top_account.solved, rating)
            this_rank = (rating / top_rating) * 1000
        ranks.append(this_rank)

    # end_rank = sum(ranks)
    print(ranks)
    user.train_rank = sum(ranks)
    user.save()
    logger.info("[Account] update_train_rank success #{} => sum({}) => {}".format(user, ranks, sum(ranks)))
