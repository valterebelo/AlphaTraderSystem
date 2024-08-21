from pandas.core.api import DataFrame as DataFrame
from abstractStrategy import Strategy
import numpy as np


class BuyNHold(Strategy):
    def __init__(self, initial_balance, start, end):
        super().__init__(initial_balance, start, end)
        
    def generate_signals(self):
        # The Buy and Hold strategy takes a position from the start and holds it.
        self.data['position'] = 1  # Always in the market
        self.data['asset_returns'] = (self.data['close'] / self.data['close'].shift(1) - 1).fillna(0)  # Asset return
        self.data['strategy_returns'] = self.data['asset_returns']  # Strategy returns are the same as asset returns for Buy & Hold
        self.data['net_worth'] = self.initial_balance * (1 + self.data['strategy_returns']).cumprod()
        return self.data
    
    def backtest(self, visualize = False):
        data = self.generate_signals()
        return super().backtest(visualize=visualize)
    
    def apply_strategy(self):
        data = self.generate_signals()

        next_position = data['position'].iloc[-1]

        position = self.wrapper.get_positions(category='linear', symbol='BTCUSDT').get('balances')[0].get('wallet_balance')
        
        if position > 0:
            current_position = 1
        elif position == 0:
            current_position = 0
        else:
            current_position = -1
           
        if next_position != current_position:
            if next_position == 1:
                self.wrapper.place_spot_order('BTCUSDT', side='buy')
            elif next_position == 0:
                pass
            else: 
                self.wrapper.place_spot_order('BTCUSDT', side='sell')

        

class AlphaTraderLongBiased(Strategy):
    def __init__(self, initial_balance, start, end):
        super().__init__(initial_balance, start, end)

    def generate_signals(self):

        self.data['position'] = np.where(
            (self.data['srs'] > 0) & (self.data['context'] == 0), 1, 
            np.where(
                (self.data['srs'] > 0) & (self.data['context'] == 1), 1, 0
            )
        )

        self.data['asset_returns'] = (self.data['close'] / self.data['close'].shift(1) - 1).fillna(0)  # Asset return
        self.data['strategy_returns'] = self.data['asset_returns'] * self.data['position'] 
        self.data['net_worth'] = self.initial_balance * (1 + self.data['strategy_returns']).cumprod()

        return self.data

    def backtest(self, visualize=False):
        return super().backtest(visualize)
    
    def apply_strategy(self):
        return super().apply_strategy()
    




class AlphaTraderAI(Strategy): 
    def __init__(self, initial_balance, start, end):
        super().__init__(initial_balance, start, end)
    pass 

