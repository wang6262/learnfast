# 被测试应用（稍复杂的业务逻辑）
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from .database import get_db, Base, engine
from .models import DBUser


app = FastAPI()


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)


@app.post("/users/", status_code=201)
def create_user(username: str, email: str, db: Session = Depends(get_db)):
    # 业务规则：邮箱不能重复
    existing = db.query(DBUser).filter(DBUser.email == email).first()
    if existing:
        raise HTTPException(status_code=409, detail="邮箱已存在")
    user = DBUser(username=username, email=email)
    db.add(user)
    db.commit()
    return {"id": user.id, "username": user.username, "email": user.email}


@app.get("/users/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(DBUser).filter(DBUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return {"id": user.id, "username": user.username, "email": user.email}
