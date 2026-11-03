import json
import pandas as pd
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request
import asyncio
import logging
from app.core.angel_one_client import AngelOneClient
from app.core.strategy_engine import StrategyEngine
from app.core.archetype_evaluator import ArchetypeEvaluator

app = FastAPI()
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()
angel_client = AngelOneClient()
strategy_engine = StrategyEngine()
archetype_evaluator = ArchetypeEvaluator(strategy_engine)

@app.on_event("startup")
async def startup_event():
    # Attempt login to Angel One on startup
    success = angel_client.login()
    if not success:
        logger.warning("Failed to login to Angel One on startup. Check credentials in .env file.")
    else:
        logger.info("Successfully connected to Angel One on startup.")
        # Setup websocket stream for some major tokens (e.g. NIFTY 50 dummy tokens for structure)
        angel_client.setup_websocket(
            token_list=[{"exchangeType": 1, "tokens": ["2885"]}], # Example token for Reliance
            on_data_callback=handle_market_data
        )
        angel_client.start_websocket()

def handle_market_data(message):
    """
    Callback for live tick data.
    In a fully functional bot, we aggregate ticks to OHLCV candles here,
    evaluate archetypes, and send signals.
    """
    logger.debug(f"Received market data: {message}")
    # Example parsing logic will go here
    # df_1m, df_5m, df_15m = aggregate_candles(message)
    # signals = archetype_evaluator.evaluate_archetypes(df_15m, df_5m, df_1m)
    # if signals:
    #     for sig in signals:
    #         asyncio.create_task(manager.broadcast(json.dumps(sig)))

@app.get("/", response_class=HTMLResponse)
async def get(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
