import io
import datetime
from PIL import Image
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from app.config import Config
from app.services_AI.food_detection_services import FoodDetectionService
from app.services.nutrition_service import NutritionService


food_detection_bp = Blueprint(
    "food_detection",
    __name__,
    url_prefix="/api/v2"
)


@food_detection_bp.route("/detect", methods=["GET", "POST"])
@jwt_required()
def detect_food():
    # -------------------------
    # Health check
    # -------------------------
    if request.method == "GET":
        return jsonify({"status": "ready"}), 200

    # -------------------------
    # Get image
    # -------------------------
    file = request.files.get("image")
    if not file:
        return jsonify({"error": "No image uploaded"}), 400

    try:
        image = Image.open(io.BytesIO(file.read())).convert("RGB")
    except Exception:
        return jsonify({"error": "Invalid image file"}), 400

    service = FoodDetectionService()

    # -------------------------
    # Detect food
    # -------------------------
    try:
        foods = service.detect_foods(image)
    except Exception as e:
        return jsonify({"error": str(e)}), 502

    foods = foods or []
    foods = service.post_process(foods)

    threshold = getattr(
        Config,
        "FOOD_CONFIDENCE_THRESHOLD",
        Config.CONFIDENCE
    )

    results = [
        {
            "detected_class": f["class"],
            "confidence": f["confidence"],
            "bbox": f["bbox"]
        }
        for f in foods
        if f["confidence"] >= threshold
    ]

    timestamp = datetime.datetime.now().isoformat()

    # -------------------------
    # No detection
    # -------------------------
    if not results:
        image_url = service.upload_original_image(image)

        return jsonify({
            "status": "success",
            "image_url": image_url,
            "detection": [],
            "nutrition_analysis": {
                "individual_items": [],
                "total_nutrition": {
                    "Calories": 0,
                    "Fat": 0,
                    "Saturates": 0,
                    "Sugar": 0,
                    "Salt": 0
                },
                "items_count": 0
            },
            "metadata": {
                "timestamp": timestamp,
                "total_detections": 0,
                "image_size": {
                    "width": image.width,
                    "height": image.height
                },
                "threshold": threshold
            }
        }), 200

    # -------------------------
    # Upload annotated image
    # -------------------------
    image_url = service.upload_annotated_image(image, foods)

    # -------------------------
    # Nutrition analysis
    # -------------------------
    nutrition_analysis = NutritionService.analyze(results)

    detection_summary = [
        {
            "detected_class": r["detected_class"],
            "disease": None,
            "detection_confidence": r["confidence"]
        }
        for r in results
    ]

    return jsonify({
        "status": "success",
        "image_url": image_url,
        "detection": results,
        "nutrition_analysis": nutrition_analysis,
        "metadata": {
            "timestamp": timestamp,
            "total_detections": len(results),
            "image_size": {
                "width": image.width,
                "height": image.height
            },
            "detection_summary": detection_summary,
            "threshold": threshold
        }
    }), 200
