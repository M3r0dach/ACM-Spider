from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship, backref
from app.models import BaseModel, session


class SubmitStatus:
    GOOD = 0
    BROKEN = 1


class Submit(BaseModel):
    __tablename__ = 'submits'

    id = Column(Integer, primary_key=True)
    pro_id = Column(String(32))
    run_id = Column(String(32))
    run_time = Column(Integer)
    memory = Column(Integer)
    lang = Column(String(32))
    result = Column(String(32))
    code = Column(Text)
    submitted_at = Column(DateTime)
    status = Column(Integer)
    oj_name = Column(String(32))
    user_id = Column(Integer)
    user_name = Column(String)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)

    def __init__(self):
        self.status = SubmitStatus.BROKEN

    def __repr__(self):
        return u'User:"{0}" \tPID : {1} \tRUNID : {2}'.format(self.user_name, self.pro_id, self.run_id)

    def save(self):
        self.updated_at = datetime.now()
        session.add(self)
        session.commit()


def get_error_submits(account):
    return session.query(Submit.run_id) \
        .filter_by(user_id=account.user_id, oj_name=account.oj_name,
                   status=SubmitStatus.BROKEN) \
        .all()


def create_submit(data):
    cur_account = data['account']
    has = session.query(Submit)\
        .filter_by(run_id=data['run_id'], oj_name=cur_account.oj_name)\
        .first()
    if not has:
        new_submit = Submit()
        new_submit.pro_id = data['pro_id']
        new_submit.run_id = data['run_id']
        new_submit.run_time = data['run_time']
        new_submit.memory = data['memory']
        new_submit.lang = data['lang']
        new_submit.memory = data['memory']
        new_submit.result = data['result']
        new_submit.submitted_at = data['submit_time']
        if data['code']:
            new_submit.code = data['code']
            new_submit.status = SubmitStatus.GOOD
        else:
            new_submit.status = SubmitStatus.BROKEN
        new_submit.oj_name = cur_account.oj_name
        new_submit.user_id = cur_account.user.id
        new_submit.user_name = cur_account.user.display_name
        new_submit.created_at = datetime.now()
        new_submit.save()
        return True


def update_code(data):
    cur_account = data['account']
    has = session.query(Submit) \
        .filter_by(run_id=data['run_id'], oj_name=cur_account.oj_name) \
        .first()
    if not has:
        return False
    has.code = data['code']
    has.status = SubmitStatus.GOOD
    return True
