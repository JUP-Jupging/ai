from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

# 라우터: 표준 경로(/v1/trash/predict) & 별칭 경로(/ai/detect) 모두 지원
from app.routers.trash import router as trash_router, predict as trash_predict
from app.routers.route import router as route_router

app = FastAPI(title="Plogging AI API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 표준 버전 경로
app.include_router(trash_router, prefix="/v1/trash", tags=["trash"])
app.include_router(route_router, prefix="/v1/route", tags=["route"])

# 헬스체크
@app.get("/health")
def health():
    return {"status": "ok"}

# ==== 배포용 별칭 경로 ====
# /ai/detect -> 기존 /v1/trash/predict와 동일 핸들러 재사용
app.add_api_route(
    path="/ai/detect",
    endpoint=trash_predict,
    methods=["POST"],
    tags=["ai"]
)
