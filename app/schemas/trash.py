from pydantic import BaseModel
from typing import List, Dict, Optional

class Box(BaseModel):
    cls: int
    label: str
    conf: float
    x1: float
    y1: float
    x2: float
    y2: float

class Counts(BaseModel):
    fine: Dict[str, int]     # 세부 클래스별 개수 (예: 종이컵, 갈색 유리…)
    grouped: Dict[str, int]  # 분리수거 7종 묶음 (예: 종이/캔/유리/플라스틱/비닐/스티로폼/건전지)

class PredictResponse(BaseModel):
    boxes: List[Box]
    time_ms: float
    counts: Counts
    image_base64: Optional[str] = None  # 박스 그려진 이미지 (data URL 형식)
