import cv2
import threading
import paho.mqtt.client as mqtt
import requests
import time

API_SERVER = "http://localhost:8000"
DEFAULT_STREAM_ID = "video1"
DEFAULT_STREAM_URL = 1  # Yerel kamera (int olarak gönderiliyor)

# === Stream başlatıcı ===
def ensure_stream_running(cam_id=DEFAULT_STREAM_ID, cam_url=DEFAULT_STREAM_URL):
    print(f"[INFO] Checking or starting stream '{cam_id}'...")
    try:
        response = requests.post(f"{API_SERVER}/stream/start", json={
            "id": cam_id,
            "url": cam_url
        })
        if response.status_code == 200:
            print(f"[INFO] Stream '{cam_id}' started successfully.")
        elif response.status_code == 400 and "already running" in response.text:
            print(f"[INFO] Stream '{cam_id}' already running.")
        else:
            print(f"[WARNING] Could not start stream: {response.text}")
    except Exception as e:
        print(f"[ERROR] Failed to reach API: {e}")

# === RTSP endpoint'lerini API'den çek
def fetch_rtsp_streams():
    try:
        response = requests.get(f"{API_SERVER}/status")
        data = response.json()
        streams = data.get("streams", [])
        endpoints = data.get("rtsp_endpoints", [])
        return dict(zip(streams, endpoints))
    except Exception as e:
        print(f"[ERROR] Failed to fetch stream status: {e}")
        return {}

# === MQTT Dinleyici ===
def on_connect(client, userdata, flags, rc):
    print("[MQTT] Connected to broker")
    client.subscribe("events/#")

def on_message(client, userdata, msg):
    print(f"[MQTT] {msg.topic} → {msg.payload.decode()}")

def mqtt_listener():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect("localhost", 1883, 60)
    client.loop_forever()

# === RTSP Görüntüleyici ===
def show_stream(name, url):
    cap = cv2.VideoCapture(url)
    if not cap.isOpened():
        print(f"[ERROR] Could not open stream: {name} ({url})")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            print(f"[{name}] Frame read failed.")
            break
        cv2.imshow(f"Stream: {name}", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()

# === Ana Çalışma Bloğu ===
if __name__ == "__main__":
    # Otomatik olarak kamera başlat
    ensure_stream_running()

    print("[INFO] Fetching active RTSP streams from API...")
    time.sleep(1.5)  # API yanıtı hazır olsun diye ufak bekleme
    RTSP_STREAMS = fetch_rtsp_streams()

    if not RTSP_STREAMS:
        print("[WARNING] No active streams found after attempt.")
    else:
        print(f"[INFO] Found streams: {list(RTSP_STREAMS.keys())}")

        # MQTT thread başlat
        threading.Thread(target=mqtt_listener, daemon=True).start()

        # Her RTSP kaynağı için ayrı thread başlat
        for cam_name, cam_url in RTSP_STREAMS.items():
            threading.Thread(target=show_stream, args=(cam_name, cam_url), daemon=True).start()

        # Ana thread sonsuz beklesin
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Client terminated.")
