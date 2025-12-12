import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    # ======= AI MODEL CONFIG =======
    FOOD_DETECTION_PATH = "app/models_AI/food_detection.pt"

    IMG_SIZE = (640, 640)
    CONFIDENCE = 0.25
    CLASS_NAMES = [
        "Bánh canh", "Bánh chưng", "Bánh cuốn", "Bánh khọt", "Bánh mì", "Bánh tráng",
        "Bánh tráng trộn", "Bánh xèo", "Bò kho", "Bò lá lốt", "Bông cải", "Bún",
        "Bún bò Huế", "Bún chả", "Bún đậu", "Bún mắm", "Bún riêu", "Cá", "Cà chua",
        "Cà pháo", "Cà rốt", "Canh", "Chả", "Chả giò", "Chanh", "Cơm", "Cơm tấm",
        "Con người", "Củ kiệu", "Cua", "Đậu hũ", "Dưa chua", "Dưa leo",
        "Gỏi cuốn", "Hamburger", "Heo quay", "Hủ tiếu", "Khổ qua thịt", "Khoai tây chiên",
        "Lẩu", "Lòng heo", "Mì", "Mực", "Nấm", "Ốc", "Ớt chuông", "Phở", "Phô mai",
        "Rau", "Salad", "Thịt bò", "Thịt gà", "Thịt heo", "Thịt kho", "Thịt nướng",
        "Tôm", "Trứng", "Xôi", "Bánh bèo", "Cao lầu", "Mì Quảng",
        "Cơm chiên Dương Châu", "Bún chả cá", "Cơm chiên gà", "Cháo lòng",
        "Nộm hoa chuối", "Nui xào bò", "Súp cua"
    ]
    NUM_CLASSES = len(CLASS_NAMES)