# Food Detection Microservices

Dự án microservice phát hiện thức ăn và theo dõi calo sử dụng AI, hỗ trợ người dùng theo dõi lượng năng lượng nạp vào và tiêu hao hàng ngày dựa trên các kiến thức y khoa chuẩn về chuyển hóa cơ bản (BMR), tổng năng lượng tiêu hao hàng ngày (TDEE), và mục tiêu năng lượng dựa trên chế độ ăn và hoạt động thể chất.

## 🚀 Tính năng chính

### 1. Phát hiện thức ăn bằng AI
- Phát hiện và nhận diện hơn 60 loại món ăn Việt Nam từ hình ảnh
- Sử dụng mô hình ONNX (YOLO) để phát hiện đối tượng
- Phân tích dinh dưỡng tự động dựa trên món ăn được phát hiện
- Upload và lưu trữ hình ảnh trên Cloudinary

### 2. Theo dõi Calorie
- Quản lý bản ghi thức ăn (thêm, sửa, xóa, xem)
- Tính toán calo nạp vào từ các món ăn
- Theo dõi lịch sử ăn uống theo ngày

### 3. Daily Energy Log
- Tự động tạo log năng lượng hàng ngày (chạy lúc 00:00)
- Tính toán BMR (Basal Metabolic Rate) theo công thức Mifflin-St Jeor
- Tính toán TDEE (Total Daily Energy Expenditure) dựa trên mức độ hoạt động
- Theo dõi calo nạp vào (calorie in) và tiêu hao (calorie out)
- Tính toán net calorie và mục tiêu calo dựa trên mục tiêu của người dùng

### 4. User Profile
- Quản lý thông tin cá nhân (chiều cao, cân nặng, giới tính, ngày sinh)
- Lịch sử cân nặng theo thời gian
- Tích hợp với service xác thực bên ngoài

## 🛠️ Công nghệ sử dụng

- **Backend Framework**: Flask 3.1.2
- **Database**: MySQL (SQLAlchemy ORM)
- **AI/ML**: 
  - ONNX Runtime (food detection)
  - PyTorch, Ultralytics YOLO
- **Authentication**: Flask-JWT-Extended
- **Image Storage**: Cloudinary
- **Scheduler**: APScheduler (Flask-APScheduler)
- **Database Migration**: Flask-Migrate (Alembic)
- **Containerization**: Docker

## 📋 Yêu cầu hệ thống

- Python 3.11+
- MySQL Database
- Cloudinary account (cho lưu trữ hình ảnh)
- JWT token từ auth service

## 🔧 Cài đặt

### 1. Clone repository

```bash
git clone <repository-url>
cd Food_Detection_Microservices
```

### 2. Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### 3. Cấu hình môi trường

Tạo file `.env` hoặc cập nhật các biến môi trường trong `app/config.py`:

```python
# Database
SQLALCHEMY_DATABASE_URI = "mysql+pymysql://user:password@host:port/database"

# Cloudinary
CLOUDINARY_CLOUD_NAME = "your_cloud_name"
CLOUDINARY_API_KEY = "your_api_key"
CLOUDINARY_API_SECRET = "your_api_secret"

# JWT
JWT_SECRET_KEY = "your_secret_key"
```

### 4. Chạy migrations

```bash
flask db upgrade
```

### 5. Chạy ứng dụng

**Development:**
```bash
python run.py
```

**Docker:**
```bash
docker build -t food-detection-microservice .
docker run -p 5002:5002 food-detection-microservice
```

Ứng dụng sẽ chạy tại `http://localhost:5002`

## 📡 API Endpoints

### Food Detection

- `GET /api/v2/detect` - Health check
- `POST /api/v2/detect` - Phát hiện thức ăn từ hình ảnh
  - **Headers**: `Authorization: Bearer <token>`
  - **Body**: `multipart/form-data` với field `image`
  - **Response**: Detection results, nutrition analysis, annotated image URL

### Calorie Management

- `GET /api/v2/calories/food-records?log_date=YYYY-MM-DD` - Lấy danh sách bản ghi thức ăn
- `POST /api/v2/calories/food-records` - Thêm bản ghi thức ăn mới
- `PUT /api/v2/calories/food-records/<record_id>` - Cập nhật bản ghi thức ăn
- `DELETE /api/v2/calories/food-records/<record_id>` - Xóa bản ghi thức ăn

### Daily Energy Log

- `GET /api/v2/daily-logs?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD` - Lấy log năng lượng theo khoảng thời gian
- `POST /api/v2/daily-logs/generate` - Tạo log năng lượng thủ công (test)
- `POST /api/v2/daily-logs/steps` - Cập nhật số bước chân

### User Profile

