import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base


# sql-alchemy engine
engine = create_engine(settings.DB_URI, echo=settings.DB_SHOW_SQL)

# global session factory
Session = sessionmaker(bind=engine)

# base model
BaseModel = declarative_base()
