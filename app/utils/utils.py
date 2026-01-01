import base64
import os
import logging
from io import BytesIO
from PIL import Image, ImageDraw
import cloudinary
import cloudinary.uploader
import tempfile
from typing import List, Dict, Any

from flask import current_app

from ..data import FOOD_NUTRITION_DB



# -------------------- IMAGE / DETECTION -------------------- #

def crop_regions(image, detections):
    crops = []
    for det in detections:
        x1, y1, x2, y2 = map(int, det['bbox'])
        crop = image.crop((x1, y1, x2, y2))
        crops.append(crop)
    return crops

def draw_boxes(image, detections):
    draw = ImageDraw.Draw(image)
    for det in detections:
        x1, y1, x2, y2 = map(int, det['bbox'])
        draw.rectangle((x1, y1, x2, y2), outline="red", width=3)
        draw.text((x1, y1 - 10), f"{det['class']} ({det['confidence']:.2f})", fill="red")
    return image

def image_to_base64(image, format="JPEG"):
    buffered = BytesIO()
    image.save(buffered, format=format)
    img_bytes = buffered.getvalue()
    encoded = base64.b64encode(img_bytes).decode('utf-8')
    return encoded

# -------------------- NMS / DEDUP -------------------- #
def calculate_iou(box1, box2):
    x1_min, y1_min, x1_max, y1_max = box1
    x2_min, y2_min, x2_max, y2_max = box2
    inter_xmin = max(x1_min, x2_min)
    inter_ymin = max(y1_min, y2_min)
    inter_xmax = min(x1_max, x2_max)
    inter_ymax = min(y1_max, y2_max)
    if inter_xmax < inter_xmin or inter_ymax < inter_ymin:
        return 0.0
    inter_area = (inter_xmax - inter_xmin) * (inter_ymax - inter_ymin)
    box1_area = (x1_max - x1_min) * (y1_max - y1_min)
    box2_area = (x2_max - x2_min) * (y2_max - y2_min)
    union_area = box1_area + box2_area - inter_area
    if union_area == 0:
        return 0.0
    return inter_area / union_area

def apply_nms(detections: List[Dict[str, Any]], iou_threshold: float = 0.5) -> List[Dict[str, Any]]:
    if not detections:
        return []
    class_groups = {}
    for det in detections:
        class_name = det['class']
        if class_name not in class_groups:
            class_groups[class_name] = []
        class_groups[class_name].append(det)
    merged_detections = []
    for class_name, class_dets in class_groups.items():
        if not class_dets:
            continue
        class_dets = sorted(class_dets, key=lambda x: -float(x['confidence']))
        clusters = []
        for i, det_i in enumerate(class_dets):
            found_cluster = False
            for cluster in clusters:
                for j in cluster:
                    det_j = class_dets[j]
                    iou = calculate_iou(det_i['bbox'], det_j['bbox'])
                    if iou > iou_threshold:
                        cluster.append(i)
                        found_cluster = True
                        break
                if found_cluster:
                    break
            if not found_cluster:
                clusters.append([i])
        for cluster in clusters:
            if not cluster:
                continue
            cluster_dets = [class_dets[i] for i in cluster]
            best_det = max(cluster_dets, key=lambda x: float(x['confidence']))
            all_boxes = [det['bbox'] for det in cluster_dets]
            x1_min = min(box[0] for box in all_boxes)
            y1_min = min(box[1] for box in all_boxes)
            x1_max = max(box[2] for box in all_boxes)
            y1_max = max(box[3] for box in all_boxes)
            merged_det = best_det.copy()
            merged_det['bbox'] = [x1_min, y1_min, x1_max, y1_max]
            merged_detections.append(merged_det)
    return merged_detections

def deduplicate_by_label(detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not detections:
        return []
    label_best = {}
    for det in detections:
        class_name = det['class']
        if class_name not in label_best or float(det['confidence']) > float(label_best[class_name]['confidence']):
            label_best[class_name] = det
    result = list(label_best.values())
    result = sorted(result, key=lambda x: -float(x['confidence']))
    return result

# -------------------- NUTRITION -------------------- #

def get_nutrition_by_name(food_name: str) -> dict:
    normalized_name = food_name.strip().lower()
    for food_item in FOOD_NUTRITION_DB:
        if food_item['name'].lower() == normalized_name:
            return {
                'name': food_item['name'],
                'serving_type': food_item['serving_type'],
                'nutrition': food_item['nutrition']
            }
    return None

def calculate_total_nutrition(detections: list) -> dict:
    total_nutrition = {'Calories':0,'Fat':0,'Carbs':0,'Protein':0}
    nutrition_details = []
    for det in detections:
        food_name = det.get('detected_class','')
        nutrition_info = get_nutrition_by_name(food_name)
        if nutrition_info:
            nutrition_details.append(nutrition_info)
            for key in total_nutrition.keys():
                total_nutrition[key] += nutrition_info['nutrition'].get(key,0)
    return {'individual_items': nutrition_details,'total_nutrition': total_nutrition,'items_count': len(nutrition_details)}

# -------------------- CLOUDINARY -------------------- #

def upload_base64_to_cloudinary(base64_str, folder="skin_analysis"):
    if base64_str.startswith("data:image"):
        base64_str = base64_str.split(",")[1]
    image_bytes = base64.b64decode(base64_str)
    has_cloudinary_url = bool(os.environ.get("CLOUDINARY_URL"))
    has_individual = bool(
        os.environ.get("CLOUDINARY_API_KEY") and os.environ.get("CLOUDINARY_API_SECRET") and os.environ.get("CLOUDINARY_CLOUD_NAME")
    )
    if not (has_cloudinary_url or has_individual or getattr(cloudinary.config(),'api_key',None)):
        logging.warning("Cloudinary credentials not found - returning base64 data URI as fallback.")
        return f"data:image/jpeg;base64,{base64_str}"
    with tempfile.NamedTemporaryFile(delete=False) as temp:
        temp.write(image_bytes)
        temp.flush()
        result = cloudinary.uploader.upload(temp.name, folder=folder, resource_type="image")
        return result.get("secure_url")
