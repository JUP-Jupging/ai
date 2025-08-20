import re
from math import log1p
from kiwipiepy import Kiwi
from rank_bm25 import BM25Okapi
from app.services.geo import haversine

kiwi = Kiwi()

# -----------------------------
# 동의어/키워드 사전 (필드에 맞춰 간결화)
# -----------------------------
SHORT_SYNONYMS = ["짧", "짧게", "가볍게", "가까운", "근처", "소규모", "단거리", "2km", "3km"]
MEDIUM_SYNONYMS = ["중거리", "보통 거리", "4km", "5km", "6km", "7km", "8km"]
LONG_SYNONYMS = ["길게", "장거리", "멀리", "도전", "챌린지", "10km", "12km", "15km"]

EASY_SYNONYMS = ["쉬움", "편안", "힐링", "가족", "초보", "완만", "평지"]
MEDIUM_DIFF_SYNONYMS = ["보통", "무난", "적당"]
HARD_SYNONYMS = ["어려움", "운동", "고난도", "등산", "트레킹", "급경사", "챌린지"]

TRASH_SYNONYMS = ["쓰레기", "줍깅", "플로깅", "봉사", "환경", "무단투기", "핫스팟"]

TOILET_SYNONYMS = ["화장실", "편의시설", "화장실 있음", "화장실 위치"]
STORE_SYNONYMS = ["매점", "식수", "편의점", "음료", "간식", "정수기", "음수대"]

REGION_SYNONYMS = ["서울", "경기", "인천", "부산", "강원", "전남", "전북", "경북", "경남", "충북", "충남", "대전", "대구", "광주", "울산", "제주", "세종"]

SCENERY_KEYWORDS = [
    "벚꽃","단풍","억새","갈대","코스모스","유채꽃",
    "바다","해안","바닷가","산","강","천","강변","천변","숲","숲길","계곡","호수","저수지",
    "전망","전망대","야경","노을","일몰","일출"
]

# 숫자/단위 파싱
KM_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(?:km|킬로|키로)")
HOUR_RE = re.compile(r"(\d+(?:\.\d+)?)\s*시간")
MIN_RE = re.compile(r"(\d+)\s*분")
RANGE_RE = re.compile(r"(\d+(?:\.\d+)?)\s*[-~]\s*(\d+(?:\.\d+)?)\s*(km|킬로|키로|시간|분)?")

def walking_kmh() -> float:
    return 4.5  # 보행 속도 가정

def duration_to_km(hours=0.0, minutes=0.0) -> float:
    return (hours + minutes/60.0) * walking_kmh()

# -----------------------------
# 형태소/키워드 추출
# -----------------------------
def extract_keywords(text: str) -> list:
    if not text:
        return []
    tokens = kiwi.tokenize(text)
    return [t.form for t in tokens if t.tag in ("NNG", "NNP", "VV", "VA")]

def parse_length_intent(text: str):
    """사용자 입력에서 길이/시간 의도를 km 범위로 변환."""
    if not text:
        return None
    m = RANGE_RE.search(text)
    if m:
        a, b, unit = m.groups()
        a, b = float(a), float(b)
        if unit in (None, "km", "킬로", "키로"):
            return (min(a, b), max(a, b))
        if unit == "시간":
            return (duration_to_km(hours=min(a,b)), duration_to_km(hours=max(a,b)))
        if unit == "분":
            return (duration_to_km(minutes=min(a,b)), duration_to_km(minutes=max(a,b)))

    m = KM_RE.search(text)
    if m:
        v = float(m.group(1))
        return (max(0.5, v - 0.5), v + 0.5)

    m = HOUR_RE.search(text)
    if m:
        v = float(m.group(1))
        km = duration_to_km(hours=v)
        return (km * 0.8, km * 1.2)

    m = MIN_RE.search(text)
    if m:
        v = float(m.group(1))
        km = duration_to_km(minutes=v)
        return (km * 0.8, km * 1.2)

    # 키워드 기반 근사
    if any(w in text for w in SHORT_SYNONYMS):
        return (0.5, 3.0)
    if any(w in text for w in LONG_SYNONYMS):
        return (10.0, 100.0)
    if any(w in text for w in MEDIUM_SYNONYMS):
        return (4.0, 8.0)
    return None

