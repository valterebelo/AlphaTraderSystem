"""
Projeto: AlfaTrader AI
Objetivo: Implementação de um ambiente de trading onde o agente toma decisões e obtém feedback.
Autor: Valter Rebelo

"""

###############################################################################
############################## Imports ########################################
###############################################################################


import matplotlib.pyplot as plt
from dataManager import DataManager
import numpy as np

###############################################################################
############################## Class TradingEnv ###############################
###############################################################################

class TradingEnvironment():

    def __init__(self, start, end, cash, contextualize=True, stateSize=30, txCosts=0.01):
        
        data_manager = DataManager()
        
        self.data = data_manager.get_data(start=start, end=end, contextualize=contextualize)
        self.data['position'] = 0
        self.data['action'] = 0
        self.data['nav'] = 0.
        self.data['cash'] = float(cash)
        self.data['net_worth'] = self.data['nav'] + self.data['cash']
        self.data['returns'] = 0.

        self.state = self._get_state()

        self.reward = 0.
        self.done = 0
        self.start = start
        self.end = end
        self.current_step = stateSize
        self.quantity = 0
        self.txCosts = txCosts
        
    def reset(self, contextualize):
        """
        Resets the environment to start a new episode after the previous trade is closed.
        """
        # Advance to the next potential trading action if the current episode ended with a closed trade
        if self.done:
            self.current_step += 1  # Move to the next step after a trade has closed

        # Check if we've reached the end of the data
        if self.current_step >= len(self.data):
            self.done = True  # No more data to process, end of data
            return None  # No more states to return, end of episodes

        # Reset the state variables for the new episode
        self.data['position'][self.current_step:] = 0
        self.data['action'][self.current_step:] = 0
        self.data['nav'][self.current_step:] = 0.
        self.data['cash'][self.current_step:] = self.data['cash'][self.current_step - 1]  # Presume continuity unless specified otherwise
        self.data['net_worth'][self.current_step:] = self.data['nav'][self.current_step] + self.data['cash'][self.current_step]
        self.data['returns'][self.current_step:] = 0.

        self.reward = 0
        self.done = False
        self.quantity = 0

        # Update the state from the new current step
        self.state = self._get_state(contextualize=contextualize)  # Assuming you want to contextualize by default
        return self.state

    def _get_state(self, contextualize):
        # List of columns to include in the state vector; this should be defined based on what you consider relevant
        relevant_columns_contextualized = ['close', 'open', 'high', 'low', 'volume', 'srs', 'hash_ribbon', 'cvd_ema24']
        
        relevant_columns_uncontextualized = ['close', 'open', 'high', 'low', 'volume', 'srs', 'hash_ribbon',
                                             '28d_market_gradient', 'mayer_multiple', 'profit_relative', 'cvd_ema24']
        if contextualize:
            state_columns = [col for col in self.data.columns if col in relevant_columns_contextualized]
        else:
            state_columns = relevant_columns_uncontextualized  # If not contextualizing, use the pre-defined relevant columns directly

        # Ensure the state includes enough historical data points
        start_index = max(0, self.current_step - self.stateSize)
        state = self.data[state_columns].iloc[start_index:self.current_step].values.flatten()
        return state.astype(float)


    def step(self, action, contextualize):
        """
        Realiza um passo no ambiente de trading baseado na ação fornecida.

        PARÂMETROS:
        - action: Ação tomada pelo agente, onde 0 é hold/cash, 1 é buy/long e -1 é short/sell.

        RETORNOS:
        - state: Novo estado do ambiente.
        - reward: Recompensa obtida com a ação.
        - done: Indica se o episódio terminou.
        - info: Dicionário com informações adicionais.
        """

        current_price = self.data['close'].iloc[self.current_step]
        market_context = self.data['context'].iloc[self.current_step] if self.contextualize else None

        previous_position = self.data['position'].iloc[self.current_step - 1]
        previous_cash = self.data['cash'].iloc[self.current_step - 1]
        previous_net_worth = self.data['net_worth'].iloc[self.current_step - 1]
        entry_price = self.data['entry_price'].iloc[self.current_step] if previous_position != 0 else current_price
        transaction_cost_rate = self.txCosts

        new_position = previous_position
        new_cash = previous_cash
        transaction_cost = 0

        self.data.at[self.current_step, 'action'] = action

        # Define transaction cost function
        def calculate_transaction_cost(price, quantity):
            return price * quantity * transaction_cost_rate

        if contextualize:
            if market_context == 1:  # Bull market
                if action == 1:  # Buy or cover short (moving to neutral)
                    if previous_position <= 0:
                        self.quantity = previous_cash / (current_price * (1 + transaction_cost_rate))
                        transaction_cost = calculate_transaction_cost(current_price, self.quantity)
                        new_cash = previous_cash - current_price * self.quantity - transaction_cost
                        new_position = 1 if previous_position == 0 else 0
                        self.data.at[self.current_step, 'entry_price'] = current_price

                elif action == -1 and previous_position == 1:  # Sell from long (moving to neutral)
                    transaction_cost = calculate_transaction_cost(current_price, self.quantity)
                    new_cash = previous_cash + current_price * self.quantity - transaction_cost
                    self.quantity = 0
                    new_position = 0

            elif market_context == 0:  # Bear market
                if action == 1 and previous_position == -1:  # Cover short (moving to neutral)
                    transaction_cost = calculate_transaction_cost(current_price, self.quantity)
                    new_cash = previous_cash + current_price * self.quantity - transaction_cost
                    self.quantity = 0
                    new_position = 0

                elif action == -1:  # Go short or stay neutral
                    if previous_position >= 0:
                        self.quantity = previous_cash / (current_price * (1 + transaction_cost_rate))
                        transaction_cost = calculate_transaction_cost(current_price, self.quantity)
                        new_cash = previous_cash - current_price * self.quantity - transaction_cost
                        new_position = -1 if previous_position == 0 else 0
                        self.data.at[self.current_step, 'entry_price'] = current_price
        
        else:
            # Action logic without context
            if action == 1:  # Buy or go long
                if previous_position <= 0:
                    self.quantity = previous_cash / (current_price * (1 + transaction_cost_rate))
                    transaction_cost = calculate_transaction_cost(current_price, self.quantity)
                    new_cash = previous_cash - current_price * self.quantity - transaction_cost
                    new_position = 1
                    self.data.at[self.current_step, 'entry_price'] = current_price

            elif action == -1:  # Sell or go short
                if previous_position >= 0:
                    transaction_cost = calculate_transaction_cost(current_price, self.quantity)
                    new_cash = previous_cash + current_price * self.quantity - transaction_cost
                    self.quantity = 0
                    new_position = -1 if previous_position == 0 else 0

        # Update state variables
        self.data.at[self.current_step, 'position'] = new_position
        self.data.at[self.current_step, 'cash'] = new_cash
        self.data.at[self.current_step, 'nav'] = self.quantity * current_price
        self.data.at[self.current_step, 'net_worth'] = self.data.at[self.current_step, 'nav'] + new_cash
        self.data.at[self.current_step, 'transaction_cost'] = transaction_cost

        # Calculate returns
        current_net_worth = self.data.at[self.current_step, 'net_worth']
        self.data.at[self.current_step, 'returns'] = (current_net_worth - previous_net_worth) / previous_net_worth if previous_net_worth != 0 else 0

        # Calculate reward only when closing a position
        if previous_position != 0 and new_position == 0:
            self.reward = np.exp(((current_price * (1 - transaction_cost_rate) - entry_price * (1 + transaction_cost_rate)) /
                                (entry_price * (1 + transaction_cost_rate))) * (1 if previous_position > 0 else -1))
            self.done = True
            self.state = self._get_state()
            return self.state, self.reward, self.done
        
        else:
            self.reward = 0  # No reward unless the position is closed

        self.current_step += 1
        self.done = self.current_step >= len(self.data) - 1
        self.state = self._get_state()

        return self.state, self.reward, self.done



    def render(self): 
        # Set the Matplotlib figure and subplots
        fig = plt.figure(figsize=(10, 8))
        ax1 = fig.add_subplot(211, ylabel='Price', xlabel='Time')
        ax2 = fig.add_subplot(212, ylabel='Capital', xlabel='Time', sharex=ax1)

        # Plot the first graph -> Evolution of the stock market price
        self.data['close'].plot(ax=ax1, color='blue', lw=2)

        ax1.plot(self.data.loc[self.data['action'] == 1.0].index, 
                 self.data['close'][self.data['action'] == 1.0],
                 '^', markersize=5, color='green')   
        
        ax1.plot(self.data.loc[self.data['action'] == -1.0].index, 
                 self.data['close'][self.data['action'] == -1.0],
                 'v', markersize=5, color='red')
        
        # Plot the second graph -> Evolution of the trading capital
        self.data['net_worth'].plot(ax=ax2, color='blue', lw=2)

        ax2.plot(self.data.loc[self.data['action'] == 1.0].index, 
                 self.data['net_worth'][self.data['action'] == 1.0],
                 '^', markersize=5, color='green')   
        
        ax2.plot(self.data.loc[self.data['action'] == -1.0].index, 
                 self.data['net_worth'][self.data['action'] == -1.0],
                 'v', markersize=5, color='red')
        
        # Generation of the two legends and plotting
        ax1.legend(["Price", "Long",  "Short"])
        ax2.legend(["Capital", "Long", "Short"])
        #plt.savefig(''.join(['Figures/', str(self.marketSymbol), '_Rendering', '.png']))
        plt.show()


        

        