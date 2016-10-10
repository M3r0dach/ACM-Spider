from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship, backref
from app.models import BaseModel, session


class SubmitStatus:
    GOOD = 0
    BROKEN = 1


class Submit(BaseModel):
    __tablename__ = 'submit'

    id = Column(Integer, primary_key=True)
    pro_id = Column(String(12))
    run_id = Column(String(20))
    submit_time = Column(DateTime, index=True)
    run_time = Column(Integer)
    memory = Column(Integer)
    lang = Column(String(50))
    result = Column(String(100))
    code = Column(Text)
    update_status = Column(Integer)
    oj_name = Column(String(20), nullable=False)
    user_name = Column(String(25), nullable=True)

    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship('User', backref=backref('submit', lazy='dynamic'))

    def __init__(self):
        self.update_status = SubmitStatus.BROKEN

    def __repr__(self):
        return u'User:"{0}" \tPID : {1} \tRUNID : {2}'.format(self.user_name, self.pro_id, self.run_id)

    def save(self):
        session.add(self)
        session.commit()

    def delete(self):
        session.delete(self)
        session.commit()


def get_error_submits(account):
    return session.query(Submit.run_id) \
        .filter_by(user_id=account.user_id, oj_name=account.oj_name,
                   update_status=SubmitStatus.BROKEN) \
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
        new_submit.submit_time = data['submit_time']
        new_submit.run_time = data['run_time']
        new_submit.memory = data['memory']
        new_submit.lang = data['lang']
        new_submit.memory = data['memory']
        new_submit.result = data['result']
        if data['code']:
            new_submit.code = data['code']
            new_submit.update_status = SubmitStatus.GOOD
        else:
            new_submit.update_status = SubmitStatus.BROKEN
        new_submit.oj_name = cur_account.oj_name
        new_submit.user = cur_account.user
        new_submit.user_name = cur_account.user.name
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
    has.update_status = SubmitStatus.GOOD
    return True