# -----------------------------
# 사용자 의도 파싱 (필드에 맞게 단순/명확)
# -----------------------------
def extract_user_prefs(text: str) -> dict:
    text = (text or "").strip()
    prefs = {}

    # 길이(범위) + 과거 호환(short/long)
    rng = parse_length_intent(text)
    if rng:
        prefs["length_range_km"] = rng
    if any(word in text for word in SHORT_SYNONYMS):
        prefs["length"] = "short"
    elif any(word in text for word in LONG_SYNONYMS):
        prefs["length"] = "long"

    # 난이도
    if any(w in text for w in EASY_SYNONYMS): prefs["difficulty"] = "쉬움"
    elif any(w in text for w in HARD_SYNONYMS): prefs["difficulty"] = "어려움"
    elif any(w in text for w in MEDIUM_DIFF_SYNONYMS): prefs["difficulty"] = "보통"

    # 플로깅/편의
    if any(w in text for w in TRASH_SYNONYMS): prefs["trash"] = True
    if any(w in text for w in TOILET_SYNONYMS): prefs["toilet"] = True
    if any(w in text for w in STORE_SYNONYMS): prefs["store"] = True

    # 지역
    for region in REGION_SYNONYMS:
        if region in text:
            prefs["region"] = region
            break

    # 경치/테마 키워드
    prefs["keywords"] = [kw for kw in SCENERY_KEYWORDS if kw in text]

    # 질의 확장을 위해 원문에서 쓰인 동의어도 저장
    prefs["synonyms_in_text"] = [
        *[w for w in SHORT_SYNONYMS if w in text],
        *[w for w in MEDIUM_SYNONYMS if w in text],
        *[w for w in LONG_SYNONYMS if w in text],
        *[w for w in EASY_SYNONYMS if w in text],
        *[w for w in MEDIUM_DIFF_SYNONYMS if w in text],
        *[w for w in HARD_SYNONYMS if w in text],
        *[w for w in TRASH_SYNONYMS if w in text],
        *[w for w in TOILET_SYNONYMS if w in text],
        *[w for w in STORE_SYNONYMS if w in text],
    ]
    return prefs

# -----------------------------
# BM25 인덱스/질의 확장 (사용 가능한 필드만)
# -----------------------------
def trail_to_text(t) -> str:
    parts = [
        str(getattr(t, "trail_name", "") or ""),
        str(getattr(t, "description", "") or ""),
        str(getattr(t, "description_detail", "") or ""),
        str(getattr(t, "city_name", "") or ""),
        str(getattr(t, "amenity_description", "") or ""),
        str(getattr(t, "toilet_description", "") or ""),
        str(getattr(t, "length", "") or ""),
    ]
    return " ".join(p for p in parts if p)

def build_bm25_corpus(trails: list):
    # 필드 가중치: 이름/도시/설명을 약하게 복제해서 가중치 부여
    docs = []
    for t in trails:
        name = (getattr(t, "trail_name", "") or "")
        city = (getattr(t, "city_name", "") or "")
        text = trail_to_text(t)
        weighted = f"{name} {name} {text} {city}"
        docs.append(weighted)
    tokenized_docs = [extract_keywords(doc) for doc in docs]
    bm25 = BM25Okapi(tokenized_docs)
    return bm25, trails

def expand_query_tokens(user_text: str, prefs: dict) -> list:
    q = extract_keywords(user_text)
    q.extend(prefs.get("keywords", []))
    q.extend(prefs.get("synonyms_in_text", []))
    if prefs.get("region"):
        q.append(prefs["region"])
    return list(dict.fromkeys(q))  # dedupe

def get_top_k_routes(user_text: str, trails: list, k: int = 10) -> list:
    bm25, trails = build_bm25_corpus(trails)
    prefs = extract_user_prefs(user_text)
    query = expand_query_tokens(user_text, prefs)
    scores = bm25.get_scores(query) if query else [0.0] * len(trails)
    top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
    return [trails[i] for i in top_indices]

# -----------------------------
# 스코어링 (가용 컬럼만 활용)
# -----------------------------
def _parse_length_from_text(length_str: str):
    if not length_str:
        return None
    m = KM_RE.search(length_str)
    if m:
        try:
            return float(m.group(1))
        except:
            return None
    return None

