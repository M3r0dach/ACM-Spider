from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship, backref
from app.models import BaseModel, SessionFactory

session = SessionFactory()


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
        pass

    def __repr__(self):
        return u'User:"{0}" \tPID : {1} \tRUNID : {2}'.format(self.user_name, self.pro_id, self.run_id)

    def save(self):
        session.add(self)
        session.commit()

    def delete(self):
        session.delete(self)
        session.commit()


def create_submit(new_submit):
    # TODO
    pass
