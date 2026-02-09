# db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base

# SQLite (local)
engine = create_engine("sqlite:///data/bot.db")

# PostgreSQL (production)
# engine = create_engine("postgresql://user:password@localhost:5432/churchbot")

SessionLocal = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(engine)