def _get_route_km(route):
    km = getattr(route, "length_detail", None)
    if km is not None:
        return km
    return _parse_length_from_text(getattr(route, "length", None))

def length_match_score(route_km: float, desired_range):
    if not route_km or not desired_range:
        return 0.0
    lo, hi = desired_range
    if lo <= route_km <= hi:
        return 1.0
    d = min(abs(route_km - lo), abs(route_km - hi))
    return max(0.0, 1.0 - d / 5.0)  # 5km 벗어나면 0

def difficulty_match_score(route_diff: str, desired: str):
    if not desired or not route_diff:
        return 0.0
    if desired in route_diff:
        return 1.0
    if desired == "보통" and any(x in route_diff for x in ["쉬움", "어려움"]):
        return 0.5
    return 0.0

def density_per_km(count, length_km):
    if not count or not length_km or length_km <= 0:
        return 0.0
    return count / max(0.5, length_km)

WEIGHTS = {
    "length": 3.0,
    "difficulty": 2.5,
    "trash": 2.0,
    "distance": 3.0,
    "toilet": 1.0,
    "store": 1.0,
    "region": 1.2,
    "keywords": 1.6,
}

def score_route(route, user_prefs, user_location=None):
    score = 0.0

    # 길이 (연속 스코어)
    route_km = _get_route_km(route)
    rng = user_prefs.get("length_range_km")
    if rng and route_km:
        score += WEIGHTS["length"] * length_match_score(route_km, rng)
    else:
        if user_prefs.get("length") == "short" and route_km and route_km < 3:
            score += 2.0
        elif user_prefs.get("length") == "long" and route_km and route_km > 10:
            score += 2.0

    # 난이도
    score += WEIGHTS["difficulty"] * difficulty_match_score(
        getattr(route, "difficulty_level", None),
        user_prefs.get("difficulty")
    )

    # 플로깅: 제보 밀도(로그 완만 증가)
    if user_prefs.get("trash"):
        rpt = getattr(route, "report_count", 0) or 0
        dens = density_per_km(rpt, route_km or 1.0)
        score += WEIGHTS["trash"] * min(1.5, log1p(dens + 1))

    # 거리(가까울수록 ↑)
    if user_location and getattr(route, "spot_latitude", None) and getattr(route, "spot_longitude", None):
        dist_km = haversine(user_location, (route.spot_latitude, route.spot_longitude))
        score += WEIGHTS["distance"] * max(0.0, 1.0 - (dist_km / 10.0))  # 0km→1, 10km→0

    # 편의 시설
    toilet_desc = (getattr(route, "toilet_description", "") or "")
    amen_desc = (getattr(route, "amenity_description", "") or "")
    if user_prefs.get("toilet") and toilet_desc and "없음" not in toilet_desc:
        score += WEIGHTS["toilet"]
    if user_prefs.get("store") and amen_desc and "없음" not in amen_desc:
        score += WEIGHTS["store"]

    # 지역
    if user_prefs.get("region") and (getattr(route, "city_name", "") or "").find(user_prefs["region"]) >= 0:
        score += WEIGHTS["region"]

    # 키워드(경치/테마)
    if user_prefs.get("keywords"):
        blob = f"{getattr(route,'description','') or ''} {getattr(route,'description_detail','') or ''}"
        hit = 0
        for kw in user_prefs["keywords"]:
            if kw in blob:
                hit += 1
        if hit:
            score += WEIGHTS["keywords"] * min(1.0, hit / 3.0)  # cap 3+

    return score

def rerank_routes(routes, user_prefs, user_location=None):
    scored = [(score_route(route, user_prefs, user_location), route) for route in routes]
    scored.sort(reverse=True, key=lambda x: x[0])
    return [route for _, route in scored]

