# app/core/db.py
import os
import oracledb
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.config import settings

# 1) Thick 모드 초기화 (엔진/세션 만들기 전에 반드시!)
IC_DIR = os.getenv("ORACLE_CLIENT_LIB_DIR", "").strip()
if not IC_DIR:
    # settings에서 받아오기 (환경변수 대신 .env로 관리하는 경우)
    IC_DIR = getattr(settings, "ORACLE_CLIENT_LIB_DIR", "") or ""

if not IC_DIR:
    # IC 경로가 없다면 여기서 명확히 실패시켜 원인 파악 용이
    raise RuntimeError(
        "ORACLE_CLIENT_LIB_DIR가 비어있습니다. .env 또는 환경변수에 Instant Client 경로를 설정하세요."
    )

# 폴더가 실제 존재/접근 가능한지 체크
if not os.path.isdir(IC_DIR):
    raise RuntimeError(f"Instant Client 폴더가 존재하지 않습니다: {IC_DIR}")

try:
    # init 호출
    oracledb.init_oracle_client(lib_dir=IC_DIR)
    print("[ORACLE] is_thin_mode:", oracledb.is_thin_mode())  # False가 되어야 합니다.
    print("[ORACLE] clientversion:", oracledb.clientversion())
except Exception as e:
    print("[ORACLE] Instant Client 초기화 실패:", e)
    raise
print("[ORACLE] is_thin_mode:", oracledb.is_thin_mode())
try:
    print("[ORACLE] clientversion:", oracledb.clientversion())
except Exception as e:
    print("[ORACLE] clientversion() error:", e)

class Base(DeclarativeBase):
    pass

engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    pool_recycle=1800,
    echo=False,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def db_ping_info() -> dict:
    with engine.connect() as conn:
        one = conn.exec_driver_sql("SELECT 1 FROM dual").scalar_one()
        db_name = conn.exec_driver_sql(
            "SELECT sys_context('USERENV','DB_NAME') FROM dual"
        ).scalar_one()
        user = conn.exec_driver_sql(
            "SELECT sys_context('USERENV','SESSION_USER') FROM dual"
        ).scalar_one()
        systs = conn.exec_driver_sql(
            "SELECT TO_CHAR(SYSDATE, 'YYYY-MM-DD HH24:MI:SS') FROM dual"
        ).scalar_one()
        return {"ok": (one == 1), "db_name": db_name, "session_user": user, "sysdate": systs}
