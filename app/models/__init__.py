from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
from config import settings

# sql-alchemy engine
engine = create_engine(settings.DB_URI, echo=settings.DB_SHOW_SQL)

# global session factory
SessionFactory = sessionmaker(bind=engine)

# base model
BaseModel = declarative_base()

session = scoped_session(SessionFactory)
