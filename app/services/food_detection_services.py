from ultralytics import YOLO
from app.config import Config
from app.utils import apply_nms, deduplicate_by_label, image_to_base64
from app.utils import draw_boxes
from app.utils import upload_base64_to_cloudinary


class FoodDetectionService:
    def __init__(self):
        self.model = YOLO(Config.FOOD_DETECTION_PATH)

    def detect_foods(self, image):
        results = self.model.predict(
            image,
            conf=Config.CONFIDENCE,
            imgsz=Config.IMG_SIZE
        )

        detections = []
        for box in results[0].boxes:
            detections.append({
                "class": self.model.names[int(box.cls)],
                "confidence": float(box.conf),
                "bbox": [float(x) for x in box.xyxy[0].tolist()]
            })

        return detections

    def post_process(self, foods):
        foods = apply_nms(foods, iou_threshold=0.5)
        foods = deduplicate_by_label(foods)
        return foods

    def upload_annotated_image(self, image, foods):
        image_with_boxes = draw_boxes(image.copy(), foods)

        base64_img = image_to_base64(image_with_boxes)

        return upload_base64_to_cloudinary(
            base64_img,
            folder="food-detection/annotated"
        )

    def upload_original_image(self, image):
        return upload_base64_to_cloudinary(
            image,
            folder="food-detection/original"
        )
