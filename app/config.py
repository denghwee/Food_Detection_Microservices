import os

import cloudinary
from dotenv import load_dotenv
load_dotenv()

class Config:
    # ======= AI MODEL CONFIG =======
    FOOD_DETECTION_PATH = "app/models_AI/food_detection.pt"
    # JWT
    SECRET_KEY = "kfhsk3jh2k3hk2h3k2h3k2h3h23jh23j423423"
    JWT_SECRET_KEY = "Some_super_secure_and_long_base64_encoded_secret_key_for_JSWT123"
    JWT_ALGORITHM = "HS256"
    JWT_TOKEN_LOCATION = ["headers"]
    JWT_HEADER_NAME = "Authorization"
    JWT_HEADER_TYPE = "Bearer"

    JWT_ACCESS_TOKEN_EXPIRES = False
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
    SQLALCHEMY_DATABASE_URI = (
        "mysql+pymysql://root:KbTJJDSQZddVEFYHVWIEpiUqdXlDOrru@mainline.proxy.rlwy.net:26370/food_db?charset=utf8mb4&ssl_disabled=false"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CLOUDINARY_CLOUD_NAME = "dn9slxnjb"
    CLOUDINARY_API_KEY = "359329663246449"
    CLOUDINARY_API_SECRET = "RFsY2YDwjKTZH-8Ed9GF1jG2_V0"

    @staticmethod
    def init_cloudinary():
        cloudinary.config(
            cloud_name=Config.CLOUDINARY_CLOUD_NAME,
            api_key=Config.CLOUDINARY_API_KEY,
            api_secret=Config.CLOUDINARY_API_SECRET,
            secure=True
        )

