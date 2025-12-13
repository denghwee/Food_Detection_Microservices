from flask import request, jsonify, render_template
import uuid
import time
import datetime
import io
import numpy as np
from PIL import Image

from ..config import Config
from ..services import FoodDetectionService
from ..utils import apply_nms, deduplicate_by_label, draw_boxes, image_to_base64, calculate_total_nutrition


def register_routes(app):

    @app.route('/')
    def home():
        return render_template('index.html')
    
    @app.route('/detect', methods=['GET', 'POST'])
    def detect():
        """food-detection pipeline.

        Returns all food items above configured threshold.
        """
        if request.method == 'GET':
            return jsonify({'status': 'ready'}), 200

        file = request.files.get('image')
        if not file:
            return jsonify({'error': 'No image uploaded.'}), 400

        image = Image.open(io.BytesIO(file.read())).convert('RGB')

        try:
            service = FoodDetectionService()
            foods = service.detect(image)
        except Exception as error:
            return jsonify({'error': str(error)}), 502

        # Normalize structure: expect list of {'class': name, 'confidence': float, 'bbox': [...]}
        foods = foods or []
        
        # Apply NMS to remove duplicate detections (same food + overlapping boxes)
        foods = apply_nms(foods, iou_threshold=0.5)
        
        # Final deduplication: keep only highest confidence per unique label
        foods = deduplicate_by_label(foods)

        # Filter by configured threshold and create results
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

        if not results:
            return jsonify({
                'status': 'success',
                'annotated_image_base64': image_to_base64(image),
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
                    'timestamp': datetime.datetime.now().isoformat(),
                    'total_detections': 0,
                    'image_size': {
                        'width': image.width,
                        'height': image.height
                    },
                    'detection_summary': []
                }
            })

        # Annotated image with boxes
        image_with_boxes = draw_boxes(image.copy(), foods)
        encoded_img = image_to_base64(image_with_boxes)

        # Create detection summary
        detection_summary = [
            {
                'detected_class': r['detected_class'],
                'disease': None,
                'detection_confidence': r['confidence'],
            }
            for r in results
        ]
        
        # Calculate nutrition analysis
        nutrition_analysis = calculate_total_nutrition(results)

        return jsonify({
            'status': 'success',
            'annotated_image_base64': encoded_img,
            'detection': results,
            'nutrition_analysis': nutrition_analysis,
            'metadata': {
                'timestamp': datetime.datetime.now().isoformat(),
                'total_detections': len(results),
                'image_size': {
                    'width': image.width,
                    'height': image.height
                },
                'detection_summary': detection_summary,
                'threshold': threshold
            }
        })