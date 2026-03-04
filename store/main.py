import datetime
import json
from typing import Set, List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, field_validator
from sqlalchemy import Column, DateTime, Float, Integer, MetaData, String, Table, create_engine, insert, select
from config import POSTGRES_DB, POSTGRES_HOST, POSTGRES_PASSWORD, POSTGRES_PORT, POSTGRES_USER

# SQLAlchemy setup
DATABASE_URL = f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
engine = create_engine(DATABASE_URL)
metadata = MetaData()

# Define the ProcessedAgentData table
processed_agent_data = Table(
    "processed_agent_data",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("road_state", String),
    Column("x", Float),
    Column("y", Float),
    Column("z", Float),
    Column("latitude", Float),
    Column("longitude", Float),
    Column("timestamp", DateTime),
)


# FastAPI models
class AccelerometerData(BaseModel):
    x: float
    y: float
    z: float


class GpsData(BaseModel):
    latitude: float
    longitude: float


class AgentData(BaseModel):
    accelerometer: AccelerometerData
    gps: GpsData
    timestamp: datetime.datetime

    @field_validator('timestamp', mode='before')
    @classmethod
    def check_timestamp(cls, value):
        if isinstance(value, datetime.datetime):
            return value
        try:
            # Обробка формату ISO з символом Z або без
            return datetime.datetime.fromisoformat(value.replace("Z", ""))
        except (TypeError, ValueError):
            raise ValueError("Invalid timestamp format. Expected ISO 8601 format.")


class ProcessedAgentData(BaseModel):
    road_state: str
    agent_data: AgentData


# Database model for response
class ProcessedAgentDataInDB(BaseModel):
    id: int
    road_state: str
    x: float
    y: float
    z: float
    latitude: float
    longitude: float
    timestamp: datetime.datetime


# FastAPI app setup
app = FastAPI()

# WebSocket subscriptions
subscriptions: Set[WebSocket] = set()


@app.websocket("/ws/")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    subscriptions.add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        subscriptions.remove(websocket)


async def send_data_to_subscribers(data: List[ProcessedAgentDataInDB]):
    for websocket in subscriptions:
        json_data = [item.model_dump_json() for item in data]
        await websocket.send_text(json.dumps(json_data))


# FastAPI CRUDL endpoints
@app.post("/processed_agent_data/")
async def create_processed_agent_data(data: List[ProcessedAgentData]):
    inserted_data = []
    with engine.connect() as connection:
        for item in data:

            stmt = insert(processed_agent_data).values(
                road_state=item.road_state,
                x=item.agent_data.accelerometer.x,
                y=item.agent_data.accelerometer.y,
                z=item.agent_data.accelerometer.z,
                latitude=item.agent_data.gps.latitude,
                longitude=item.agent_data.gps.longitude,
                timestamp=item.agent_data.timestamp
            ).returning(processed_agent_data)

            result = connection.execute(stmt)
            row = result.fetchone()
            inserted_data.append(ProcessedAgentDataInDB(
                id=row[0],
                road_state=row[1],
                x=row[2],
                y=row[3],
                z=row[4],
                latitude=row[5],
                longitude=row[6],
                timestamp=row[7]
            ))
        connection.commit()


    await send_data_to_subscribers(inserted_data)
    return {"status": "ok", "count": len(inserted_data)}


@app.get("/processed_agent_data/{processed_agent_data_id}", response_model=ProcessedAgentDataInDB)
def read_processed_agent_data(processed_agent_data_id: int):
    with engine.connect() as connection:
        query = select(processed_agent_data).where(processed_agent_data.c.id == processed_agent_data_id)
        result = connection.execute(query).fetchone()
        if result:
            return ProcessedAgentDataInDB(
                id=result[0], road_state=result[1], x=result[2], y=result[3],
                z=result[4], latitude=result[5], longitude=result[6], timestamp=result[7]
            )
    return {"error": "Not found"}


@app.get("/processed_agent_data/", response_model=List[ProcessedAgentDataInDB])
def list_processed_agent_data():
    res = []
    with engine.connect() as connection:
        query = select(processed_agent_data)
        rows = connection.execute(query).fetchall()
        for row in rows:
            res.append(ProcessedAgentDataInDB(
                id=row[0], road_state=row[1], x=row[2], y=row[3],
                z=row[4], latitude=row[5], longitude=row[6], timestamp=row[7]
            ))
    return res


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)