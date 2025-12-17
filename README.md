1. Giới thiệu

Dự án Calorie Tracker nhằm hỗ trợ người dùng theo dõi lượng năng lượng nạp vào và tiêu hao hàng ngày, dựa trên các kiến thức y khoa chuẩn về chuyển hóa cơ bản (BMR), tổng năng lượng tiêu hao hàng ngày (TDEE), và mục tiêu năng lượng dựa trên chế độ ăn và hoạt động thể chất.

Các kiến thức này được tích hợp trực tiếp vào hệ thống qua các model, service và API, giúp người dùng nhận được dữ liệu cá nhân hóa về năng lượng, từ đó hỗ trợ quyết định chế độ ăn uống và hoạt động thể chất hợp lý.

2. Các kiến thức y khoa áp dụng
2.1. Basal Metabolic Rate (BMR)

Định nghĩa:
BMR là lượng năng lượng cơ thể cần để duy trì các chức năng cơ bản khi nghỉ ngơi (hô hấp, tuần hoàn, trao đổi chất, duy trì nhiệt độ cơ thể).

Công thức tính:
Trong dự án, sử dụng Mifflin-St Jeor Equation, một công thức được công nhận trong y khoa hiện đại:

Nam:

𝐵
𝑀
𝑅
=
10
×
c
a
ˆ
n nặng (kg)
+
6.25
×
chi
e
ˆ
ˋ
u cao (cm)
−
5
×
tuổi (n
a
˘
m)
+
5
BMR=10×c
a
ˆ
n nặng (kg)+6.25×chi
e
ˆ
ˋ
u cao (cm)−5×tuổi (n
a
˘
m)+5

Nữ:

𝐵
𝑀
𝑅
=
10
×
c
a
ˆ
n nặng (kg)
+
6.25
×
chi
e
ˆ
ˋ
u cao (cm)
−
5
×
tuổi (n
a
˘
m)
−
161
BMR=10×c
a
ˆ
n nặng (kg)+6.25×chi
e
ˆ
ˋ
u cao (cm)−5×tuổi (n
a
˘
m)−161

Triển khai trong dự án:

Dữ liệu chiều cao, cân nặng và ngày sinh lấy từ bảng UserProfile và UserProfileWeightHistory.

Nếu người dùng chưa có lịch sử cân nặng, BMR trả về 0 để tránh lỗi tính toán.

BMR được lưu trong trường base_calorie_out của DailyEnergyLog.

Ý nghĩa y khoa: BMR là nền tảng để tính năng lượng cần thiết, giúp cá nhân hóa kế hoạch dinh dưỡng và tránh nguy cơ dư thừa hoặc thiếu năng lượng.

2.2. Total Daily Energy Expenditure (TDEE)

Định nghĩa:
TDEE là tổng năng lượng tiêu hao trong ngày, bao gồm:

BMR – năng lượng cơ bản để duy trì cơ thể lúc nghỉ ngơi.

Thermic Effect of Food (TEF) – năng lượng tiêu hao để tiêu hóa và hấp thụ thực phẩm (tạm tính trong tổng calorie in).

Activity Calories – năng lượng tiêu hao do hoạt động thể chất (hoạt động thể thao, sinh hoạt hàng ngày).

Triển khai trong dự án:

Trường tdee trong DailyEnergyLog lưu giá trị tổng năng lượng tiêu hao, tính toán theo:

𝑇
𝐷
𝐸
𝐸
=
𝐵
𝑀
𝑅
×
hệ s
o
ˆ
ˊ
 hoạt động
TDEE=BMR×hệ s
o
ˆ
ˊ
 hoạt động

Hệ số hoạt động được dựa trên ActivityLevelEnum, bao gồm:

Hoạt động	Hệ số
Sedentary (ít vận động)	1.2
Lightly active (vận động nhẹ)	1.375
Moderately active (vận động vừa)	1.55
Very active (vận động nhiều)	1.725

Năng lượng tiêu hao từ hoạt động cụ thể được cộng thêm từ bảng Activity vào activity_calorie_out.

Ý nghĩa y khoa: TDEE phản ánh chính xác nhu cầu năng lượng của cơ thể theo ngày, giúp xác định mức ăn phù hợp để giảm, duy trì hoặc tăng cân.

2.3. Goal-based Calorie Target

Định nghĩa:
Mỗi người có mục tiêu năng lượng dựa trên mong muốn về cân nặng:

Lose weight (giảm cân): giảm ~500 kcal/ngày để giảm ~0.5 kg/tuần.

Maintain (duy trì cân nặng): năng lượng nạp = TDEE.

Gain weight (tăng cân): tăng ~300–500 kcal/ngày tùy mục tiêu.

