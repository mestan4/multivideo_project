Intelligent Multi-Source Video Analytics & Streaming Platform
# Intelligent Multi-Source Video Analytics & Streaming Platform

## 📌 Project Overview
This project implements a **real-time video analytics and streaming platform** that:
- Accepts multiple camera streams (or video files)
- Performs real-time **object/person detection** using **YOLOv5**
- Streams annotated video via **RTSP (GStreamer)** and **HTTP MJPEG (Flask)**
- Allows camera management through a **web dashboard**

## 🧠 Technologies Used
- **Python 3.9**
- **Flask** – REST API & MJPEG video server
- **GStreamer & RTSP Server** – Real-time streaming backend
- **YOLOv5 (Ultralytics)** – Deep learning-based object detection
- **OpenCV** – Frame capture and processing
- **Docker** – Containerized environment for deployment

## 🛠️ Features
- RTSP-based video output with low-latency H.264 encoding
- Web dashboard for starting/stopping video sources
- MJPEG HTTP endpoint for live monitoring
- Support for camera index (e.g., webcam) or video file inputs
- Modular architecture: RTSP server, Flask server, Detection thread

## 📂 Project Structure
main_server.py           # Flask server + GStreamer RTSP integration
yolo_detector.py         # YOLOv5 inference wrapper
gstreamer_server.py      # (Optional) Standalone RTSP server module
client_viewer.py         # Client RTSP viewer example
mqtt_module.py           # (Optional) MQTT event publishing (disabled)
requirements.txt         # Dependencies
Dockerfile               # Image definition
docker-compose.yml       # Deployment script
video1.mp4 / video2.mp4  # Sample test videos (user-provided)

## 🌐 API Endpoints
| Endpoint             | Method | Description                        |
|----------------------|--------|------------------------------------|
| `/dashboard`         | GET    | HTML dashboard to control streams  |
| `/stream/start`      | POST   | Start stream with form: `id`, `url`|
| `/stream/stop`       | POST   | Stop stream with form: `id`        |
| `/video/<cam_id>`    | GET    | MJPEG stream from specified cam    |
| `/status`            | GET    | List of currently active streams   |

## 🧪 How to Run (Locally via Docker)
1. Place `video1.mp4` and `video2.mp4` inside your project directory.
2. Build and run the container:
```
docker-compose up --build
```
3. Open your browser at:
```
http://localhost:8000/dashboard
```
4. Start a stream using the form (e.g., `video1.mp4`).
5. View live stream at:
```
http://localhost:8000/video/cam1
```

## 🎯 Notes
- If using webcam, use `0` as the camera URL.
- For testing on macOS, prefer video file input instead of camera index.
- For production, run the Flask server behind a WSGI server like Gunicorn.

## 📦 Future Improvements
- Add user authentication to the dashboard
- Integrate database logging of detection events
- Enable MQTT for real-time alerting
- Add support for multi-class object detection reports

---
 Tolgahan Mestan Kaya 2103272 – Cağın Hakan Denizci 2003371 -CMP4221 Project Submission