# -----------------------------
# 점수 + 내러티브 reason 생성
# -----------------------------
def score_route_with_breakdown(route, user_prefs, user_location=None):
    """총점과 이유 생성을 위한 부가정보를 함께 계산."""
    breakdown = {}
    total = 0.0

    # 길이
    route_km = _get_route_km(route)
    rng = user_prefs.get("length_range_km")
    part = 0.0
    if rng and route_km:
        part = WEIGHTS["length"] * length_match_score(route_km, rng)
    else:
        if user_prefs.get("length") == "short" and route_km and route_km < 3:
            part = 2.0
        elif user_prefs.get("length") == "long" and route_km and route_km > 10:
            part = 2.0
    if part:
        breakdown["length"] = round(part, 3); total += part
    breakdown["_route_km"] = route_km

    # 난이도
    part = WEIGHTS["difficulty"] * difficulty_match_score(
        getattr(route, "difficulty_level", None),
        user_prefs.get("difficulty")
    )
    if part:
        breakdown["difficulty"] = round(part, 3); total += part

    # 플로깅 밀도
    if user_prefs.get("trash"):
        rpt = getattr(route, "report_count", 0) or 0
        dens = density_per_km(rpt, route_km or 1.0)
        tpart = WEIGHTS["trash"] * min(1.5, log1p(dens + 1))
        if tpart:
            breakdown["trash_density"] = round(tpart, 3); total += tpart
            breakdown["_report_count"] = rpt
            breakdown["_report_density"] = round(dens, 3)

    # 근접성
    if user_location and getattr(route, "spot_latitude", None) and getattr(route, "spot_longitude", None):
        dist_km = haversine(user_location, (route.spot_latitude, route.spot_longitude))
        ppart = WEIGHTS["distance"] * max(0.0, 1.0 - (dist_km / 10.0))
        if ppart:
            breakdown["proximity"] = round(ppart, 3); total += ppart
            breakdown["_distance_km"] = round(dist_km, 2)

    # 편의시설
    toilet_desc = (getattr(route, "toilet_description", "") or "")
    amen_desc = (getattr(route, "amenity_description", "") or "")
    if user_prefs.get("toilet") and toilet_desc and "없음" not in toilet_desc:
        breakdown["toilet"] = round(WEIGHTS["toilet"], 3); total += WEIGHTS["toilet"]
    if user_prefs.get("store") and amen_desc and "없음" not in amen_desc:
        breakdown["store"] = round(WEIGHTS["store"], 3); total += WEIGHTS["store"]

    # 지역
    if user_prefs.get("region") and (getattr(route, "city_name", "") or "").find(user_prefs["region"]) >= 0:
        breakdown["region"] = round(WEIGHTS["region"], 3); total += WEIGHTS["region"]

    # 테마 키워드
    kw_hits = 0
    if user_prefs.get("keywords"):
        blob = f"{getattr(route,'description','') or ''} {getattr(route,'description','') or ''} {getattr(route,'description_detail','') or ''}"
        for kw in user_prefs["keywords"]:
            if kw in blob:
                kw_hits += 1
        if kw_hits:
            kpart = WEIGHTS["keywords"] * min(1.0, kw_hits / 3.0)
            breakdown["keywords"] = round(kpart, 3); total += kpart
            breakdown["_keyword_hits"] = kw_hits

    return total, breakdown

def _matched_keywords(route, prefs):
    blob = f"{getattr(route,'description','') or ''} {getattr(route,'description_detail','') or ''}"
    return [kw for kw in prefs.get('keywords', []) if kw in blob]

def _describe_distance_km(d):
    if d is None:
        return None
    if d < 1:  return "아주 가까워 바로 접근 가능합니다"
    if d < 3:  return "가까운 편이라 접근성이 좋습니다"
    if d < 7:  return "대중교통·차량으로 접근하기 무난합니다"
    return "다소 거리가 있지만 목적지형 코스입니다"

def _describe_density(dens, cnt):
    if cnt == 0:            return "플로깅 제보는 아직 없습니다"
    if dens is None:        return None
    if dens < 0.5:          return f"플로깅 제보 {cnt}건으로 비교적 적은 편입니다"
    if dens < 1.5:          return f"플로깅 제보 {cnt}건으로 보통 수준입니다"
    return f"플로깅 제보 {cnt}건으로 활동 포인트가 많은 편입니다"

