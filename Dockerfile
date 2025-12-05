# Sử dụng Python 3.9 Slim (Debian based)
FROM python:3.9-slim

# Thiết lập biến môi trường để Python không tạo file .pyc và log mượt hơn
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 1. Cài đặt các thư viện hệ thống cần thiết
# LƯU Ý QUAN TRỌNG: Đã thay 'libgl1-mesa-glx' bằng 'libgl1' vì Debian mới không còn gói cũ
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    wget \
    sqlite3 \
    procps \
    && rm -rf /var/lib/apt/lists/*

# 2. Tải model nhận diện khuôn mặt
RUN wget https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/haarcascade_frontalface_default.xml -O /haarcascade_frontalface_default.xml

# 3. Cài đặt các thư viện Python
RUN pip3 install --no-cache-dir \
    opencv-python-headless \
    paho-mqtt \
    flask \
    numpy \
    requests

# 4. Copy mã nguồn vào container
COPY run.sh /
COPY app.py /
COPY templates /templates
COPY static /static

# 5. Cấp quyền thực thi
RUN chmod a+x /run.sh

# 6. Chạy script
CMD [ "/run.sh" ]