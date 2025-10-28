from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

# FastAPI 앱 생성
app = FastAPI(
    title="NOVAS EZ API",
    description="NOVAS EZ 프로젝트 FastAPI 예제",
    version="1.0.0"
)


# 루트 엔드포인트
@app.get("/")
async def root():
    return {"message": "NOVAS EZ FastAPI 서버에 오신 걸 환영합니다!"}

# 헬스 체크
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "NOVAS EZ API"}

# 모든 아이템 조회
@app.get("/items", response_model=List[Item])
async def get_items():
    return items_db

# 특정 아이템 조회
@app.get("/items/{item_id}", response_model=Item)
async def get_item(item_id: int):
    item = next((item for item in items_db if item.id == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="아이템을 찾을 수 없습니다")
    return item

# 아이템 생성
@app.post("/items", response_model=Item)
async def create_item(item: ItemCreate):
    global next_id
    new_item = Item(
        id=next_id,
        name=item.name,
        description=item.description,
        price=item.price
    )
    items_db.append(new_item)
    next_id += 1
    return new_item

# 아이템 수정
@app.put("/items/{item_id}", response_model=Item)
async def update_item(item_id: int, item_update: ItemCreate):
    item_index = next((i for i, item in enumerate(items_db) if item.id == item_id), None)
    if item_index is None:
        raise HTTPException(status_code=404, detail="아이템을 찾을 수 없습니다")
    
    updated_item = Item(
        id=item_id,
        name=item_update.name,
        description=item_update.description,
        price=item_update.price
    )
    items_db[item_index] = updated_item
    return updated_item

# 아이템 삭제
@app.delete("/items/{item_id}")
async def delete_item(item_id: int):
    item_index = next((i for i, item in enumerate(items_db) if item.id == item_id), None)
    if item_index is None:
        raise HTTPException(status_code=404, detail="아이템을 찾을 수 없습니다")
    
    deleted_item = items_db.pop(item_index)
    return {"message": f"아이템 '{deleted_item.name}'이 삭제되었습니다"}

# 검색 기능
@app.get("/items/search/", response_model=List[Item])
async def search_items(q: str):
    results = [item for item in items_db if q.lower() in item.name.lower()]
    return results

# 서버 실행 함수
if __name__ == "__main__":
    uvicorn.run(
        "fastapi_example:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )