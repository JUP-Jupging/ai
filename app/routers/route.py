from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.db import get_db
from app.core.db import db_ping_info
from app.core.config import settings
from app.schemas.route import RecommendRequest, RecommendResponse, TrailRecommend
from app.repositories.trail_repo import get_all_trails
from app.services.recommend import recommend_routes
from app.services.recommend import recommend_routes_brief

router = APIRouter()

def _mask(uri: str) -> str:
    # oracle+oracledb://user:pass@host:port/...
    try:
        head, tail = uri.split("://", 1)
        creds_host = tail.split("@", 1)
        if len(creds_host) == 2:
            creds, rest = creds_host
            if ":" in creds:
                user = creds.split(":")[0]
                return f"{head}://{user}:***@{rest}"
        return uri
    except Exception:
        return uri

# ✅ 여기 추가
@router.get("/db-ping")
def db_ping():
    try:
        info = db_ping_info()
        return {"status": "ok", "info": info}
    except Exception as e:
        # 에러도 같이 보여주면 디버깅 편함
        raise HTTPException(status_code=500, detail=f"DB ping failed: {e}")

@router.get("/db-debug")
def db_debug(db: Session = Depends(get_db)):
    info = {
        "uri": _mask(settings.SQLALCHEMY_DATABASE_URI),
        "db_service": settings.DB_SERVICE,
        "db_sid": settings.DB_SID,
    }
    try:
        val = db.execute(text("SELECT 1 FROM DUAL")).scalar()
        info.update({"ok": True, "value": int(val)})
    except Exception as e:
        info.update({"ok": False, "error_type": e.__class__.__name__, "error": str(e)})
    return info

@router.post("/recommend", response_model=RecommendResponse)
def recommend_api(
    req: RecommendRequest,
    db: Session = Depends(get_db)
):
    try:
        trails = get_all_trails(db)
        user_location = (req.lat, req.lng) if (req.lat is not None and req.lng is not None) else None
        # ✅ 상위 3개에 대해 score/reason 계산
        rows = recommend_routes_brief(
            user_text=req.story,
            trails=trails,
            user_location=user_location,
            k=3
        )
        # rows: [{ "trail_id", "trail_name", "score", "reason" }, ...]

        # 원본 trail 매핑
        by_id = {t.trail_id: t for t in trails}

        # ✅ 점수/이유를 붙여서 반환 (항상 최대 3개)
        result = []
        for r in rows:
            base = by_id.get(r["trail_id"])
            if base is None:
                continue
            result.append(
                TrailRecommend(
                    trail_id=base.trail_id,
                    trail_type_name=base.trail_type_name,
                    trail_name=base.trail_name,
                    description=base.description,
                    description_detail=base.description_detail,
                    city_name=base.city_name,
                    difficulty_level=base.difficulty_level,
                    length=base.length,
                    length_detail=base.length_detail,
                    option_description=base.option_description,
                    toilet_description=base.toilet_description,
                    amenity_description=base.amenity_description,
                    lot_number_address=base.lot_number_address,
                    spot_latitude=base.spot_latitude,
                    spot_longitude=base.spot_longitude,
                    report_count=base.report_count,
                    img1=base.img1,
                    img2=base.img2,
                    # ⬇️ 추가 필드
                    score=round(r["score"], 2),
                    reason=r["reason"],
                )
            )

        return RecommendResponse(trails=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"추천 실패: {e}")