# 被测试的 FastAPI 应用（简化版）
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

items_db = {1: {"name": "键盘", "price": 299.0}}


class ItemCreate(BaseModel):
    name: str
    price: float


@app.get("/")
def root():
    return {"message": "Hello Test"}


@app.get("/items/{item_id}")
def get_item(item_id: int):
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="商品不存在")
    return items_db[item_id]


@app.post("/items/", status_code=201)
def create_item(item: ItemCreate):
    new_id = max(items_db.keys()) + 1 if items_db else 1
    items_db[new_id] = item.model_dump()
    return {"id": new_id, **item.model_dump()}
