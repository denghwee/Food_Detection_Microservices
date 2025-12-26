from flask import request, jsonify, render_template
import uuid
import time
import datetime
import io
import numpy as np
from PIL import Image
from flask_jwt_extended import jwt_required

from ..config import Config
from ..services import FoodDetectionService
from ..utils import apply_nms, deduplicate_by_label, draw_boxes, image_to_base64, calculate_total_nutrition
from ..utils.cloudinary_helper import upload_image_to_cloudinary

def register_routes(app):

    @app.route('/')
    def home():
        return render_template('index.html')

    @app.route('/api/v2/detect', methods=['GET', 'POST'])
    @jwt_required()
    def detect():
        """
        Food detection + nutrition analysis
        Upload annotated image to Cloudinary and return image URL
        """

        # -------------------------
        # Health check
        # -------------------------
        if request.method == 'GET':
            return jsonify({'status': 'ready'}), 200

        # -------------------------
        # Get image
        # -------------------------
        file = request.files.get('image')
        if not file:
            return jsonify({'error': 'No image uploaded.'}), 400

        try:
            image = Image.open(io.BytesIO(file.read())).convert('RGB')
        except Exception:
            return jsonify({'error': 'Invalid image file.'}), 400

        # -------------------------
        # Detect food
        # -------------------------
        try:
            service = FoodDetectionService()
            foods = service.detect(image)
        except Exception as error:
            return jsonify({'error': str(error)}), 502

        foods = foods or []

        # -------------------------
        # Post-processing
        # -------------------------
        foods = apply_nms(foods, iou_threshold=0.5)
        foods = deduplicate_by_label(foods)

        threshold = getattr(Config, 'FOOD_CONFIDENCE_THRESHOLD', Config.CONFIDENCE)

        results = [
            {
                'detected_class': f.get('class', 'unknown'),
                'confidence': float(f.get('confidence', 0)),
                'bbox': f.get('bbox', []),
            }
            for f in foods
            if float(f.get('confidence', 0)) >= threshold
        ]

        timestamp = datetime.datetime.now().isoformat()

        # -------------------------
        # No detection case
        # -------------------------
        if not results:
            image_url = upload_image_to_cloudinary(
                image,
                folder="food-detection/original"
            )

            return jsonify({
                'status': 'success',
                'image_url': image_url,
                'detection': [],
                'nutrition_analysis': {
                    'individual_items': [],
                    'total_nutrition': {
                        'Calories': 0,
                        'Fat': 0,
                        'Saturates': 0,
                        'Sugar': 0,
                        'Salt': 0
                    },
                    'items_count': 0
                },
                'metadata': {
                    'timestamp': timestamp,
                    'total_detections': 0,
                    'image_size': {
                        'width': image.width,
                        'height': image.height
                    },
                    'threshold': threshold
                }
            }), 200

        # -------------------------
        # Draw boxes & upload
        # -------------------------
        image_with_boxes = draw_boxes(image.copy(), foods)

        image_url = upload_image_to_cloudinary(
            image_with_boxes,
            folder="food-detection/annotated"
        )

        # -------------------------
        # Nutrition analysis
        # -------------------------
        nutrition_analysis = calculate_total_nutrition(results)

        detection_summary = [
            {
                'detected_class': r['detected_class'],
                'disease': None,
                'detection_confidence': r['confidence']
            }
            for r in results
        ]

        # -------------------------
        # Response
        # -------------------------
        return jsonify({
            'status': 'success',
            'image_url': image_url,
            'detection': results,
            'nutrition_analysis': nutrition_analysis,
            'metadata': {
                'timestamp': timestamp,
                'total_detections': len(results),
                'image_size': {
                    'width': image.width,
                    'height': image.height
                },
                'detection_summary': detection_summary,
                'threshold': threshold
            }
        }), 200
