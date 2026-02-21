import json
from typing import List, Set
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import insert, select, update, delete
from sqlalchemy.exc import SQLAlchemyError
from .models import (
    engine, processed_agent_data, create_tables,
    ProcessedAgentData, ProcessedAgentDataInDB
)
from .config import DATABASE_URL

app = FastAPI(title="Store API - Road Vision")

create_tables()

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

async def send_data_to_subscribers(data):
    dead = []
    for ws in list(subscriptions):
        try:
            await ws.send_json(data)
        except Exception:
            dead.append(ws)
    for d in dead:
        subscriptions.discard(d)

@app.post("/processed_agent_data/", response_model=List[ProcessedAgentDataInDB])
async def create_processed_agent_data(data: List[ProcessedAgentData]):
    conn = engine.connect()
    inserted_rows = []
    trans = conn.begin()
    try:
        for item in data:
            agent = item.agent_data
            stmt = insert(processed_agent_data).values(
                road_state=item.road_state,
                x=agent.accelerometer.x,
                y=agent.accelerometer.y,
                z=agent.accelerometer.z,
                latitude=agent.gps.latitude,
                longitude=agent.gps.longitude,
                timestamp=agent.timestamp
            ).returning(processed_agent_data)
            res = conn.execute(stmt)
            row = res.fetchone()
            inserted_rows.append(dict(row._mapping))
        trans.commit()
        await send_data_to_subscribers({"type": "new_batch", "count": len(inserted_rows), "items": inserted_rows})
        return inserted_rows
    except SQLAlchemyError as e:
        trans.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/processed_agent_data/{processed_agent_data_id}", response_model=ProcessedAgentDataInDB)
def read_processed_agent_data(processed_agent_data_id: int):
    conn = engine.connect()
    try:
        stmt = select(processed_agent_data).where(processed_agent_data.c.id == processed_agent_data_id)
        res = conn.execute(stmt).fetchone()
        if not res:
            raise HTTPException(status_code=404, detail="Not found")
        return dict(res._mapping)
    finally:
        conn.close()

@app.get("/processed_agent_data/", response_model=List[ProcessedAgentDataInDB])
def list_processed_agent_data():
    conn = engine.connect()
    try:
        stmt = select(processed_agent_data).order_by(processed_agent_data.c.id)
        res = conn.execute(stmt).fetchall()
        return [dict(r._mapping) for r in res]
    finally:
        conn.close()

@app.put("/processed_agent_data/{processed_agent_data_id}", response_model=ProcessedAgentDataInDB)
def update_processed_agent_data(processed_agent_data_id: int, data: ProcessedAgentData):
    conn = engine.connect()
    trans = conn.begin()
    try:
        agent = data.agent_data
        stmt = (
            update(processed_agent_data)
            .where(processed_agent_data.c.id == processed_agent_data_id)
            .values(
                road_state=data.road_state,
                x=agent.accelerometer.x,
                y=agent.accelerometer.y,
                z=agent.accelerometer.z,
                latitude=agent.gps.latitude,
                longitude=agent.gps.longitude,
                timestamp=agent.timestamp
            )
            .returning(processed_agent_data)
        )
        res = conn.execute(stmt).fetchone()
        if not res:
            trans.rollback()
            raise HTTPException(status_code=404, detail="Not found")
        trans.commit()
        return dict(res._mapping)
    except SQLAlchemyError as e:
        trans.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.delete("/processed_agent_data/{processed_agent_data_id}", response_model=ProcessedAgentDataInDB)
def delete_processed_agent_data(processed_agent_data_id: int):
    conn = engine.connect()
    trans = conn.begin()
    try:
        stmt = delete(processed_agent_data).where(processed_agent_data.c.id == processed_agent_data_id).returning(processed_agent_data)
        res = conn.execute(stmt).fetchone()
        if not res:
            trans.rollback()
            raise HTTPException(status_code=404, detail="Not found")
        trans.commit()
        return dict(res._mapping)
    except SQLAlchemyError as e:
        trans.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)