def format_reason_narrative(route, prefs, breakdown, score, rank=None, top_score=None, total_candidates=None):
    """
    줄글로 reason 생성. 만점 없이 상대 점수/순위를 함께 표현.
    """
    km = breakdown.get("_route_km")
    dist = breakdown.get("_distance_km")
    cnt = breakdown.get("_report_count", 0)
    dens = breakdown.get("_report_density")
    kws = _matched_keywords(route, prefs)
    parts = []

    # 헤더: 점수/상대 지표
    header = f"사연 유사도 점수는 {score:.2f}점입니다"
    if top_score and top_score > 0:
        rel = min(100.0, max(0.0, score / top_score * 100.0))
        if rank is not None and total_candidates:
            header += f" (후보 {total_candidates}개 중 {rank}위, 상위 후보 대비 {rel:.0f}% 수준)"
        else:
            header += f" (상위 후보 대비 약 {rel:.0f}% 수준)"
    header += "."
    parts.append(header)

    # 본문: 거리/난이도/접근성/편의/플로깅/키워드/지역
    detail_bits = []

    if km:
        detail_bits.append(f"코스 길이는 약 {km:.1f}km로 요청하신 거리대와 잘 맞고")
    if breakdown.get("difficulty") and getattr(route, "difficulty_level", None):
        detail_bits.append(f"난이도는 {route.difficulty_level}라 가족·초보도 편하게 걷기 좋아요")
    if "proximity" in breakdown and dist is not None:
        phr = _describe_distance_km(dist)
        if phr: detail_bits.append(f"현 위치에서 약 {dist:.1f}km, {phr}")
    if "toilet" in breakdown:
        detail_bits.append("화장실 이용이 가능하며")
    if "store" in breakdown:
        detail_bits.append("근처에 편의점·식수 접근도 가능합니다")
    if prefs.get("trash"):
        dens_text = _describe_density(dens, cnt)
        if dens_text: detail_bits.append(dens_text)
    if prefs.get("region") and prefs["region"] in (getattr(route,"city_name","") or ""):
        detail_bits.append(f"{prefs['region']} 권역 조건에도 부합합니다")
    if breakdown.get("_keyword_hits"):
        if kws:
            detail_bits.append(f"또한 {', '.join(kws)} 키워드가 코스 설명에 확인됩니다")
        else:
            detail_bits.append("또한 요청하신 테마 키워드가 코스 설명에 확인됩니다")

    if detail_bits:
        text = " ".join(detail_bits)
        if not text.endswith(("요", "다", "습니다", ".")):
            text += "."
        parts.append(text)

    return " ".join(parts)

# -----------------------------
# 추천 결과: 총점 + 내러티브 reason (최대 3개)
# -----------------------------
def recommend_routes_brief(user_text: str, trails: list, user_location=None, k: int = 3):
    """
    반환:
    [
      {"trail_id": 1, "trail_name": "○○코스", "score": 7.42, "reason": "사연 유사도 점수는 ..."},
      ...
    ] (항상 최대 3개)
    """
    k = min(k, 3)

    # 1) BM25 넉넉히 뽑기
    initial_k = max(50, k * 3)
    bm25, _ = build_bm25_corpus(trails)
    prefs = extract_user_prefs(user_text)
    query = expand_query_tokens(user_text, prefs)
    scores = bm25.get_scores(query) if query else [0.0] * len(trails)
    top_idx = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:initial_k]
    selected = [trails[i] for i in top_idx]

    # 2) 재정렬 + 내러티브 생성
    rows = []
    for r in selected:
        total, bd = score_route_with_breakdown(r, prefs, user_location)
        rows.append((total, r, bd))
    rows.sort(key=lambda x: x[0], reverse=True)

    out = []
    top_score = rows[0][0] if rows else None
    total_candidates = len(rows)
    for idx, (total, r, bd) in enumerate(rows[:k], start=1):
        reason_text = format_reason_narrative(
            route=r, prefs=prefs, breakdown=bd, score=total,
            rank=idx, top_score=top_score, total_candidates=total_candidates
        )
        out.append({
            "trail_id": getattr(r, "trail_id", None),
            "trail_name": getattr(r, "trail_name", None),
            "score": round(total, 2),
            "reason": reason_text,
        })
    return out

# 기존 리스트만 필요할 때 (최대 3개)
def recommend_routes(user_text: str, trails: list, user_location=None, k: int = 3) -> list:
    k = min(k, 3)
    user_prefs = extract_user_prefs(user_text)
    initial_k = max(50, k * 3)
    top_k = get_top_k_routes(user_text, trails, initial_k)
    reranked = rerank_routes(top_k, user_prefs, user_location)
    return reranked[:k]
