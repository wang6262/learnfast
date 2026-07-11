# 被测试的异步 FastAPI 应用

from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, Session, declarative_base

# 使用 SQLite 做测试数据库（零配置，内存模式）
# 生产代码用 PostgreSQL，测试用 SQLite 是常见模式
engine = create_engine("sqlite:///./test.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class DBUser(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100))


Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app = FastAPI()


@app.get("/users/")
def list_users(db: Session = Depends(get_db)):
    users = db.query(DBUser).all()
    return [{"id": u.id, "username": u.username, "email": u.email} for u in users]


@app.post("/users/", status_code=201)
def create_user(username: str, email: str, db: Session = Depends(get_db)):
    user = DBUser(username=username, email=email)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "username": user.username, "email": user.email}
