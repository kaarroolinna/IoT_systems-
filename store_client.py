import json
import paho.mqtt.client as mqtt

MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "processed_data_topic"


class StoreClient:
    def __init__(self, broker=MQTT_BROKER, port=MQTT_PORT, topic=MQTT_TOPIC):
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
            print(f"[StoreClient] Connected to MQTT ({self.broker}:{self.port})")
            self.client.subscribe(self.topic)
        else:
            print(f"[StoreClient] Failed to connect, rc={rc}")

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
            print(f"[StoreClient] Error parsing message: {e}")

    def get_data(self):
        data = self.latest_data
        self.latest_data = None  # скидаємо після читання
        return data