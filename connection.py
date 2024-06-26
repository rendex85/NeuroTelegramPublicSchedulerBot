import os

from sqlmodel import SQLModel, Session, create_engine
from dotenv import load_dotenv

load_dotenv()
DB_NAME = TOKEN = os.getenv("DB_NAME")
engine = create_engine(f"sqlite:///{DB_NAME}.db", echo=False)


def init_db():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
