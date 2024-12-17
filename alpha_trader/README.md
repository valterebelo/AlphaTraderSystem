# Alpha Trader Bot

## Visão Geral

O AlfaTrader é um pacote de trading para implementação e teste estratégias de trading com bitcoin, utilizando dados on-chain e de mercado.

## Componentes

### 1. DataManager
- **Propósito**: Gerencia o download e processamento de dados on-chain e OHLCV (para fins de backtest).
- **Principais Funcionalidades**:
  - Busca dados do Glassnode, Binance (Bybit também).
  - Mescla e processa dados para avaliação de estratégias.
  - Utiliza variáveis de ambiente para chaves de API e endpoints.

### 2. Trading Strategies
- **Propósito**: Utilizado para criar intâncias da classe Strategy, utilizando dados do DataManager. 
- **AlphaTraderLongBiased2**: Implementa uma estratégia técnica em cima do indicador fundamental Stablecoin Ratio Signal, informado por métricas de on-chain que contextualizam o mercado atual (bull ou bear market). Essa foi a estratégia com melhor resultado no backtest.

### 3. PerformanceEstimator
- **Propósito**: Avalia o desempenho das instâncias de estratégia de trading.
- **Principais Métricas**:
  - Lucro e Perda (PnL)
  - Retorno e Volatilidade Anualizados
  - Razões de Sharpe e Sortino
  - Máxima Retração (Drawdown)
  - etc. 

### 4. Estratégia Abstrata
- **Propósito**: Fornece uma classe base para todas as estratégias de trading, garantindo consistência e reutilização.
- **Funcionalidades**:
  - Métodos abstratos para gerar sinais e aplicar estratégias.
  - Capacidades de backtesting com visualização de desempenho.

## Configuração

### Configuração do Ambiente

Para executar o pacote AlphaTrader, você precisa configurar um arquivo `.env` no diretório `alpha_trader` com a seguinte configuração:

GLASSNODE_API_KEY='sua_chave_api_glassnode'

SSR='indicators/ssr_oscillator'
BTC_PRICE='market/price_usd_close'
SUPPLY_IN_PROFIT='supply/profit_relative'
MVRV_Z_SCORE='market/mvrv_z_score'
BTC_REALIZED_PRICE='market/price_realized_usd'
CVD='market/spot_cvd_sum'
BTC_HASH_RATE='mining/hash_rate_mean'
ENTITY_ADJ_NUPL='indicators/net_unrealized_profit_loss_account_based'
PUELL_MULTIPLE='indicators/puell_multiple'
ENTITY_ADJ_DORMANCY_FLOW='indicators/dormancy_flow'

BYBIT_API_KEY='sua_chave_api_bybit'
BYBIT_API_SECRET='seu_segredo_api_bybit'
BYBIT_API_KEY_TEST='sua_chave_api_bybit_teste'
BYBIT_API_SECRET_TEST='seu_segredo_api_bybit_teste'
BYBIT_API_KEY_EMP='sua_chave_api_bybit_emp'
BYBIT_API_SECRET_EMP='seu_segredo_api_bybit_emp'


### Instalação

1. Clone o repositório:
   ```bash
   git clone https://github.com/valterebelo/AlphaTraderSystem.git
   ```

2. Navegue até o diretório do projeto:
   ```bash
   cd alpha_trader
   ```

3. Instale os pacotes necessários:
   ```bash
   pip install -r requirements.txt
   ```

### Uso

- **Backtesting**: Use o método `backtest` nas classes de estratégia para avaliar o desempenho.
- **Trading ao Vivo**: Implemente o método `apply_strategy` para executar trades com base nos sinais gerados. (Em desenvolvimento)

## Licença

Este projeto está licenciado sob a Licença MIT.
