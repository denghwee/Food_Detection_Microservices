from .services import BaseService
from ultralytics import YOLO
from ..config import Config

class FoodDetectionService(BaseService):
    def __init__(self):
        super().__init__()
        self.model = YOLO(Config.FOOD_DETECTION_PATH)

    def detect(self, image):
        results = self.model.predict(image, conf=Config.CONFIDENCE, imgsz=Config.IMG_SIZE)
        detections = []
        for box in results[0].boxes:
            detections.append({
                "class": self.model.names[int(box.cls)],
                "confidence": float(box.conf),
                "bbox": [float(x) for x in box.xyxy[0].tolist()]
            })
        return detections