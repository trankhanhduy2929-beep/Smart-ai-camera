# Smart-ai-camera
Dưới đây là bản mô tả chi tiết các tính năng cho Add-on "Smart Cam AI Manager" mà chúng ta đã xây dựng. Bạn có thể dùng nội dung này cho file README.md hoặc giới thiệu về Add-on.

📸 Smart Cam AI Manager - Mô tả Tính Năng
Smart Cam AI Manager là một Home Assistant Add-on mạnh mẽ giúp biến các camera giám sát thông thường (Imou, Ezviz, Hikvision, Dahua...) thành camera thông minh có khả năng nhận diện khuôn mặt và phát hiện chuyển động cục bộ (Local). Add-on hoạt động độc lập, bảo mật và tích hợp sâu vào Home Assistant.

🌟 1. Giao diện Quản lý Web (Web UI) Tích hợp
Thay vì phải chỉnh sửa các file cấu hình yaml phức tạp, bạn có thể quản lý mọi thứ trực quan ngay trên trình duyệt:

Sidebar Integration: Tích hợp trực tiếp vào thanh menu bên trái của Home Assistant (Ingress), không cần mở port ra ngoài internet.

Thêm/Xóa Camera Nóng: Thêm hoặc xóa luồng Camera RTSP ngay lập tức mà không cần khởi động lại Add-on hay Home Assistant.

Dashboard trực quan: Giao diện thiết kế hiện đại, dễ sử dụng trên cả máy tính và điện thoại.

🧠 2. Công nghệ AI Nhận diện & Xử lý Ảnh
Sử dụng thư viện OpenCV và thuật toán Haar Cascade để xử lý hình ảnh theo thời gian thực:

Phát hiện chuyển động (Motion Detection): Sử dụng thuật toán trừ nền (Background Subtraction) để phát hiện chuyển động. Giúp lọc bỏ các khung hình tĩnh, tiết kiệm tài nguyên hệ thống.

Nhận diện & Cắt khuôn mặt (Face Crop): Khi có chuyển động, AI sẽ quét tìm khuôn mặt. Nếu phát hiện, hệ thống sẽ tự động cắt riêng khuôn mặt và lưu lại thành ảnh nhỏ.

Bộ lọc thông minh: Chỉ ghi nhận khuôn mặt khi có chuyển động thực sự và có cơ chế "Cooldown" (thời gian chờ) để tránh spam thông báo liên tục.

🏠 3. Tự động tích hợp Home Assistant (MQTT Discovery)
Add-on giao tiếp với Home Assistant thông qua giao thức MQTT:

Zero Config: Không cần khai báo thủ công bất kỳ sensor nào trong file configuration.yaml.

Auto Discovery: Tự động tạo các Entity tương ứng ngay khi thêm Camera mới:

sensor.ten_camera_last_face: Chứa thời gian và tên file ảnh khuôn mặt mới nhất.

(Tùy chọn mở rộng) binary_sensor.ten_camera_motion: Trạng thái chuyển động.

📂 4. Thư viện Ảnh & Lưu trữ (Gallery)
Quản lý lịch sử ra vào dễ dàng:

Lưu trữ cục bộ (Local Storage): Ảnh khuôn mặt được lưu trực tiếp trên ổ cứng của Home Assistant (trong thư mục /share hoặc /data), đảm bảo quyền riêng tư tuyệt đối, không gửi ảnh lên Cloud bên thứ 3.

Xem lại lịch sử (Gallery Viewer): Xem lại toàn bộ các khuôn mặt đã bắt được ngay trên Web UI.

Bộ lọc tìm kiếm: Hỗ trợ lọc ảnh theo Ngày/Tháng và theo từng Camera cụ thể.

⚡ 5. Hiệu năng & Tối ưu hóa
Được thiết kế để chạy trên các thiết bị cấu hình thấp như Raspberry Pi, Mini PC:

Đa luồng (Multi-threading): Mỗi camera chạy trên một luồng xử lý riêng biệt, đảm bảo độ mượt mà.

Tối ưu tài nguyên: Tự động resize khung hình trước khi xử lý AI để giảm tải CPU.

Cơ chế Reconnect: Tự động kết nối lại camera nếu bị mất mạng hoặc camera khởi động lại.

💡 Ứng dụng thực tế
Điểm danh thành viên: Ghi lại khuôn mặt những người ra vào cổng/cửa nhà theo thời gian thực.

Thông báo thông minh: Gửi ảnh khuôn mặt người vừa bấm chuông hoặc đi vào sân qua Telegram/Facebook Messenger (kết hợp với Automation của HA).

Giám sát an ninh: Xem nhanh hôm nay có người lạ nào lảng vảng trước nhà hay không thông qua tab Lịch sử.
