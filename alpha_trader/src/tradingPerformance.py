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

    def __init__(self, tradingData: pd.DataFrame):
        """
        OBJETIVO: Construtor do objeto inicializando as variáveis da classe. 
        
        ENTRADAS: - tradingData: Dados de trading da execução da estratégia.
        
        SAÍDAS: /
        """

        self.data = tradingData
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
        """
        OBJETIVO: Computar o Lucro & Perda (PnL) da estratégia de trading.
        
        SAÍDAS: - PnL: Lucro & Perda.
        """
        self.PnL = self.data['net_worth'].iloc[-1] - self.data['net_worth'].iloc[0]
        return self.PnL

    def computeAnnualizedReturn(self):
        """
        OBJETIVO: Computar o Retorno Anualizado da estratégia de trading.
        
        SAÍDAS: - annualizedReturn: Retorno Anualizado.
        """
        total_hours = (self.data.index[-1] - self.data.index[0]).total_seconds() / 3600
        self.annualizedReturn = (self.data['net_worth'].iloc[-1] / self.data['net_worth'].iloc[0]) ** (8760.0 / total_hours) - 1  # 8760 horas em um ano
        return self.annualizedReturn

    def computeAnnualizedVolatility(self):
        """
        OBJETIVO: Computar a Volatilidade Anualizada da estratégia de trading.
        
        SAÍDAS: - annualizedVolatility: Volatilidade Anualizada.
        """
        hourly_returns = self.data['returns']
        self.annualizedVolatility = np.std(hourly_returns) * np.sqrt(8760)  # 8760 horas em um ano
        return self.annualizedVolatility

    def computeProfitability(self):
        """
        OBJETIVO: Computar a Lucratividade e a Proporção Média Lucro/Prejuízo.
        
        SAÍDAS: - profitability: Lucratividade.
                 - averageProfitLossRatio: Proporção Média Lucro/Prejuízo.
        """
        trades = self.data[self.data['position'].diff() != 0]
        profitable_trades = trades[trades['returns'] > 0]
        losing_trades = trades[trades['returns'] <= 0]

        self.profitability = len(profitable_trades) / len(trades) if len(trades) > 0 else 0
        avg_profit = profitable_trades['returns'].mean() if len(profitable_trades) > 0 else 0
        avg_loss = losing_trades['returns'].mean() if len(losing_trades) > 0 else 0
        self.averageProfitLossRatio = avg_profit / abs(avg_loss) if avg_loss != 0 else 0

        return self.profitability, self.averageProfitLossRatio

    def computeSharpeRatio(self, risk_free_rate=0.02):
        """
        OBJETIVO: Computar a Razão de Sharpe da estratégia de trading.
        
        ENTRADAS: - risk_free_rate: Taxa livre de risco para o cálculo da Razão de Sharpe.
        
        SAÍDAS: - sharpeRatio: Razão de Sharpe.
        """
        excess_returns = self.data['returns'] - risk_free_rate / 8760  # Taxa livre de risco diária convertida para horária
        self.sharpeRatio = np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(8760)
        return self.sharpeRatio

    def computeSortinoRatio(self, risk_free_rate=0.02):
        """
        OBJETIVO: Computar a Razão de Sortino da estratégia de trading.
        
        ENTRADAS: - risk_free_rate: Taxa livre de risco para o cálculo da Razão de Sortino.
        
        SAÍDAS: - sortinoRatio: Razão de Sortino.
        """
        excess_returns = self.data['returns'] - risk_free_rate / 8760  # Taxa livre de risco diária convertida para horária
        downside_deviation = np.std(excess_returns[excess_returns < 0])
        self.sortinoRatio = np.mean(excess_returns) / downside_deviation * np.sqrt(8760)
        return self.sortinoRatio

    def computeMaxDrawdown(self):
        """
        OBJETIVO: Computar a Máxima Retração e a Duração Máxima da Retração.
        
        SAÍDAS: - maxDD: Máxima Retração.
                 - maxDDD: Duração Máxima da Retração.
        """
        cumulative_returns = self.data['net_worth'].cummax()
        drawdown = (self.data['net_worth'] - cumulative_returns) / cumulative_returns
        self.maxDD = drawdown.min()
        end_date = drawdown.idxmin()
        start_date = (self.data['net_worth'][:end_date]).idxmax()
        self.maxDDD = (end_date - start_date).total_seconds() / 3600  # Duração em horas
        return self.maxDD, self.maxDDD

    def computeSkewness(self):
        """
        OBJETIVO: Computar a Assimetria dos retornos.
        
        SAÍDAS: - skewness: Assimetria dos retornos.
        """
        self.skewness = self.data['returns'].skew()
        return self.skewness

    def computeNumberOfTrades(self):
        """
        OBJETIVO: Computar o número de trades realizados.
        
        SAÍDAS: - numberOfTrades: Número de trades realizados.
        """
        self.numberOfTrades = self.data['position'].diff().abs().sum() / 2  # Cada trade envolve duas mudanças de posição
        return self.numberOfTrades

    def computePerformance(self):
        """
        OBJETIVO: Computar todos os indicadores de desempenho.
        
        SAÍDAS: Dicionário contendo todos os indicadores de desempenho.
        """
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
        """
        OBJETIVO: Exibir todo o conjunto de indicadores de desempenho em uma tabela.
        
        SAÍDAS: Imprime uma tabela com todos os indicadores de desempenho.
        """
        performance = self.computePerformance()
        performance_table = tabulate(performance.items(), headers=['Indicador', 'Valor'], tablefmt='pretty')
        
        print(performance_table)

    
        