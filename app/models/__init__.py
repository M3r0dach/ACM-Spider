from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from settings import DB_URI, DB_SHOW_SQL

# sql-alchemy engine
engine = create_engine(DB_URI, echo=DB_SHOW_SQL)

# global session factory
Session = sessionmaker(bind=engine)

# base model
BaseModel = declarative_base()
