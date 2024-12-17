from pandas.core.api import DataFrame as DataFrame
from abstractStrategy import Strategy
import numpy as np
import pandas as pd


class BuyNHold(Strategy):
    def __init__(self, initial_balance, start, end):
        super().__init__(initial_balance, start, end)
        
    def generate_signals(self):
        # The Buy and Hold strategy takes a position from the start and holds it.
        self.data['position'] = 1  # Always in the market
        self.data['asset_returns'] = (self.data['close'] / self.data['open'] - 1).fillna(0)  # Asset return
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


class AFT01(Strategy):
    def __init__(self, initial_balance, start, end):
        super().__init__(initial_balance, start, end)

    def generate_signals(self):
        # Calculate EMAs
        self.data['EMA_200'] = self.data['close'].ewm(span=200, adjust=False).mean()
        self.data['EMA_50'] = self.data['close'].ewm(span=50, adjust=False).mean()

        # Hi-Lo Activator
        self.data['Avg_High'] = self.data['high'].rolling(window=3).mean()
        self.data['Avg_Low'] = self.data['low'].rolling(window=3).mean()
        self.data['HiLo_Activator'] = np.where(
            self.data['close'] > self.data['Avg_High'], 
            self.data['Avg_Low'], 
            self.data['Avg_High']
        )

        self.data['money_flow_multiplier'] = ((self.data['close'] - self.data['low']) - (self.data['high'] - self.data['close'])) / (self.data['high'] - self.data['low']).replace(0, float('nan'))
        self.data['money_flow_volume'] = self.data['money_flow_multiplier'] * self.data['volume']
        self.data['A/D'] = self.data['money_flow_volume'].cumsum()
        
        # Scoring system: currently using only EMA scores
        self.data['ema_score'] = np.where(
            (self.data['close'] > self.data['EMA_200']) & (self.data['close'] > self.data['EMA_50']), 
            1, -1
        )

        self.data['hilo_score'] = np.where(
            self.data['close'] > self.data['HiLo_Activator'], 1, -1)
        
        self.data['ad_score'] = np.where(
            self.data['A/D'] > 0, 1, -1
        )

        # Combine scores if desired
        # For now, just total_score = ema_score
        self.data['total_score'] = self.data['ema_score'] + self.data['hilo_score'] + self.data['ad_score']

        # Determine raw positions based on total_score
        self.data['position_raw'] = np.where(self.data['total_score'] > 0, 1, 
                                    np.where(self.data['total_score'] < 0, -1, 0))

        # Shift position by one day to avoid look-ahead bias
        self.data['position'] = self.data['position_raw'].shift(1).fillna(0)

        # Calculate returns as open-to-open returns for realism
        self.data['asset_returns'] = (self.data['open'].shift(-1) / self.data['open'] - 1).fillna(0)

        # Fee assumption: 0.1% each time a position changes (simple model)
        fee_rate = 0.001
        self.data['trade_flag'] = (self.data['position'].diff().abs() > 0).astype(int)

        # Adjust strategy returns
        self.data['strategy_returns'] = (self.data['asset_returns'] * self.data['position']) - (self.data['trade_flag'] * fee_rate)

        # Compute net worth over time
        self.data['net_worth'] = self.initial_balance * (1 + self.data['strategy_returns']).cumprod()

        return self.data

    def backtest(self, visualize=False):
        return super().backtest(visualize)
    
    def apply_strategy(self):
        data = self.generate_signals()
        
        next_position = data['position'].iloc[-1]
        position = self.wrapper.get_positions(
            category='linear', 
            symbol='BTCUSDT'
        ).get('balances')[0].get('wallet_balance')
        
        # Determine current position
        if position > 0:
            current_position = 1
        elif position == 0:
            current_position = 0
        else:
            current_position = -1
           
        # Execute trades if position needs to change
        if next_position != current_position:
            if next_position == 1:
                self.wrapper.place_spot_order('BTCUSDT', side='buy')
            elif next_position == -1:
                self.wrapper.place_spot_order('BTCUSDT', side='sell')
            else:  # next_position == 0
                if current_position > 0:
                    self.wrapper.place_spot_order('BTCUSDT', side='sell')
                elif current_position < 0:
                    self.wrapper.place_spot_order('BTCUSDT', side='buy')


