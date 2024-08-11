from abc import ABC, abstractmethod
from tradingPerformance import PerformanceEstimator
from dataManager import DataManager
import pandas as pd 
from executionEngine import BybitWrapper
from datetime import datetime, timezone



class Strategy(ABC):
    
    @abstractmethod
    def __init__(self, initial_balance, start, end, contextualize=True):
        self.data_manager = DataManager()
        self.backtester = PerformanceEstimator()
        self.initial_balance = initial_balance
        if end == 'now':
            end = datetime.today().astimezone(timezone.utc).strftime('%Y-%m-%d')

        self.data = self.data_manager(start=start, end=end, 
                                      contextualize=contextualize)
        

        self.wrapper = BybitWrapper()
        self.data['net_worth'] = self.initial_balance
    
    @abstractmethod
    def generate_signals(self) -> pd.DataFrame:
        pass
    
    @abstractmethod
    def backtest(self, data): 
        self.backtester.displayPerformance(data=data)

    @abstractmethod
    def apply_strategy(self): 
        pass 

