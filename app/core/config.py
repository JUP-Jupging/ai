from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
class Settings(BaseSettings):
    # .env 읽기 설정 (+ 소문자도 허용, 정의 안 된 키는 무시)
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,  # db_user == DB_USER로 취급
        extra="ignore",        # 정의 안 된 키는 무시(에러 금지)
    )

    # === 기존 YOLO/서버 설정 ===
    WEIGHTS_PATH: str = "models/best.pt"
    IMG_SIZE: int = 640
    CONF: float = 0.25
    IOU: float = 0.45
    OMP_NUM_THREADS: int = 4
    ALLOW_ORIGINS: list[str] = ["*"]

    # === Oracle DB 설정 ===
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int = 1521
    DB_SERVICE: str | None = None   # 예: XEPDB1
    DB_SID: str | None = None       # 예: xe

    ORACLE_CLIENT_LIB_DIR: Optional[str] = None
    LOG_LEVEL: str = "INFO"
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        base = f"oracle+oracledb://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}"
        if self.DB_SERVICE:
            return f"{base}/?service_name={self.DB_SERVICE}"
        if self.DB_SID:
            return f"{base}/{self.DB_SID}"
        raise ValueError("DB_SERVICE 또는 DB_SID 중 하나는 반드시 설정해야 합니다.")

settings = Settings()