- `GET /api/v2/user-profile` - Lấy thông tin profile
- `POST /api/v2/user-profile` - Tạo profile mới
- `PUT /api/v2/user-profile` - Cập nhật profile
- `GET /api/v2/user-profile/weight-history` - Lấy lịch sử cân nặng
- `GET /api/v2/user-profile/ai/profile-input` - Lấy dữ liệu input cho AI profile
- `GET /api/v2/user-profile/ai/goal-input` - Lấy dữ liệu input cho AI goal

## 🧠 Kiến thức y khoa áp dụng

### 1. Basal Metabolic Rate (BMR)

BMR là lượng năng lượng cơ thể cần để duy trì các chức năng cơ bản khi nghỉ ngơi.

**Công thức Mifflin-St Jeor:**

- **Nam**: `BMR = 10 × cân nặng (kg) + 6.25 × chiều cao (cm) - 5 × tuổi (năm) + 5`
- **Nữ**: `BMR = 10 × cân nặng (kg) + 6.25 × chiều cao (cm) - 5 × tuổi (năm) - 161`

BMR được lưu trong trường `base_calorie_out` của `DailyEnergyLog`.

### 2. Total Daily Energy Expenditure (TDEE)

TDEE là tổng năng lượng tiêu hao trong ngày, bao gồm:
- BMR – năng lượng cơ bản
- Activity Calories – năng lượng từ hoạt động thể chất

**Công thức:** `TDEE = BMR × hệ số hoạt động`

**Hệ số hoạt động:**
- Sedentary (ít vận động): 1.2
- Lightly active (vận động nhẹ): 1.375
- Moderately active (vận động vừa): 1.55
- Very active (vận động nhiều): 1.725

### 3. Goal-based Calorie Target

Mục tiêu năng lượng dựa trên mục tiêu cân nặng:
- **Lose weight**: TDEE - 500 kcal/ngày (~0.5 kg/tuần)
- **Maintain**: TDEE
- **Gain weight**: TDEE + 300-500 kcal/ngày

### 4. Net Calorie

Cân bằng năng lượng: `Net Calorie = Total Calorie In - Base Calorie Out - Activity Calorie Out`

- Net calorie dương → dư năng lượng, có thể tăng cân
- Net calorie âm → thiếu năng lượng, có thể giảm cân
- Net calorie ≈ 0 → duy trì cân nặng

## 📊 Cấu trúc Database

### Các bảng chính

| Bảng | Chức năng |
|------|-----------|
| `UserProfile` | Thông tin cơ bản người dùng: email, giới tính, ngày sinh, chiều cao |
| `UserProfileWeightHistory` | Lịch sử cân nặng để tính BMR chính xác |
| `DailyEnergyLog` | Log năng lượng hàng ngày: calorie in, BMR, TDEE, activity out, target calorie |
| `FoodRecord` | Bản ghi thức ăn: tên món, calo, số lượng, ngày |
| `Activity` | Hoạt động thể chất và calo tiêu hao |

## 🤖 AI Model

- **Model**: YOLO-based food detection model
- **Format**: ONNX (optimized for inference)
- **Classes**: 60+ món ăn Việt Nam (Bánh mì, Phở, Bún chả, Cơm, v.v.)
- **Input Size**: 640x640
- **Confidence Threshold**: 0.25

## ⏰ Scheduled Jobs

- **Daily Log Job**: Tự động tạo `DailyEnergyLog` cho tất cả người dùng lúc 00:00 mỗi ngày

## 📁 Cấu trúc thư mục

```
Food_Detection_Microservices/
├── app/
│   ├── controllers/          # API controllers
│   ├── services/              # Business logic
│   ├── services_AI/          # AI services (food detection)
│   ├── models/                # Database models
│   ├── models_AI/             # AI model files (.onnx, .pt)
│   ├── routes/                # Route definitions
│   ├── utils/                 # Utility functions
│   ├── jobs/                  # Scheduled jobs
│   ├── config.py              # Configuration
│   └── __init__.py            # App factory
├── migrations/                # Database migrations
├── Dockerfile                 # Docker configuration
├── requirements.txt           # Python dependencies
└── run.py                     # Application entry point
```

## 🔐 Authentication

Tất cả API endpoints (trừ health check) yêu cầu JWT token trong header:

```
Authorization: Bearer <your_jwt_token>
```

Token được lấy từ auth service bên ngoài.

## 🐳 Docker

Build và chạy với Docker:

```bash
# Build image
docker build -t food-detection-microservice .

# Run container
docker run -p 5002:5002 \
  -e MICRO_HOST=0.0.0.0 \
  -e MICRO_PORT=5002 \
  food-detection-microservice
```

## 📝 Notes

- Model AI được load vào memory khi service khởi động
- Hình ảnh được upload lên Cloudinary và trả về URL
- Daily logs được tạo tự động mỗi ngày lúc 00:00
- BMR được tính dựa trên cân nặng gần nhất trong lịch sử

## 📄 License

[Thêm thông tin license nếu có]

## 👥 Contributors

[Thêm thông tin contributors nếu có]
