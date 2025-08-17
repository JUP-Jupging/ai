from ultralytics import YOLO
from PIL import Image
import os, torch
from app.core.config import settings

class YOLOService:
    _instance = None

    def __init__(self):
        os.environ.setdefault("OMP_NUM_THREADS", str(settings.OMP_NUM_THREADS))
        torch.set_num_threads(settings.OMP_NUM_THREADS)
        self.model = YOLO(settings.WEIGHTS_PATH)
        # 워밍업
        self.model.predict(
            Image.new("RGB", (settings.IMG_SIZE, settings.IMG_SIZE)),
            imgsz=settings.IMG_SIZE, conf=settings.CONF, iou=settings.IOU,
            device="cpu", verbose=False
        )

    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = YOLOService()
        return cls._instance
    def predict(self, img):
        return self.model.predict(
            img, imgsz=settings.IMG_SIZE, conf=settings.CONF,
            iou=settings.IOU, device="cpu", verbose=False
        )[0]

yolo_service = YOLOService.get()
