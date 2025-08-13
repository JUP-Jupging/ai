from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    WEIGHTS_PATH: str = "models/best.pt"
    IMG_SIZE: int = 640
    CONF: float = 0.25
    IOU: float = 0.45
    OMP_NUM_THREADS: int = 4
    ALLOW_ORIGINS: list[str] = ["*"]

    class Config:
        env_file = ".env"

settings = Settings()
