from pydantic import BaseModel
from typing import List, Optional

class RecommendRequest(BaseModel):
    story: str
    lat: Optional[float] = None
    lng: Optional[float] = None

class TrailRecommend(BaseModel):
    trail_id: int
    trail_type_name: Optional[str] = None
    trail_name: Optional[str] = None
    description: Optional[str] = None
    description_detail: Optional[str] = None
    city_name: Optional[str] = None
    difficulty_level: Optional[str] = None
    length: Optional[str] = None           # 구간 정보 (문자형)
    length_detail: Optional[float] = None  # 실제 거리 (숫자형)
    option_description: Optional[str] = None
    toilet_description: Optional[str] = None
    amenity_description: Optional[str] = None
    lot_number_address: Optional[str] = None
    spot_latitude: Optional[float] = None
    spot_longitude: Optional[float] = None
    report_count: Optional[int] = None
    img1: Optional[str] = None
    img2: Optional[str] = None
    score: Optional[float] = None
    reason: Optional[str] = None
class RecommendResponse(BaseModel):
    trails: List[TrailRecommend]