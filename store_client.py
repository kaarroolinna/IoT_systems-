import json
import paho.mqtt.client as mqtt

class StoreClient:
    def __init__(self, broker="localhost", port=1883, topic="processed_data_topic"):
        self.broker = broker
        self.port = port
        self.topic = topic

        self.client = mqtt.Client()
        self.latest_data = None

        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        try:
            self.client.connect(self.broker, self.port)
            self.client.loop_start()
        except Exception as e:
            print(f"[StoreClient] MQTT not available: {e}")

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("[StoreClient] Connected to MQTT")
            self.client.subscribe(self.topic)

    def on_message(self, client, userdata, msg):
        try:
            payload = msg.payload.decode("utf-8")
            data = json.loads(payload)

            gps = data["agent_data"]["gps"]
            road_state = data["road_state"]

            self.latest_data = {
                "lat": gps["lat"],
                "lon": gps["lon"],
                "road_state": road_state
            }

        except Exception as e:
            print(f"[StoreClient] Error: {e}")

    def get_data(self):
        return self.latest_data