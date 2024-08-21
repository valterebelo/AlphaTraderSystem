from abc import ABC, abstractmethod
from tradingPerformance import PerformanceEstimator
from dataManager import DataManager
import pandas as pd 
from executionEngine import BybitWrapper
from datetime import datetime, timezone


class Strategy(ABC):
    
    @abstractmethod
    def __init__(self, initial_balance, start, end, demo=True, contextualize=True):
        self.data_manager = DataManager()
        self.initial_balance = initial_balance
        if end == 'now':
            end = datetime.today().astimezone(timezone.utc).strftime('%Y-%m-%d')

        self.data = self.data_manager.get_data(start=start, end=end, contextualize=contextualize)
        self.wrapper = BybitWrapper(demo=demo)
        self.data['net_worth'] = self.initial_balance
    
    @abstractmethod
    def generate_signals(self) -> pd.DataFrame:
        pass
    
    def backtest(self, visualize=False):
        data = self.generate_signals()
        self.backtester = PerformanceEstimator(tradingData=data, visualize=visualize)
        self.backtester.displayPerformance()
    
    @abstractmethod
    def apply_strategy(self): 
        pass 
