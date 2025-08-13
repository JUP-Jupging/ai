from fastapi import APIRouter

router = APIRouter()

@router.get("/ping")
def ping():
    return {"route": "ok"}  # 여기만 두고, 나중에 알고리즘 붙이면 됨