class AlphaTraderLongBiased(Strategy):
    def __init__(self, initial_balance, start, end):
        super().__init__(initial_balance, start, end)

    def generate_signals(self):
        # Smooth the context
        self.data['context_long_ma'] = self.data['context'].rolling(window=4800, min_periods=1).mean()
        self.data['context_short_ma'] = self.data['context'].rolling(window=1200, min_periods=1).mean()

        # Define a simple rule:
        # If short_ma > long_ma by a certain margin, environment is "hotter"
        # If short_ma < long_ma by a certain margin, environment is "cooler"
        diff = self.data['context_short_ma'] - self.data['context_long_ma']

        def get_position(srs_val, diff_val):
            if srs_val > 0:
                # Bullish signal
                if diff_val < -0.1:
                    # short_ma < long_ma: conditions cooler
                    return 2.0  # more aggressive long
                elif diff_val < 0.15:
                    # mild difference: slightly heated
                    return 1.0
                else:
                    # big positive difference: overheated
                    return 0.0
            elif srs_val < 0:
                # Bearish signal
                if diff_val >= 0.3:
                    # significantly overheated
                    return -1.0
                elif diff_val > 0:
                    # slightly overheated
                    return 0.0
                else:
                    # not overheated, no short
                    return 0.0
            else:
                # srs == 0
                return 0.0

        self.data['position'] = self.data.apply(lambda row: get_position(row['srs'], diff.loc[row.name]), axis=1)

        self.data['asset_returns'] = (self.data['close'] / self.data['open'] - 1).fillna(0)
        self.data['strategy_returns'] = self.data['asset_returns'] * self.data['position']
        self.data['net_worth'] = self.initial_balance * (1 + self.data['strategy_returns']).cumprod()

        return self.data

    def backtest(self, visualize=False):
        return super().backtest(visualize)
    
    def apply_strategy(self):
        return super().apply_strategy()
    
class AlphaTraderLongBiased2(Strategy):
    def __init__(self, initial_balance, start, end):
        super().__init__(initial_balance, start, end)

    def generate_signals(self):
        # Shorten MA windows to increase sensitivity and frequency of trades
        self.data['context_long_ma'] = self.data['context'].rolling(window=2400, min_periods=1).mean()
        self.data['context_short_ma'] = self.data['context'].rolling(window=600, min_periods=1).mean()

        diff = self.data['context_short_ma'] - self.data['context_long_ma']

        # Add a price momentum indicator over a short term (e.g., 24 hours)
        self.data['price_momentum'] = (self.data['close'] / self.data['close'].shift(24) - 1).fillna(0)

        def get_position(srs_val, diff_val, price_mom):
            if srs_val > 0:
                # Bullish signal scenario, using increments of 0,0.5,1,2
                if diff_val < -0.05:
                    # Very cool environment -> max bullish = 2x long
                    return 2.0
                elif diff_val < 0.0:
                    # Slightly cool environment
                    # If momentum >0, stay more aggressive (1x), else maybe 0.5x
                    return 1.0 if price_mom > 0 else 0.5
                elif diff_val < 0.05:
                    # Near neutral environment
                    # If momentum positive, 1x long; if not, 0.5x
                    return 1.0 if price_mom > 0.02 else 0.5
                elif diff_val < 0.1:
                    # Slightly overheated
                    # Possibly remain long but lower exposure
                    return 0.5 if price_mom > 0.05 else 0.0
                else:
                    # Overheated environment
                    return 0.0
            elif srs_val < 0:
                # Bearish signal scenario, using increments of 0,-0.5,-1.0
                if diff_val > 0.2:
                    # Significantly overheated
                    # If momentum is negative, full -1.0, else -0.5
                    return -1.0 if price_mom < -0.02 else -0.5
                elif diff_val > 0.1:
                    # Slightly overheated
                    return -0.5
                else:
                    # Not overheated enough to short
                    return 0.0
            else:
                # srs == 0, neutral signal => no position
                return 0.0

        self.data['position'] = self.data.apply(
            lambda row: get_position(row['srs'], diff.loc[row.name], row['price_momentum']), axis=1
        )

        self.data['asset_returns'] = (self.data['close'] / self.data['open'] - 1).fillna(0)
        self.data['strategy_returns'] = self.data['asset_returns'] * self.data['position']
        self.data['net_worth'] = self.initial_balance * (1 + self.data['strategy_returns']).cumprod()

        return self.data

    def backtest(self, visualize=False):
        return super().backtest(visualize)
    
    def apply_strategy(self):
        return super().apply_strategy()
    


