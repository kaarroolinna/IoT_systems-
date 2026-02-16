from paho.mqtt import client as mqtt_client
import time
from schema.aggregated_data_schema import AggregatedDataSchema
from file_datasource import FileDatasource
import config


def connect_mqtt(broker, port):
    print(f"CONNECT TO {broker}:{port}")

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print(f"Connected to MQTT Broker ({broker}:{port})!")
        else:
            print(f"Failed to connect {broker}:{port}, return code {rc}\n")
            exit(rc)

    client = mqtt_client.Client()
    client.on_connect = on_connect
    client.connect(broker, port)
    client.loop_start()
    return client


def publish(client, topic, datasource, delay):
    datasource.startReading()
    schema = AggregatedDataSchema()

    while True:
        time.sleep(delay)
        data = datasource.read()

        msg = schema.dumps(data)
        client.publish(topic, msg)

        client.publish(f"{topic}/accelerometer/x", str(data.accelerometer.x))
        client.publish(f"{topic}/accelerometer/y", str(data.accelerometer.y))
        client.publish(f"{topic}/accelerometer/z", str(data.accelerometer.z))

        client.publish(f"{topic}/gps/longitude", str(data.gps.longitude))
        client.publish(f"{topic}/gps/latitude", str(data.gps.latitude))
        
        client.publish(f"{topic}/parking/empty_count", str(data.parking.empty_count))
        client.publish(f"{topic}/parking/gps/longitude", str(data.parking.gps.longitude))
        client.publish(f"{topic}/parking/gps/latitude", str(data.parking.gps.latitude))

        client.publish(f"{topic}/time", data.time.isoformat())


def run():
    client = connect_mqtt(config.MQTT_BROKER_HOST, config.MQTT_BROKER_PORT)
    datasource = FileDatasource("data/accelerometer.csv", "data/gps.csv", "data/parking.csv")
    publish(client, config.MQTT_TOPIC, datasource, config.DELAY)


if __name__ == "__main__":
    run()