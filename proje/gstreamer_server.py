# === Intelligent Multi-Source Video Analytics & Streaming Platform ===
# main_server.py (Dual Stream: Raw & Annotated + Toggle Button)

import threading
import time
import json
import warnings
import numpy as np
import paho.mqtt.client as mqtt
from flask import Flask, Response, request, jsonify
from yolo_detector import YOLODetector

import gi

gi.require_version('Gst', '1.0')
gi.require_version('GstRtspServer', '1.0')
from gi.repository import Gst, GstRtspServer, GLib, GObject

Gst.init(None)
warnings.filterwarnings("ignore", category=FutureWarning)

detector = YOLODetector()
streams = {}
latest_frames = {}
raw_frames = {}
mqtt_client = None

# ========== RTSP Media Factory ==========
class RTSPMediaFactory(GstRtspServer.RTSPMediaFactory):
    def __init__(self, cam_id, use_raw=False):
        super().__init__()
        self.cam_id = cam_id
        self.use_raw = use_raw
        self.launch_string = (
            'appsrc name=source is-live=true block=true format=time do-timestamp=true '
            'caps="video/x-raw,format=BGR,width=640,height=480,framerate=30/1" ! '
            'videoconvert ! x264enc tune=zerolatency bitrate=512 speed-preset=superfast ! '
            'rtph264pay config-interval=1 name=pay0 pt=96'
        )
        self.set_launch(self.launch_string)
        self.set_shared(True)
        self.frame = None

    def do_configure(self, media):
        appsrc = media.get_element().get_child_by_name("source")
        appsrc.connect("need-data", self.on_need_data)

    def on_need_data(self, src, length):
        frame = raw_frames.get(self.cam_id) if self.use_raw else latest_frames.get(self.cam_id)
        if frame is None:
            return
        data = frame.tobytes()
        buf = Gst.Buffer.new_allocate(None, len(data), None)
        buf.fill(0, data)
        timestamp = Gst.util_uint64_scale(Gst.util_get_timestamp(), 1, Gst.SECOND)
        buf.pts = buf.dts = timestamp
        buf.duration = Gst.util_uint64_scale_int(1, Gst.SECOND, 30)
        src.emit("push-buffer", buf)

# ========== RTSP Server ==========
class RTSPServer:
    def __init__(self, port=8554):
        self.server = GstRtspServer.RTSPServer()
        self.server.set_service(str(port))
        self.mounts = self.server.get_mount_points()
        self.factories = {}
        self.loop = GLib.MainLoop()
        self.thread = threading.Thread(target=self.loop.run)

    def start(self):
        self.server.attach(None)
        self.thread.start()
        print("[RTSP] Server started at rtsp://localhost:8554/")

        
    def add_stream(self, cam_id):
        raw_factory = RTSPMediaFactory(cam_id, use_raw=True)
        annotated_factory = RTSPMediaFactory(cam_id, use_raw=False)

        self.mounts.add_factory(f"/raw/{cam_id}", raw_factory)
        self.mounts.add_factory(f"/annotated/{cam_id}", annotated_factory)

        self.factories[f"raw_{cam_id}"] = raw_factory
        self.factories[f"annotated_{cam_id}"] = annotated_factory

        print(f"[RTSP] Raw stream available at rtsp://localhost:8554/raw/{cam_id}")
        print(f"[RTSP] Annotated stream available at rtsp://localhost:8554/annotated/{cam_id}")


    def push_frame(self, cam_id, frame, raw=False):
        if raw:
            raw_frames[cam_id] = frame
        else:
            latest_frames[cam_id] = frame
        if cam_id in self.factories:
            self.factories[cam_id].frame = frame

rtsp_server = RTSPServer()
rtsp_server.start()

# ========== GStreamer Ingestion (No OpenCV) ==========
class GStreamerCamera(threading.Thread):
    def __init__(self, cam_id, device_index):
        super().__init__()
        self.cam_id = cam_id
        self.device_index = device_index
        self.running = False

    def run(self):
        pipeline_str = (
            f"v4l2src device=/dev/video{self.device_index} ! "
            "video/x-raw,width=640,height=480,framerate=30/1 ! "
            "videoconvert ! video/x-raw,format=BGR ! appsink name=sink emit-signals=true"
        )
        pipeline = Gst.parse_launch(pipeline_str)
        appsink = pipeline.get_by_name("sink")
        pipeline.set_state(Gst.State.PLAYING)
        self.running = True

        def on_new_sample(sink):
            sample = sink.emit("pull-sample")
            buf = sample.get_buffer()
            caps = sample.get_caps()
            w = caps.get_structure(0).get_value("width")
            h = caps.get_structure(0).get_value("height")
            success, mapinfo = buf.map(Gst.MapFlags.READ)
            if not success:
                return Gst.FlowReturn.ERROR
            frame = np.frombuffer(mapinfo.data, dtype=np.uint8).reshape((h, w, 3))
            buf.unmap(mapinfo)
            rtsp_server.push_frame(self.cam_id, frame, raw=True)
            annotated, people = detector.detect(frame)
            rtsp_server.push_frame(self.cam_id, annotated, raw=False)

            if mqtt_client:
                topic = f"events/{self.cam_id}/person"
                msg = json.dumps({"count": people})
                mqtt_client.publish(topic, msg)

            return Gst.FlowReturn.OK

        appsink.connect("new-sample", on_new_sample)

        bus = pipeline.get_bus()
        while self.running:
            msg = bus.timed_pop_filtered(100 * Gst.MSECOND, Gst.MessageType.ERROR | Gst.MessageType.EOS)
            if msg:
                print(f"[GStreamer] Message: {msg.type}")
                break

        pipeline.set_state(Gst.State.NULL)

    def stop(self):
        self.running = False

