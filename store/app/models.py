from datetime import datetime
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from sqlalchemy import (
    create_engine, MetaData, Table, Column, Integer, String, Float, DateTime
)
from sqlalchemy.sql import select
from .config import DATABASE_URL

engine = create_engine(DATABASE_URL, echo=False)
metadata = MetaData()

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

def create_tables():
    metadata.create_all(engine)

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
    timestamp: datetime

    @validator('timestamp', pre=True)
    def check_timestamp(cls, v):
        if isinstance(v, datetime):
            return v
        try:
            return datetime.fromisoformat(v)
        except Exception:
            raise ValueError("Invalid timestamp format. Expected ISO 8601.")

class ProcessedAgentData(BaseModel):
    road_state: str
    agent_data: AgentData

class ProcessedAgentDataInDB(BaseModel):
    id: int
    road_state: str
    x: float
    y: float
    z: float
    latitude: float
    longitude: float
    timestamp: datetime