Triển khai trong dự án:

Trường target_calorie trong DailyEnergyLog lưu giá trị này.

Mục tiêu được tính tự động dựa trên GoalTypeEnum.

Ý nghĩa y khoa: Hỗ trợ lập kế hoạch dinh dưỡng cá nhân hóa, tránh dư thừa hoặc thiếu năng lượng, phù hợp với tiêu chuẩn an toàn giảm cân / tăng cân.

2.4. Tracking Calorie In & Out

Calorie In (nạp vào):

Lấy từ food records, với các thông số: tên món, calorie, số lượng.

Tính tổng năng lượng nạp vào total_calorie_in.

Sử dụng dữ liệu từ FOOD_NUTRITION_DB để đảm bảo chính xác về dinh dưỡng.

Calorie Out (tiêu hao):

Gồm BMR + Activity Calories (activity_calorie_out).

Hoạt động thể chất nhập vào từ người dùng hoặc qua detection (ảnh thức ăn/hoạt động).

Net Calorie (cân bằng năng lượng):

𝑁
𝑒
𝑡
𝐶
𝑎
𝑙
𝑜
𝑟
𝑖
𝑒
=
𝑇
𝑜
𝑡
𝑎
𝑙
𝐶
𝑎
𝑙
𝑜
𝑟
𝑖
𝑒
𝐼
𝑛
−
𝐵
𝑎
𝑠
𝑒
𝐶
𝑎
𝑙
𝑜
𝑟
𝑖
𝑒
𝑂
𝑢
𝑡
−
𝐴
𝑐
𝑡
𝑖
𝑣
𝑖
𝑡
𝑦
𝐶
𝑎
𝑙
𝑜
𝑟
𝑖
𝑒
𝑂
𝑢
𝑡
NetCalorie=TotalCalorieIn−BaseCalorieOut−ActivityCalorieOut

Ý nghĩa y khoa:

Net calorie dương → dư năng lượng, có thể tăng cân.

Net calorie âm → thiếu năng lượng, có thể giảm cân.

Net calorie ≈ 0 → duy trì cân nặng hiện tại.

2.5. Age, Gender & Historical Weight

Tuổi ảnh hưởng trực tiếp đến BMR (người già BMR thấp hơn).

Giới tính: nam giới thường BMR cao hơn nữ giới cùng cân nặng và chiều cao.

Lịch sử cân nặng: chọn giá trị cân nặng gần nhất để tính BMR chính xác, đặc biệt nếu người dùng thay đổi cân nặng thường xuyên.

2.6. Khuyến nghị y khoa được áp dụng

Sử dụng công thức chuẩn y khoa (Mifflin-St Jeor) thay vì công thức tùy ý.

Tính cá nhân hóa dựa trên giới tính, tuổi, chiều cao, cân nặng.

Cập nhật dữ liệu lịch sử cân nặng để BMR và TDEE chính xác theo thời gian.

Theo dõi Net Calorie hàng ngày để cảnh báo dư/thiếu năng lượng.

Định nghĩa các mức hoạt động thể chất chuẩn theo y học thể thao (sedentary → very active).

Tính toán mục tiêu calo dựa trên GoalTypeEnum, giúp người dùng an toàn giảm/gain cân.

2.7. Lợi ích lâm sàng của dự án

Giúp người dùng kiểm soát cân nặng một cách khoa học.

Dự phòng bệnh lý liên quan đến thừa cân/thiếu cân: béo phì, tiểu đường, loãng xương.

Hỗ trợ chế độ ăn cá nhân hóa, tránh suy dinh dưỡng hoặc ăn quá nhiều.

Tích hợp hoạt động thể chất, giúp theo dõi calo tiêu hao thực tế.

3. Các bảng dữ liệu liên quan
Table	Chức năng
UserProfile	Thông tin cơ bản người dùng: email, giới tính, ngày sinh
UserProfileWeightHistory	Lịch sử cân nặng để tính BMR chính xác
DailyEnergyLog	Lưu log năng lượng hàng ngày: calorie in, BMR, TDEE, activity out, target calorie
FoodRecord	Lưu thông tin món ăn: tên, calo, số lượng
Activity	Lưu hoạt động thể chất và calo tiêu hao
4. Tóm tắt

Dự án Calorie Tracker là sự kết hợp giữa:

Kiến thức y khoa về chuyển hóa năng lượng.

Công nghệ theo dõi dữ liệu cá nhân (Flask + SQLAlchemy + JWT).

Công thức tính BMR/TDEE/Net Calorie chuẩn xác.

Mục tiêu cuối cùng là giúp người dùng lập kế hoạch ăn uống và vận động hợp lý, dựa trên cơ sở y khoa, an toàn và cá nhân hóa.