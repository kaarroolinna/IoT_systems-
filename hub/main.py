import logging
from typing import List
from fastapi import FastAPI
from redis import Redis
import paho.mqtt.client as mqtt
from app.adapters.store_api_adapter import StoreApiAdapter
from app.entities.processed_agent_data import ProcessedAgentData
from config import (
    STORE_API_BASE_URL, REDIS_HOST, REDIS_PORT, BATCH_SIZE,
    MQTT_TOPIC, MQTT_BROKER_HOST, MQTT_BROKER_PORT,
)

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [%(module)s] %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("app.log")],
)

redis_client = Redis(host=REDIS_HOST, port=REDIS_PORT)
store_adapter = StoreApiAdapter(api_base_url=STORE_API_BASE_URL)
app = FastAPI()


@app.post("/processed_agent_data/")
async def save_processed_agent_data(processed_agent_data: ProcessedAgentData):
    redis_client.lpush("processed_agent_data", processed_agent_data.model_dump_json())
    if redis_client.llen("processed_agent_data") >= BATCH_SIZE:
        batch = []
        for _ in range(BATCH_SIZE):
            raw_data = redis_client.lpop("processed_agent_data")
            if raw_data:
                batch.append(ProcessedAgentData.model_validate_json(raw_data))
        store_adapter.save_data(processed_agent_data_batch=batch)
    return {"status": "ok"}


def on_message(client, userdata, msg):
    try:
        payload: str = msg.payload.decode("utf-8")
        processed_agent_data = ProcessedAgentData.model_validate_json(payload, strict=True)

        redis_client.lpush("processed_agent_data", processed_agent_data.model_dump_json())

        if redis_client.llen("processed_agent_data") >= BATCH_SIZE:
            batch = []
            for _ in range(BATCH_SIZE):
                raw_data = redis_client.lpop("processed_agent_data")
                if raw_data:
                    batch.append(ProcessedAgentData.model_validate_json(raw_data))

            if batch:
                store_adapter.save_data(processed_agent_data_batch=batch)
    except Exception as e:
        logging.error(f"Error processing MQTT message: {e}")


client = mqtt.Client()
client.on_connect = lambda c, u, f, rc: (logging.info("Connected to MQTT"),
                                         c.subscribe(MQTT_TOPIC)) if rc == 0 else None
client.on_message = on_message
client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT)
client.loop_start()