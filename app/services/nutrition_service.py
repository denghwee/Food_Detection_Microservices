from app.utils import calculate_total_nutrition


class NutritionService:
    @staticmethod
    def analyze(detections):
        return calculate_total_nutrition(detections)
