# step18_repository_uow/database.py — 数据库连接和会话配置
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "postgresql+psycopg2://postgres:123456@localhost:5432/learnfast"

engine = create_engine(DATABASE_URL, pool_size=5, max_overflow=10, pool_pre_ping=True, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
