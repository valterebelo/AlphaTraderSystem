import importlib
from pybit.unified_trading import HTTP
import os
from utils import utils
importlib.reload(utils)
from datetime import datetime

class BybitWrapper():

    def __init__(self, demo=False, api_key=None, api_secret=None):
        print(f'Wrapper Activated. Demo Mode == {demo}')
        self.demo = demo
        
        if self.demo:   
            self.api_key = api_key or os.getenv("BYBIT_API_KEY_TEST")
            self.api_secret = api_secret or os.getenv("BYBIT_API_SECRET_TEST")
            self.session = HTTP(api_key=self.api_key, api_secret=self.api_secret, demo=demo, log_requests=True)
        else:
            self.api_key = api_key or os.getenv("BYBIT_API_KEY")
            self.api_secret = api_secret or os.getenv("BYBIT_API_SECRET")
            self.session = HTTP(api_key=self.api_key, api_secret=self.api_secret, demo=demo, log_requests=True)
        

    ###########################################################################
    ##########################  Account Data   ################################
    ########################################################################### 

    def transaction_log(self, account_type='UNIFIED', market=None, coin=None):
        
        response = self.session.get_transaction_log(accountType=account_type,category=market,currency=coin)

        return utils.parse_transaction_log(response)


    def wallet_balance(self, account_type: str, coin: str):
        
        response = self.session.get_wallet_balance(accountType=account_type, coin=coin)
        
        return utils.parse_wallet_balance(response)
    
    def get_coin_balance(self, account_type: str = 'UNIFIED', coin: str = None, member_id: str = None, with_bonus: int = 0):
        
        if self.demo:
            raise RuntimeError("This operation is not allowed in demo mode.")
        else:
            response = self.session.get_coins_balance(
                accountType=account_type,
                coin=coin,
                memberId=member_id,
                withBonus=with_bonus
            )
            return utils.parse_coin_balance(response=response)
    
    def get_api_details(self):
        if self.demo:
            raise RuntimeError("This operation is not allowed in demo mode.")
        else:
            response=self.session.get_api_key_information()
            return response
        
    ###########################################################################
    ##########################  Market Data   #################################
    ###########################################################################    
    

    # Market Data Endpoints (Common for Spot and Perpetual)
    def get_orderbook(self, ticker: str, category: str, limit: int = 100):
        response=self.session.get_orderbook(category=category, symbol=ticker, limit=limit)
        return utils.parse_orderbook(response=response)
    
    def get_candles(self, market, ticker, interval: str = "60", limit: int = 10):
        response=self.session.get_kline(category=market, symbol=ticker, interval=interval, limit=limit)
        return utils.parse_klines(response)


    ###########################################################################
    ##########################  Spot Order Management   #######################
    ###########################################################################


    def build_market_order_payload(self,
                                ticker: str, 
                                side: str, 
                                qty: float, 
                                execution_type: str = 'GTC', 
                                annotations: str = None) -> dict:
        """
        Builds the payload for a market order on the spot market.

        :param ticker: The trading pair symbol (e.g., 'BTCUSDT').
        :param side: The side of the order ('Buy' or 'Sell').
        :param qty: The quantity of the asset to buy or sell.
        :param execution_type: The order execution type ('GTC', 'IOC', etc.). Defaults to 'GTC'.
        :param annotations: Optional annotations for the order.
        :return: A dictionary payload for the order.
        """

        # Validate side parameter
        if side not in ['Buy', 'Sell']:
            raise ValueError("Invalid side, must be 'Buy' or 'Sell'.")

        # Validate execution_type parameter
        valid_execution_types = ['GTC', 'IOC', 'FOK']
        if execution_type not in valid_execution_types:
            raise ValueError(f"Invalid execution_type, must be one of {valid_execution_types}.")

        # Automate annotations if not provided
        if annotations is None:
            current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            annotations = f"{side}_{qty}_{ticker}_{current_time}"

        payload = {
            "category": "spot",
            "symbol": ticker,
            "side": side,
            "orderType": "Market",
            "qty": qty,
            "timeInForce": execution_type,
            "orderLinkId": annotations,
            "isLeverage": 0,
            "orderFilter": "Order"
        }

        return payload

    # Spot Market Endpoints
    def place_spot_market_order(self, payload: dict):
        """
        Places a market order on the spot market using a pre-built payload.

        :param payload: A dictionary containing the order details.
        :return: The API response from placing the order.
        """
        try:
            response = self.session.place_order(**payload)
            
        except Exception as e:
            print(f"Error placing order: {e}")
            return None

        return response
    
    def cancel_spot_order(self, symbol: str, order_id: str):
        pass

    def spot_order_history(self, market: str = 'spot', ticker='BTCUSDT', limit: int = 100):
        
        
        response = self.session.get_order_history(category=market, 
                                                  symbol=ticker,
                                                  limit=limit
                                                  )
        
        
        return utils.parse_order_history(response)
    

    ###########################################################################
    ####################  Derivatives Position Management   ###################
    ########################################################################### 

    def get_positions(self, market: str, ticker: str, settleCoin: str = None, limit: int = 20, cursor: str = None):
        response = self.session.get_positions(
            category=market,
            symbol=ticker,
            settleCoin=settleCoin,
            limit=limit,
            cursor=cursor
        )

        return utils.parse_positions(response)

    def place_perp_order(self, symbol: str, side: str, order_type: str, qty: float, price: float = None, reduce_only: bool = False):
        pass
    
    def cancel_perp_order(self, symbol: str, order_id: str):
        pass
    
    def get_perp_balance(self, coin: str = "USDT"):
        pass
    
    def get_perp_positions(self, symbol: str):
        pass
    
    def get_perp_order_history(self, symbol: str, start_time: int = None, end_time: int = None, limit: int = 50):
        pass