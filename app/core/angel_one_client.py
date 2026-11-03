import os
import time
import pyotp
import logging
from SmartApi import SmartConnect
from SmartApi.smartWebSocketV2 import SmartWebSocketV2
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AngelOneClient:
    def __init__(self):
        self.api_key = os.getenv("ANGEL_API_KEY")
        self.client_code = os.getenv("ANGEL_CLIENT_CODE")
        self.password = os.getenv("ANGEL_PASSWORD")
        self.totp_secret = os.getenv("ANGEL_TOTP_SECRET")
        self.smart_api = SmartConnect(api_key=self.api_key)
        self.auth_token = None
        self.feed_token = None
        self.refresh_token = None
        self.ws = None

    def login(self):
        try:
            totp = pyotp.TOTP(self.totp_secret).now()
            data = self.smart_api.generateSession(self.client_code, self.password, totp)

            if data['status'] == False:
                logger.error(f"Login failed: {data['message']}")
                return False

            self.auth_token = data['data']['jwtToken']
            self.refresh_token = data['data']['refreshToken']
            self.feed_token = self.smart_api.getfeedToken()
            logger.info("Successfully logged in to Angel One SmartAPI")
            return True
        except Exception as e:
            logger.error(f"Error during login: {str(e)}")
            return False

    def fetch_gainers_losers(self):
        # Approximating a market scanner
        # In a real scenario, we would use an Angel One API endpoint for top gainers/losers or specific indices
        pass

    def setup_websocket(self, token_list, on_data_callback):
        if not self.feed_token:
            logger.error("Feed token not available. Please login first.")
            return

        correlation_id = "test_123"
        action = 1 # Subscribe
        mode = 3 # Mode 3 includes full snap quote / 1min OHLCV equivalent details

        self.ws = SmartWebSocketV2(self.auth_token, self.api_key, self.client_code, self.feed_token)

        def on_data(wsapp, message):
            on_data_callback(message)

        def on_open(wsapp):
            logger.info("WebSocket connected")
            self.ws.subscribe(correlation_id, mode, token_list)

        def on_error(wsapp, error):
            logger.error(f"WebSocket Error: {error}")

        def on_close(wsapp):
            logger.info("WebSocket closed")

        self.ws.on_open = on_open
        self.ws.on_data = on_data
        self.ws.on_error = on_error
        self.ws.on_close = on_close

    def start_websocket(self):
        if self.ws:
            self.ws.connect()

    def get_historical_data(self, exchange, symboltoken, interval, fromdate, todate):
        try:
            historicParam = {
                "exchange": exchange,
                "symboltoken": symboltoken,
                "interval": interval,
                "fromdate": fromdate,
                "todate": todate
            }
            res = self.smart_api.getCandleData(historicParam)
            if res and res.get('status'):
                return res.get('data')
            return []
        except Exception as e:
            logger.error(f"Error fetching historical data: {str(e)}")
            return []

if __name__ == '__main__':
    # Test stub
    client = AngelOneClient()
    print("AngelOneClient instantiated successfully")
