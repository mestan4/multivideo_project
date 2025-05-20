FROM debian:bullseye

# Gerekli sistem paketlerini yükle
RUN apt-get update && apt-get install -y \
    python3 python3-pip \
    python3-gi \
    gstreamer1.0-tools \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    libgirepository1.0-dev \
    gir1.2-gst-rtsp-server-1.0 \
    libglib2.0-dev \
    libgstreamer1.0-dev \
    libgstreamer-plugins-base1.0-dev \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Çalışma dizini
WORKDIR /app

# Tüm proje dosyalarını kopyala
COPY . .

# Python bağımlılıklarını yükle
RUN pip3 install --no-cache-dir -r requirements.txt

# Uygulama başlangıç komutu
CMD ["python3", "main_server.py"]

