from fastapi import APIRouter, UploadFile, File, Query
from fastapi.responses import JSONResponse
from PIL import Image, ImageDraw, ImageFont
import io, base64
from app.services.yolo_service import yolo_service
from app.schemas.trash import PredictResponse, Box, Counts

router = APIRouter()

# 0-based 세부 라벨(11종)
FINE_LABELS_0BASED = {
    0:"종이", 1:"종이팩", 2:"종이컵", 3:"캔류", 4:"유리병",
    5:"페트", 6:"플라스틱", 7:"비닐", 8:"유리 + 다중포장재",
    9:"페트 + 다중포장재", 10:"스티로폼", 11:"건전지",
}

# 7종 묶음 매핑
GROUP_MAP_0BASED = {
    **{i:"종이" for i in [0,1,2]},
    3:"캔",
    **{i:"유리" for i in [4,8]},
    **{i:"플라스틱" for i in [5,6,9]},
    7:"비닐",
    10:"스티로폼",
    11:"건전지",
}

# PIL(RGB) 색상
COLOR_BY_GROUP = {
    "종이": (60,180,255),
    "캔": (80,200,120),
    "유리": (120,160,240),
    "플라스틱": (160,160,80),
    "비닐": (200,120,120),
    "스티로폼": (150,150,220),
    "건전지": (100,100,255),
    "기타": (180,180,180),
}

def _load_korean_font(size: int = 20):
    """한글 폰트 자동 탐색 (환경에 없으면 기본폰트)"""
    candidates = [
        "C:/Windows/Fonts/malgun.ttf",  # Windows
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",  # macOS
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",  # Linux
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size=size)
        except Exception:
            continue
    return ImageFont.load_default()

def draw_grouped_boxes_pil(orig_rgb: Image.Image, det_xyxy, det_cls) -> str | None:
    """이미지에 '묶음 7종 한글 라벨'만 표시(점수 X) → JPEG base64 반환"""
    img = orig_rgb.copy()
    draw = ImageDraw.Draw(img)
    font = _load_korean_font()

    for (x1, y1, x2, y2), k in zip(det_xyxy, det_cls):
        k = int(k)
        group = GROUP_MAP_0BASED.get(k, "기타")
        color = COLOR_BY_GROUP.get(group, (180,180,180))

        # 박스
        draw.rectangle([(x1, y1), (x2, y2)], outline=color, width=3)

        # 라벨 (배경박스 + 텍스트)
        label = group
        left, top, right, bottom = draw.textbbox((0, 0), label, font=font)
        tw, th = right - left, bottom - top
        pad = 4
        draw.rectangle([(x1, y1 - th - pad*2), (x1 + tw + pad*2, y1)], fill=color)
        draw.text((x1 + pad, y1 - th - pad), label, fill=(255,255,255), font=font)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/jpeg;base64,{b64}"

@router.post("/predict", response_model=PredictResponse)
async def predict(
    file: UploadFile = File(...),
    return_image: bool = Query(True),
    grouped_only_boxes: bool = Query(True)
):
    # 업로드 파일 → PIL RGB
    pil_img = Image.open(io.BytesIO(await file.read())).convert("RGB")

    # 추론 (서버 설정값 그대로 사용)
    res = yolo_service.predict(pil_img)

    xyxy = res.boxes.xyxy.tolist() if res.boxes is not None else []
    cls  = [int(c) for c in (res.boxes.cls.tolist() if res.boxes is not None else [])]

    # 집계 (세부 & 묶음)
    fine_counts, grouped_counts = {}, {}
    for k in cls:
        fine = FINE_LABELS_0BASED.get(k, f"UNK_{k}")
        group = GROUP_MAP_0BASED.get(k, "기타")
        fine_counts[fine] = fine_counts.get(fine, 0) + 1
        grouped_counts[group] = grouped_counts.get(group, 0) + 1

    # 박스 목록 (묶음 라벨만; 점수는 0.0 고정)
    boxes = []
    for (x1, y1, x2, y2), k in zip(xyxy, cls):
        label = GROUP_MAP_0BASED.get(k, "기타") if grouped_only_boxes \
                else FINE_LABELS_0BASED.get(k, f"UNK_{k}")
        boxes.append(Box(cls=k, label=label, conf=0.0,
                         x1=float(x1), y1=float(y1), x2=float(x2), y2=float(y2)))

    # 이미지(base64)
    img_b64 = draw_grouped_boxes_pil(pil_img, xyxy, cls) if return_image else None

    payload = PredictResponse(
        boxes=boxes,
        time_ms=float(res.speed.get("inference", 0.0)),
        counts=Counts(fine=fine_counts, grouped=grouped_counts),
        image_base64=img_b64
    )
    return JSONResponse(payload.model_dump())

# main.py에서 별칭(/ai/detect)로 재사용하기 위한 참조
# (app.add_api_route(..., endpoint=trash_predict, ...))
predict.__name__ = "trash_predict"
