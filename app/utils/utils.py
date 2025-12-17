import base64
import os
import logging
from io import BytesIO
from PIL import Image, ImageDraw
import cloudinary
import cloudinary.uploader
import tempfile
from typing import List, Dict, Any
from ..data import FOOD_NUTRITION_DB
from datetime import date
from app.models.user_profile import UserProfile
from ..models.user_profile_weight_history import UserProfileWeightHistory
from app.models.daily_energy_log import DailyEnergyLog
from ..extensions import db
from app.enums.app_enum import ActivityLevelEnum, GoalTypeEnum

# -------------------- CALORIE / BMR / TDEE -------------------- #
ACTIVITY_FACTOR = {
    ActivityLevelEnum.sedentary: 1.2,
    ActivityLevelEnum.lightly_active: 1.375,
    ActivityLevelEnum.moderately_active: 1.55,
    ActivityLevelEnum.very_active: 1.725,
}

GOAL_ADJUSTMENT = {
    GoalTypeEnum.lose_weight: -500,
    GoalTypeEnum.maintain: 0,
    GoalTypeEnum.gain_weight: 500,
}

def get_latest_user_metrics(user_email: str):
    """
    Lấy thông tin chiều cao, cân nặng gần nhất của user
    từ bảng UserProfileWeightHistory để tính BMR
    """
    profile = UserProfile.query.filter_by(user_email=user_email).first()
    if not profile:
        return None, None, None, None

    last_history = (
        UserProfileWeightHistory.query
        .filter_by(user_profile_id=profile.id)
        .order_by(UserProfileWeightHistory.created_at.desc())
        .first()
    )

    if last_history:
        return last_history.height_cm, last_history.weight_kg, profile.gender, profile.date_of_birth
    else:
        # Nếu chưa có lịch sử cân nặng, fallback về profile hiện tại
        return None, None, profile.gender, profile.date_of_birth

def calculate_bmr_from_metrics(height_cm, weight_kg, gender, date_of_birth):
    """
    Tính BMR theo công thức Mifflin-St Jeor
    """
    if not all([height_cm, weight_kg, gender, date_of_birth]):
        return 0

    today = date.today()
    age = today.year - date_of_birth.year - (
        (today.month, today.day) < (date_of_birth.month, date_of_birth.day)
    )

    if gender.lower() == "male":
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161

    return int(bmr)

def calculate_bmr(user_email: str) -> int:
    """
    Wrapper để tiện test
    Lấy metrics gần nhất rồi tính BMR
    """
    height_cm, weight_kg, gender, dob = get_latest_user_metrics(user_email)
    return calculate_bmr_from_metrics(height_cm, weight_kg, gender, dob)

def calculate_tdee(user_email: str):
    """
    Tính TDEE và target calories dựa trên BMR, activity level và goal
    """
    profile = UserProfile.query.filter_by(user_email=user_email).first()
    if not profile:
        return 0, 0, 0

    height_cm, weight_kg, gender, dob = get_latest_user_metrics(user_email)
    bmr = calculate_bmr_from_metrics(height_cm, weight_kg, gender, dob)

    activity_factor = ACTIVITY_FACTOR.get(profile.activity_level, 1.2)
    tdee = int(bmr * activity_factor)

    goal_adjust = GOAL_ADJUSTMENT.get(profile.goal_type, 0)
    target_calorie = tdee + goal_adjust

    # Giới hạn y khoa
    if gender and gender.lower() == "female" and target_calorie < 1200:
        target_calorie = 1200
    elif gender and gender.lower() == "male" and target_calorie < 1500:
        target_calorie = 1500

    return bmr, tdee, target_calorie

def create_daily_logs_for_all_users():
    """
    Tạo DailyEnergyLog cho mỗi user vào ngày mới.
    base_calorie_out được tính từ BMR dựa trên
    chiều cao / cân nặng gần nhất.
    """
    today = date.today()
    users = UserProfile.query.all()

    for user in users:
        if DailyEnergyLog.query.filter_by(user_email=user.user_email, log_date=today).first():
            continue

        height_cm, weight_kg, gender, dob = get_latest_user_metrics(user.user_email)
        bmr, tdee, target_calorie = calculate_tdee(user.user_email)

        daily_log = DailyEnergyLog(
            user_email=user.user_email,
            log_date=today,
            base_calorie_out=bmr,
            tdee=tdee,
            target_calorie=target_calorie,
            total_calorie_in=0,
            activity_calorie_out=0,
            net_calorie=-target_calorie
        )

        db.session.add(daily_log)

    db.session.commit()

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
