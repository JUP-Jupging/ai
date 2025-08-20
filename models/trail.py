from sqlalchemy import Column, Integer, String, Float
from app.core.db import Base

class Trail(Base):
    __tablename__ = "TRAIL"  # 실제 테이블명에 맞게 수정

    trail_id = Column(Integer, primary_key=True, index=True)  # ESNTL_ID
    trail_type_name = Column(String)      # WLK_COURS_FLAG_NM
    trail_name = Column(String)           # WLK_COURS_NM
    description = Column(String)          # COURS_DC
    description_detail = Column(String)   # COURS_DC
    city_name = Column(String)            # SIGNGU_NM
    difficulty_level = Column(String)     # COURS_LEVEL_NM
    length_detail = Column(Float)        # COURS_DETAIL_LT_CN
    length = Column(String)                # COURS_LT_CN
    option_description = Column(String)   # OPTN_DC
    toilet_description = Column(String)   # TOILET_DC
    amenity_description = Column(String)  # CVNTL_NM
    lot_number_address = Column(String)   # LNM_ADDR
    spot_latitude = Column(Float)         # COURS_SPOT_LA
    spot_longitude = Column(Float)        # COURS_SPOT_LO
    report_count = Column(Integer)        # REPORT_COUNT
    img1 = Column(String)                 # IMG1
    img2 = Column(String)                 # IMG2