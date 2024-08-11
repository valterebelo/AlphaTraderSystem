from abstractStrategy import Strategy


class BuyNHold(Strategy):
    def __init__(self, initial_balance, start, end):
        super().__init__(initial_balance, start, end)
        

    def generate_signals(self):
          
        self.data['position'] = 1
        self.data['daily_return'] = self.data['close'] / self.data['close'].shift(1) - 1 
        self.data['net_worth'] *= (1 + self.data['daily_return']).cumprod() 
        self.data['daily_return'].iloc[0] = 0  
  
        return self.data
    
    def backtest(self):
        data = self.generate_signals()
        return super().backtest(data)
    
    def execute_strategy(self):
        
        data = self.generate_signals()

        next_position = data['position'].iloc[-1]

        position = self.wrapper.get_positions(category='linear',
                                                      symbol='BTCUSDT'
                                                      ).get('balances')[0].get('wallet_balance')
        
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

        
                
     

class AlphaTraderOne(Strategy):
    def __init__(self, initial_balance, start, end):
        super().__init__(initial_balance, start, end)
    pass 

class AlphaTraderAI(Strategy): 
    def __init__(self, initial_balance, start, end):
        super().__init__(initial_balance, start, end)
    pass 