# ========== Flask Web Server ==========
app = Flask(__name__)

@app.route("/video/<cam_id>")
def video(cam_id):
    def gen():
        while True:
            frame = latest_frames.get(cam_id)
            if frame is not None:
                import cv2
                _, jpeg = cv2.imencode('.jpg', frame)
                yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
            time.sleep(0.05)
    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route("/video_raw/<cam_id>")
def video_raw(cam_id):
    def gen():
        while True:
            frame = raw_frames.get(cam_id)
            if frame is not None:
                import cv2
                _, jpeg = cv2.imencode('.jpg', frame)
                yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
            time.sleep(0.05)
    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route("/stream/start", methods=["POST"])
def start_stream():
    data = request.json
    cam_id = data.get("id")
    device = int(data.get("url", 0))
    if cam_id in streams:
        return jsonify({"status": "already running"})
    rtsp_server.add_stream(cam_id)
    worker = GStreamerCamera(cam_id, device)
    worker.start()
    streams[cam_id] = worker
    return jsonify({"status": f"started {cam_id}"})

@app.route("/stream/stop", methods=["POST"])
def stop_stream():
    data = request.json
    cam_id = data.get("id")
    worker = streams.pop(cam_id, None)
    if worker:
        worker.stop()
        return jsonify({"status": f"stopped {cam_id}"})
    return jsonify({"status": "not running"})

@app.route("/status")
def status():
    return jsonify({"active_streams": list(streams.keys())})

@app.route("/dashboard")
def dashboard():
    return '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <title>📷 Camera Control Dashboard</title>
      <style>
        body { font-family: Arial, sans-serif; background: #f4f4f4; padding: 20px; }
        h1 { text-align: center; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 20px; }
        .card { background: white; padding: 10px; border-radius: 10px; box-shadow: 0 0 8px rgba(0,0,0,0.1); }
        video, img { width: 100%; border-radius: 6px; }
        button { margin: 5px 0; width: 48%; padding: 8px; }
      </style>
    </head>
    <body>
      <h1>🎥 Intelligent Camera Stream Dashboard</h1>
      <div class="grid" id="cameraGrid"></div>

      <script>
        const cameras = ["cam1", "cam2", "cam3"]

        function createCameraCard(cam_id) {
          const card = document.createElement("div")
          card.className = "card"
          const streamType = cam_id === "cam1" ? "raw" : "annotated"
          card.innerHTML = `
            <h3>${cam_id}</h3>
            <p>RTSP: rtsp://localhost:8554/${streamType}/${cam_id}</p>
            <img id="img_${cam_id}" src="/video/${cam_id}" />
            <div>
              <button onclick="startStream('${cam_id}')">Start</button>
              <button onclick="stopStream('${cam_id}')">Stop</button>
            </div>
            <div>
              <button onclick="toggleStream('${cam_id}')">Toggle Raw/Annotated</button>
            </div>
            <p id="status_${cam_id}">Not running</p>
          `
          return card
        }

        function toggleStream(cam_id) {
          const img = document.getElementById(`img_${cam_id}`)
          const isRaw = img.src.includes("video_raw")
          img.src = isRaw ? `/video/${cam_id}` : `/video_raw/${cam_id}`
        }

        async function startStream(cam_id) {
          const res = await fetch("/stream/start", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ id: cam_id, url: 0 })
          });
          const json = await res.json()
          document.getElementById(`status_${cam_id}`).innerText = json.status || "Started"
        }

        async function stopStream(cam_id) {
          const res = await fetch("/stream/stop", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ id: cam_id })
          });
          const json = await res.json()
          document.getElementById(`status_${cam_id}`).innerText = json.status || "Stopped"
        }

        cameras.forEach(cam_id => {
          document.getElementById("cameraGrid").appendChild(createCameraCard(cam_id))
        });
      </script>
    </body>
    </html>
    '''

# ========== MQTT Setup ==========
def setup_mqtt():
    global mqtt_client
    mqtt_client = mqtt.Client()
    mqtt_client.connect("localhost", 1883, 60)
    mqtt_client.loop_start()

if __name__ == '__main__':
    setup_mqtt()
    app.run(host='0.0.0.0', port=8000, threaded=True)
