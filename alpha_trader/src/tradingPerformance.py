"""
Projeto: AlfaTrader Intelligence
Objetivo: Implementação de um estimador de resultados. 
Autor: Valter Rebelo

"""

###############################################################################
################################### Imports ###################################
###############################################################################


import numpy as np
import pandas as pd
from tabulate import tabulate
import matplotlib.pyplot as plt



###############################################################################
########################### Class tradingStrategy #############################
###############################################################################

class PerformanceEstimator:
    """
    OBJETIVO: Estimar com precisão o desempenho de uma estratégia de trading, 
              computando diversos indicadores de desempenho.
        
    VARIÁVEIS: - data: Dados de atividade de trading do ambiente de trading.
               - PnL: Lucro & Perda (indicador de desempenho).
               - annualizedReturn: Retorno Anualizado (indicador de desempenho).
               - annualizedVolatility: Volatilidade Anualizada (indicador de desempenho).
               - profitability: Lucratividade (indicador de desempenho).
               - averageProfitLossRatio: Proporção Média Lucro/Prejuízo (indicador de desempenho).
               - sharpeRatio: Razão de Sharpe (indicador de desempenho).
               - sortinoRatio: Razão de Sortino (indicador de desempenho).
               - maxDD: Máxima Retração (indicador de desempenho).
               - maxDDD: Duração Máxima da Retração (indicador de desempenho).
               - skewness: Assimetria dos retornos (indicador de desempenho).
               - numberOfTrades: Número de trades realizados.
          
    MÉTODOS:   -  __init__: Construtor do objeto inicializando algumas variáveis da classe. 
               - computePnL: Computar o Lucro & Perda.
               - computeAnnualizedReturn: Computar o Retorno Anualizado.
               - computeAnnualizedVolatility: Computar a Volatilidade Anualizada.
               - computeProfitability: Computar a Lucratividade e a Proporção Média Lucro/Prejuízo.
               - computeSharpeRatio: Computar a Razão de Sharpe.
               - computeSortinoRatio: Computar a Razão de Sortino.
               - computeMaxDrawdown: Computar a Máxima Retração e a Duração Máxima da Retração.
               - computeSkewness: Computar a Assimetria dos retornos.
               - computeNumberOfTrades: Computar o número de trades realizados.
               - computePerformance: Computar todos os indicadores de desempenho.
               - displayPerformance: Exibir todo o conjunto de indicadores de desempenho em uma tabela.
    """

    def __init__(self, tradingData: pd.DataFrame, visualize=False):
        """
        OBJETIVO: Construtor do objeto inicializando as variáveis da classe.
        
        ENTRADAS: - tradingData: Dados de trading da execução da estratégia.
                  - visualize: Se verdadeiro, gera gráficos para funções aplicáveis.
        
        SAÍDAS: /
        """
        self.data = tradingData
        self.visualize = visualize
        self.PnL = 0
        self.annualizedReturn = 0
        self.annualizedVolatility = 0
        self.profitability = 0
        self.averageProfitLossRatio = 0
        self.sharpeRatio = 0
        self.sortinoRatio = 0
        self.maxDD = 0
        self.maxDDD = 0
        self.skewness = 0
        self.numberOfTrades = 0

    def computePnL(self):
        self.PnL = self.data['net_worth'].iloc[-1] - self.data['net_worth'].iloc[0]
        if self.visualize:
            plt.figure(figsize=(10, 6))
            plt.plot(self.data['net_worth'])
            plt.title('Net Worth Over Time')
            plt.xlabel('Time')
            plt.ylabel('Net Worth')
            plt.grid(True)
            plt.show()
        return self.PnL

    def computeAnnualizedReturn(self):
        total_hours = (self.data.index[-1] - self.data.index[0]).total_seconds() / 3600
        self.annualizedReturn = (self.data['net_worth'].iloc[-1] / self.data['net_worth'].iloc[0]) ** (8760.0 / total_hours) - 1
        if self.visualize:
            plt.figure(figsize=(10, 6))
            plt.plot(self.data['net_worth'], label='Net Worth')
            plt.title('Annualized Return')
            plt.xlabel('Time')
            plt.ylabel('Net Worth')
            plt.grid(True)
            plt.legend()
            plt.show()
        return self.annualizedReturn

    def computeAnnualizedVolatility(self):
        hourly_returns = self.data['strategy_returns']
        self.annualizedVolatility = np.std(hourly_returns) * np.sqrt(8760)
        if self.visualize:
            plt.figure(figsize=(10, 6))
            plt.hist(hourly_returns, bins=50, edgecolor='black')
            plt.title('Distribution of Hourly Returns')
            plt.xlabel('Hourly Returns')
            plt.ylabel('Frequency')
            plt.grid(True)
            plt.show()
        return self.annualizedVolatility

    def computeProfitability(self):
        trades = self.data[self.data['position'].diff() != 0]
        profitable_trades = trades[trades['strategy_returns'] > 0]
        losing_trades = trades[trades['strategy_returns'] <= 0]

        self.profitability = len(profitable_trades) / len(trades) if len(trades) > 0 else 0
        avg_profit = profitable_trades['strategy_returns'].mean() if len(profitable_trades) > 0 else 0
        avg_loss = losing_trades['strategy_returns'].mean() if len(losing_trades) > 0 else 0
        self.averageProfitLossRatio = avg_profit / abs(avg_loss) if avg_loss != 0 else 0

        if self.visualize:
            plt.figure(figsize=(10, 6))
            plt.bar(['Profitable Trades', 'Losing Trades'], [len(profitable_trades), len(losing_trades)])
            plt.title('Profitability Analysis')
            plt.ylabel('Number of Trades')
            plt.grid(True)
            plt.show()

        return self.profitability, self.averageProfitLossRatio

    def computeSharpeRatio(self, risk_free_rate=0.05):
        risk_free_rate_hourly = (1 + risk_free_rate) ** (1/8760) - 1
        excess_returns = self.data['strategy_returns'] - risk_free_rate_hourly
        self.sharpeRatio = np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(8760)
        if self.visualize:
            plt.figure(figsize=(10, 6))
            plt.plot(self.data.index, excess_returns.cumsum(), label='Cumulative Excess Returns')
            plt.title('Sharpe Ratio Analysis')
            plt.xlabel('Time')
            plt.ylabel('Cumulative Excess Returns')
            plt.grid(True)
            plt.legend()
            plt.show()
        return self.sharpeRatio

    def computeSortinoRatio(self, risk_free_rate=0.02):
        risk_free_rate_hourly = (1 + risk_free_rate) ** (1/8760) - 1
        excess_returns = self.data['strategy_returns'] - risk_free_rate_hourly
        downside_deviation = np.std(excess_returns[excess_returns < 0])
        self.sortinoRatio = np.mean(excess_returns) / downside_deviation * np.sqrt(8760)
        if self.visualize:
            plt.figure(figsize=(10, 6))
            plt.plot(self.data.index, excess_returns, label='Excess Returns')
            plt.fill_between(self.data.index, 0, excess_returns, where=excess_returns<0, color='red', alpha=0.5, label='Downside Risk')
            plt.title('Sortino Ratio Analysis')
            plt.xlabel('Time')
            plt.ylabel('Excess Returns')
            plt.grid(True)
            plt.legend()
            plt.show()
        return self.sortinoRatio

    def computeSkewness(self):
        self.skewness = self.data['strategy_returns'].skew()
        if self.visualize:
            plt.figure(figsize=(10, 6))
            plt.hist(self.data['strategy_returns'], bins=50, edgecolor='black')
            plt.title('Skewness of Strategy Returns')
            plt.xlabel('Strategy Returns')
            plt.ylabel('Frequency')
            plt.grid(True)
            plt.show()
        return self.skewness

    def computeMaxDrawdown(self):
        cumulative_returns = self.data['net_worth'].cummax()
        drawdown = (self.data['net_worth'] - cumulative_returns) / cumulative_returns
        self.maxDD = drawdown.min()
        end_date = drawdown.idxmin()
        start_date = (self.data['net_worth'][:end_date]).idxmax()
        self.maxDDD = (end_date - start_date).total_seconds() / 3600  # Duration in hours

        if self.visualize:
            plt.figure(figsize=(10, 6))
            plt.plot(self.data['net_worth'], label='Net Worth')
            plt.plot(cumulative_returns, label='Cumulative Max', linestyle='--')
            plt.fill_between(self.data.index, self.data['net_worth'], cumulative_returns, color='red', alpha=0.3, label='Drawdown')
            plt.title('Max Drawdown Analysis')
            plt.xlabel('Time')
            plt.ylabel('Net Worth')
            plt.grid(True)
            plt.legend()
            plt.show()

        return self.maxDD, self.maxDDD

    def computeNumberOfTrades(self):
        self.numberOfTrades = self.data['position'].diff().abs().sum() / 2
        if self.visualize:
            plt.figure(figsize=(10, 6))
            plt.plot(self.data['position'], label='Position')
            plt.title('Number of Trades Over Time')
            plt.xlabel('Time')
            plt.ylabel('Position')
            plt.grid(True)
            plt.legend()
            plt.show()
        return self.numberOfTrades

    def computePerformance(self):
        performance = {
            'PnL': self.computePnL(),
            'Annualized Return': self.computeAnnualizedReturn(),
            'Annualized Volatility': self.computeAnnualizedVolatility(),
            'Profitability': self.computeProfitability(),
            'Sharpe Ratio': self.computeSharpeRatio(),
            'Sortino Ratio': self.computeSortinoRatio(),
            'Max Drawdown': self.computeMaxDrawdown(),
            'Skewness': self.computeSkewness(),
            'Number of Trades': self.computeNumberOfTrades()
        }
        return performance

    def displayPerformance(self):
        performance = self.computePerformance()
        performance_table = tabulate(performance.items(), headers=['Indicador', 'Valor'], tablefmt='pretty')
        print(performance_table)

    
        