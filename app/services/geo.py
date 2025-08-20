import math

def haversine(coord1, coord2):
    """
    두 좌표(위도, 경도) 사이의 거리(km) 반환
    coord1, coord2: (lat, lng)
    """
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    R = 6371  # 지구 반지름 (km)
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))