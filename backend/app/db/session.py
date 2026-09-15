from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.config import get_settings


@lru_cache
def get_engine():
    # Construction is lazy; the first query opens a connection.
    return create_engine(get_settings().database_url, pool_pre_ping=True,
                         connect_args={"connect_timeout": 3})


def get_db():
    with Session(get_engine()) as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