class AlphaTraderOne(Strategy):
    def __init__(self, initial_balance, start, end):
        super().__init__(initial_balance, start, end)


    def compute_confidence_gauge(self):
        # 1. RSI Calculation
        delta = self.data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        self.data['rsi'] = 100 - (100/(1 + (gain/loss)))
        
        # Normalize RSI: Map [30,70] to [0,1], clamp outside values
        self.data['rsi_norm'] = ((self.data['rsi'] - 30) / (70 - 30)).clip(0,1)

        # 2. ATR-based Volatility
        high_low = self.data['high'] - self.data['low']
        high_close = (self.data['high'] - self.data['close'].shift(1)).abs()
        low_close = (self.data['low'] - self.data['close'].shift(1)).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        self.data['ATR'] = tr.rolling(window=14).mean()

        # Normalize ATR: Smaller ATR -> higher confidence
        atr_min = self.data['ATR'].rolling(window=200, min_periods=20).min()
        atr_max = self.data['ATR'].rolling(window=200, min_periods=20).max()
        self.data['atr_norm'] = 1 - ((self.data['ATR'] - atr_min) / (atr_max - atr_min)).clip(0,1)
        self.data['atr_norm'] = self.data['atr_norm'].fillna(0.5)  # fallback if insufficient data

        # Combine indicators into confidence score
        self.data['confidence_score'] = (self.data['rsi_norm'] + self.data['atr_norm']) / 2

    def generate_signals(self):
        # Compute confidence gauge
        self.compute_confidence_gauge()

        # Set base positions from logic:
        # SRS > 0 + context=1 => long base (1x)
        # SRS < 0 + context=1 => cash (0x)
        # SRS > 0 + context=0 => cash (0x)
        # SRS < 0 + context=0 => short base (1x)
        self.data['base_position'] = np.where(
            (self.data['srs'] > 0) & (self.data['context'] == 1), 1,
            np.where((self.data['srs'] < 0) & (self.data['context'] == 0), -1, 0)
        )

        # Confidence threshold
        high_conf_threshold = 0.6

        # Initialize final_position as a copy of base_position
        self.data['final_position'] = self.data['base_position'].copy()

        # Condition 1: srs>0, context=1 (base long)
        cond1 = (self.data['srs'] > 0) & (self.data['context'] == 1)
        cond1_conf = self.data.loc[cond1, 'confidence_score'] > high_conf_threshold
        self.data.loc[cond1, 'final_position'] = np.where(cond1_conf, 2.0, 1.0)

        # Condition 2: srs<0, context=1 => always 0x
        cond2 = (self.data['srs'] < 0) & (self.data['context'] == 1)
        # No np.where needed, just assign 0:
        self.data.loc[cond2, 'final_position'] = 0.0

        # Condition 3: srs>0, context=0 => base cash
        # If high confidence => 1x long, else 0x
        cond3 = (self.data['srs'] > 0) & (self.data['context'] == 0)
        cond3_conf = self.data.loc[cond3, 'confidence_score'] > high_conf_threshold
        self.data.loc[cond3, 'final_position'] = np.where(cond3_conf, 1.0, 0.0)

        # Condition 4: srs<0, context=0 => base long (1x)
        # If high confidence => 2x, else 1x
        cond4 = (self.data['srs'] < 0) & (self.data['context'] == 0)
        cond4_conf = self.data.loc[cond4, 'confidence_score'] > high_conf_threshold
        self.data.loc[cond4, 'final_position'] = np.where(cond4_conf, 2.0, 1.0)

        # Shift positions by one bar to avoid look-ahead bias
        self.data['position'] = self.data['final_position'].shift(1).fillna(0)

        # Compute returns (open-to-open)
        self.data['asset_returns'] = (self.data['open'].shift(-1) / self.data['open'] - 1).fillna(0)

        # Trade flag for fees
        self.data['trade_flag'] = (self.data['position'].diff().abs() > 0).astype(int)

        # Fee of 0.1% per position change
        fee_rate = 0.001
        self.data['strategy_returns'] = (self.data['asset_returns'] * self.data['position']) - (self.data['trade_flag'] * fee_rate)

        # Net worth calculation
        self.data['net_worth'] = self.initial_balance * (1 + self.data['strategy_returns']).cumprod()

        return self.data
    
    def backtest(self, visualize=False):
        return super().backtest(visualize)
    
    def apply_strategy(self):
        return super().apply_strategy()

