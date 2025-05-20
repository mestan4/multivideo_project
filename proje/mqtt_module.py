import paho.mqtt.client as mqtt
import threading
import json

class MQTTClient:
    def __init__(self, host='localhost', port=1883):
        self.host = host
        self.port = port
        self.client = mqtt.Client()
        self.subscriptions = {}

        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

    def connect(self):
        self.client.connect(self.host, self.port, 60)
        thread = threading.Thread(target=self.client.loop_forever)
        thread.daemon = True
        thread.start()
        print(f"[MQTT] Connected to {self.host}:{self.port}")

    def _on_connect(self, client, userdata, flags, rc):
        print("[MQTT] Connected with result code", rc)
        for topic in self.subscriptions:
            client.subscribe(topic)
            print(f"[MQTT] Resubscribed to: {topic}")

    def _on_message(self, client, userdata, msg):
        callback = self.subscriptions.get(msg.topic)
        if callback:
            try:
                payload = json.loads(msg.payload.decode())
            except:
                payload = msg.payload.decode()
            callback(msg.topic, payload)

    def publish_event(self, cam_id, event_type, payload=None):
        topic = f"events/{cam_id}/{event_type}"
        payload = payload or {}
        message = json.dumps(payload)
        self.client.publish(topic, message)
        print(f"[MQTT] Published to {topic}: {message}")

    def subscribe(self, topic, callback):
        self.subscriptions[topic] = callback
        self.client.subscribe(topic)
        print(f"[MQTT] Subscribed to: {topic}")