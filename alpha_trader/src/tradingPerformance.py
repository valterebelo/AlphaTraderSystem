"""
Projeto: Alpha Trader Intelligence
Objetivo: Implementação de um estimador de resultados. 
Autor: Valter Rebelo
"""

###############################################################################
################################### Imports ###################################
###############################################################################

import numpy as np
import pandas as pd
from tabulate import tabulate
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots  # Certifique-se de que esta importação está presente

###############################################################################
########################### Class PerformanceEstimator #########################
###############################################################################

class PerformanceEstimator:
    """
    OBJETIVO: Estimar com precisão o desempenho de uma estratégia de trading, 
              computando diversos indicadores de desempenho.
    """

    def __init__(self, tradingData: pd.DataFrame, visualize=False):
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
        return self.PnL

    def computeMaxDrawdown(self):
        cumulative_returns = self.data['net_worth'].cummax()
        drawdown = (self.data['net_worth'] - cumulative_returns) / cumulative_returns
        self.maxDD = drawdown.min()
        end_date = drawdown.idxmin()
        start_date = (self.data['net_worth'][:end_date]).idxmax()
        self.maxDDD = (end_date - start_date).total_seconds() / 3600  # Duração em horas

        if self.visualize:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=self.data.index, y=self.data['net_worth'], mode='lines', name='Net Worth'))
            fig.add_trace(go.Scatter(x=self.data.index, y=cumulative_returns, mode='lines',
                                     name='Cumulative Max', line=dict(dash='dash')))
            fig.add_trace(go.Scatter(
                x=self.data.index,
                y=self.data['net_worth'],
                fill='tonexty',
                fillcolor='rgba(255,0,0,0.3)',
                mode='none',
                name='Drawdown'
            ))
            fig.update_layout(title='Max Drawdown Analysis',
                              xaxis_title='Time',
                              yaxis_title='Net Worth',
                              template='plotly_white')
            fig.show()

        return self.maxDD, self.maxDDD

    def computeAnnualizedReturn(self):
        total_hours = (self.data.index[-1] - self.data.index[0]).total_seconds() / 3600
        self.annualizedReturn = (self.data['net_worth'].iloc[-1] / self.data['net_worth'].iloc[0] - 1)
        return self.annualizedReturn

    def computeAnnualizedVolatility(self):
        hourly_returns = self.data['strategy_returns']
        self.annualizedVolatility = np.std(hourly_returns)
        if self.visualize:
            fig = px.histogram(self.data, x='strategy_returns', nbins=50, title='Distribution of Hourly Returns',
                               labels={'strategy_returns': 'Hourly Returns', 'count': 'Frequency'})
            fig.update_layout(template='plotly_white')
            fig.show()
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
            fig = go.Figure(data=[
                go.Bar(name='Profitable Trades', x=['Profitable Trades'], y=[len(profitable_trades)],
                       marker_color='green'),
                go.Bar(name='Losing Trades', x=['Losing Trades'], y=[len(losing_trades)],
                       marker_color='red')
            ])
            fig.update_layout(title='Profitability Analysis',
                              yaxis_title='Number of Trades',
                              template='plotly_white',
                              barmode='group')
            fig.show()

        return self.profitability, self.averageProfitLossRatio

    def computeSharpeRatio(self, risk_free_rate=0.05):
        risk_free_rate_hourly = (1 + risk_free_rate) ** (1 / 8760) - 1
        excess_returns = self.data['strategy_returns'] - risk_free_rate_hourly
        self.sharpeRatio = np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(8760)
        if self.visualize:
            fig = px.line(x=self.data.index, y=excess_returns.cumsum(), title='Sharpe Ratio Analysis',
                          labels={'x': 'Time', 'y': 'Cumulative Excess Returns'})
            fig.add_hline(y=0, line_dash="dash", line_color="grey")
            fig.update_layout(template='plotly_white')
            fig.show()
        return self.sharpeRatio

    def computeSortinoRatio(self, risk_free_rate=0.02):
        risk_free_rate_hourly = (1 + risk_free_rate) ** (1 / 8760) - 1
        excess_returns = self.data['strategy_returns'] - risk_free_rate_hourly
        downside_deviation = np.std(excess_returns[excess_returns < 0])
        self.sortinoRatio = np.mean(excess_returns) / downside_deviation * np.sqrt(8760) if downside_deviation != 0 else 0
        if self.visualize:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=self.data.index, y=excess_returns, mode='lines', name='Excess Returns'))
            fig.add_trace(go.Scatter(
                x=self.data.index,
                y=[0]*len(self.data.index),
                mode='lines',
                line=dict(color='grey', dash='dash'),
                name='Zero Line'
            ))
            fig.add_trace(go.Scatter(
                x=self.data.index,
                y=np.where(excess_returns < 0, excess_returns, 0),
                fill='tozeroy',
                fillcolor='rgba(255,0,0,0.3)',
                mode='none',
                name='Downside Risk'
            ))
            fig.update_layout(title='Sortino Ratio Analysis',
                              xaxis_title='Time',
                              yaxis_title='Excess Returns',
                              template='plotly_white')
            fig.show()
        return self.sortinoRatio

    def computeSkewness(self):
        self.skewness = self.data['strategy_returns'].skew()
        return self.skewness

    def plotPriceAndPosition(self):
        """
        Updates:
        1. Two subplots (rows=2, cols=1):
        - Upper: Close Price + Position Markers
        - Lower: Net Worth (segmented by position sign)
        2. Remove net worth segments from the legend (showlegend=False).
        3. Make symbols smaller (e.g. size=6).
        """

        if self.visualize:
            # Create two subplots, one for close/positions (top) and one for net worth (bottom)
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                                vertical_spacing=0.05, 
                                subplot_titles=("Close Price & Positions", "Net Worth"))

            # Plot the BTC close price (thin gray line) on the top subplot
            fig.add_trace(
                go.Scatter(x=self.data.index, y=self.data['close'], mode='lines', 
                        name='Close Price', line=dict(color='gray', width=1)),
                row=1, col=1
            )

            # Identify position changes
            position_changes = self.data['position'].diff().fillna(0) != 0

            # Define marker styles based on position value
            position_marker_map = {
                1.0: ('green', 'triangle-up'),
                0.5: ('green', 'square'),
                2.0: ('green', 'x'),
                0: ('goldenrod', 'square'),
                -0.5: ('red', 'square'),
                -1.0: ('red', 'triangle-down')
            }

            # Add a separate scatter trace for each position value at changes on the top subplot
            for pos_val, (color, symbol) in position_marker_map.items():
                df_pos = self.data[(self.data['position'] == pos_val) & position_changes]
                if len(df_pos) > 0:
                    fig.add_trace(
                        go.Scatter(
                            x=df_pos.index, 
                            y=df_pos['close'],
                            mode='markers',
                            marker=dict(
                                symbol=symbol, 
                                size=6,  # smaller symbols
                                color=color,
                                line=dict(color='black', width=1)
                            ),
                            name=f'Pos {pos_val}'
                        ),
                        row=1, col=1
                    )

            # Now handle the net worth line on the bottom subplot
            # Map sign to color for net_worth line
            sign_color_map = {
                1: 'darkgreen',   # long
                0: 'goldenrod',   # cash
                -1: 'darkred'     # short
            }

            positions = self.data['position'].values
            net_worth_values = self.data['net_worth'].values
            times = self.data.index
            signs = np.sign(positions)

            # Segment the net_worth line by sign changes
            segments = []
            start_idx = 0
            for i in range(1, len(signs)):
                if signs[i] != signs[i-1]:
                    segments.append((start_idx, i-1, signs[i-1]))
                    start_idx = i
            segments.append((start_idx, len(signs)-1, signs[-1]))

            # Plot each net_worth segment with corresponding color and no legend
            for start, end, s in segments:
                segment_color = sign_color_map[s]
                fig.add_trace(
                    go.Scatter(
                        x=times[start:end+1],
                        y=net_worth_values[start:end+1],
                        mode='lines',
                        line=dict(color=segment_color, width=2),
                        showlegend=False  # no legend for these segments
                    ),
                    row=2, col=1
                )

            # Update layout
            fig.update_layout(
                template='plotly_white',
                showlegend=True,  # Keep legend for markers and close price
                title='Asset Price, Position Changes, and Net Worth'
            )
            
            fig.update_xaxes(title_text="Time", row=2, col=1)
            fig.update_yaxes(title_text="Close Price", row=1, col=1)
            fig.update_yaxes(title_text="Net Worth", row=2, col=1)

            fig.show()

    def computeNumberOfTrades(self):
        self.numberOfTrades = self.data['position'].diff().abs().sum() / 2
        if self.visualize:
            fig = px.line(self.data, x=self.data.index, y='position', title='Number of Trades Over Time',
                          labels={'position': 'Position', 'index': 'Time'})
            fig.update_layout(template='plotly_white')
            fig.show()
        return self.numberOfTrades

    def computePerformance(self):
        performance = {
            'Performance History': self.plotPriceAndPosition(),
            'PnL': self.computePnL(),
            'Max Drawdown': self.computeMaxDrawdown(),
            'Annualized Return': self.computeAnnualizedReturn(),
            'Annualized Volatility': self.computeAnnualizedVolatility(),
            'Profitability': self.computeProfitability(),
            'Sharpe Ratio': self.computeSharpeRatio(),
            'Sortino Ratio': self.computeSortinoRatio(),
            'Skewness': self.computeSkewness(),
            'Number of Trades': self.computeNumberOfTrades()
        }
        return performance

    def displayPerformance(self):
        performance = self.computePerformance()
        
        # Format the tuple values
        if isinstance(performance['Profitability'], tuple):
            profitability, profit_loss_ratio = performance['Profitability']
            performance['Profitability'] = f"{profitability:.2%}"
            performance['Profit/Loss Ratio'] = f"{float(profit_loss_ratio):.2f}"
        
        if isinstance(performance['Max Drawdown'], tuple):
            max_dd, max_dd_duration = performance['Max Drawdown']
            performance['Max Drawdown'] = f"{float(max_dd):.2%}"
            performance['Max Drawdown Duration (hours)'] = f"{float(max_dd_duration):.1f}"
        
        # Remove entries that are not indicators
        performance = {k: v for k, v in performance.items() if k not in ['Positions']}
        
        # Format other numeric values
        formatted_performance = {
            key: (
                f"{value:.2%}" if key in ['Annualized Return', 'Annualized Volatility']
                else f"{value:.2f}" if isinstance(value, (float, np.float64, np.float32))
                else value
            )
            for key, value in performance.items()
        }
        
        performance_table = tabulate(
            formatted_performance.items(), 
            headers=['Indicador', 'Valor'], 
            tablefmt='pretty'
        )
        print(performance_table)