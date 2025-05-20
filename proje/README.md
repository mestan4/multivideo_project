# 📷  Multi-Source Video Analytics & Streaming Platform

This project provides multi-camera streaming, real-time AI-based person detection, RTSP/MJPEG streaming, MQTT event notifications, and a dynamic web-based control panel.

---

## 🚀 Features

* 🔌 Multi webcam / IP camera ingestion
* 🧠 Person detection using YOLOv5
* 🎥 GStreamer-based RTSP streaming (annotated frames)
* 🌐 MJPEG stream (for web dashboard & client viewers)
* 📡 MQTT-based person count publishing
* 🖥️ Web-based dashboard for controlling streams

---

## 📁 File Structure

```
project/
├── main_server.py         # Main Flask + RTSP + MQTT server
├── gstreamer_server.py    # gstreamer server
├── yolo_detector.py       # YOLOv5 detection module
├── mqtt_module.py         # MQTT client wrapper
├── client_viewer.py       # OpenCV + MQTT viewer client
├── requirements.txt       # Python dependencies
├── test_stream.sh         # Bash script for testing stream
└── README.md              # This documentation
```

---

## ⚙️ Installation

### 🐍 Python Packages

```bash
pip install -r requirements.txt
```

### 🧱 System Packages (Ubuntu)

```bash
sudo apt update
sudo apt install -y \
    python3-gi \
    gir1.2-gst-rtsp-server-1.0 \
    gstreamer1.0-tools \
    mosquitto \
    mosquitto-clients
```

---

## ▶️ Usage

### 🔧 Start the Server

```bash
python3 gstreamer_server.py
```

### 🎦 Start a Camera Stream

```bash
curl -X POST http://localhost:8000/stream/start \
     -H "Content-Type: application/json" \
     -d '{"id": "cam1", "url": 0}'
```

### 🌐 Web Dashboard

Open in browser:

```
http://localhost:8000/dashboard
```

### 📺 RTSP Stream via VLC

```
rtsp://localhost:8554/raw/cam_id
```

### 🧪 Test Script

```bash
bash test_stream.sh
```

---

## 🧠 Notes

* MJPEG stream is available via `/video/<cam_id>` endpoint.
* Person count is published to MQTT topic: `events/<cam_id>/person`
* Cameras can be dynamically added or removed.

---

## 🛠️ Requirements

* Python 3.9+
* OpenCV, Flask, PyTorch, GStreamer, Paho MQTT

---

