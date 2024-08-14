from datetime import datetime
import pandas as pd 

def timestamp_to_datetime(timestamp):
    """
    Convert a Unix timestamp (in milliseconds) to a human-readable datetime string.

    :param timestamp: Unix timestamp in milliseconds.
    :return: Datetime string in the format 'YYYY-MM-DD HH:MM:SS'.
    """
    return datetime.utcfromtimestamp(timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S')


def parse_klines(response):
    if response.get('retCode') != 0:
        raise ValueError(f"Error in response: {response.get('retMsg', 'Unknown error')}")

    candles = []

    # Correctly access 'list' inside 'result'
    for candle in response.get('result', {}).get('list', []):
        candles.append({
            't': timestamp_to_datetime(int(candle[0])),
            'open': float(candle[1]),
            'high': float(candle[2]),
            'low': float(candle[3]),
            'close': float(candle[4]),
            'volume': float(candle[5]),
            'turnover': float(candle[6])
        })

    # Create DataFrame and set 't' as the index
    df = pd.DataFrame(candles)
    df.set_index('t', inplace=True)
    df.sort_index(ascending=True, inplace=True)
    return df


def parse_orderbook(response):
    if response.get('retCode') != 0:
        raise ValueError(f"Error in response: {response.get('retMsg', 'Unknown error')}")

    bids, asks = [], []

    for bid in response.get('result', {}).get('b', []):
        price, size = bid
        bids.append({'price': float(price), 'size': float(size)})

    for ask in response.get('result', {}).get('a', []):
        price, size = ask
        asks.append({'price': float(price), 'size': float(size)})

    return pd.DataFrame({'bids': bids, 'asks': asks})


def parse_positions(response):
    positions = []

    if response.get('retCode') != 0:
        raise ValueError(f"Error in response: {response.get('retMsg', 'Unknown error')}")

    for pos in response.get('result', {}).get('list', []):
        position = {

            'created_time': timestamp_to_datetime(int(pos.get('createdTime', 0))) if pos.get('createdTime') else None,
            'updated_time': timestamp_to_datetime(int(pos.get('updatedTime', 0))) if pos.get('updatedTime') else None,
            'symbol': pos.get('symbol', 'Unknown Symbol'),
            'side': pos.get('side', 'Unknown Side'),
            'size': float(pos.get('size', 0)) if pos.get('size') else 0.0,
            'avg_price': float(pos.get('avgPrice', 0)) if pos.get('avgPrice') else 0.0,
            'position_value': float(pos.get('positionValue', 0)) if pos.get('positionValue') else 0.0,
            'unrealised_pnl': float(pos.get('unrealisedPnl', 0)) if pos.get('unrealisedPnl') else 0.0,
            'leverage': float(pos.get('leverage', 0)) if pos.get('leverage') else 0.0,
            'liq_price': pos.get('liqPrice', None),
            'mark_price': float(pos.get('markPrice', 0)) if pos.get('markPrice') else 0.0,
            'position_status': pos.get('positionStatus', 'Unknown Status'),
            'trade_mode': pos.get('tradeMode', 'Unknown Trade Mode'),
            'position_balance': float(pos.get('positionBalance', 0)) if pos.get('positionBalance') else 0.0,
            'take_profit': float(pos.get('takeProfit', 0)) if pos.get('takeProfit') not in ['', None] else None,
            'stop_loss': float(pos.get('stopLoss', 0)) if pos.get('stopLoss') not in ['', None] else None,
            'position_idx': pos.get('positionIdx')
        }
        positions.append(position)

    if not positions:  # Check if the positions list is empty
        return print('No open positions at the moment.')

    return pd.DataFrame(positions)


def parse_wallet_balance(response):
    if response.get('retCode') != 0:
        raise ValueError(f"Error in response: {response.get('retMsg', 'Unknown error')}")

    wallet_info = []

    for account in response.get('result', {}).get('list', []):
        for coin_info in account.get('coin', []):
            wallet_info.append({
                'account_type': account.get('accountType'),
                'total_equity': float(account.get('totalEquity', 0)) if account.get('totalEquity') not in ['', None] else 0.0,
                'total_wallet_balance': float(account.get('totalWalletBalance', 0)) if account.get('totalWalletBalance') not in ['', None] else 0.0,
                'total_margin_balance': float(account.get('totalMarginBalance', 0)) if account.get('totalMarginBalance') not in ['', None] else 0.0,
                'total_available_balance': float(account.get('totalAvailableBalance', 0)) if account.get('totalAvailableBalance') not in ['', None] else 0.0,
                'coin': coin_info.get('coin'),
                'equity': float(coin_info.get('equity', 0)) if coin_info.get('equity') not in ['', None] else 0.0,
                'usd_value': float(coin_info.get('usdValue', 0)) if coin_info.get('usdValue') not in ['', None] else 0.0,
                'wallet_balance': float(coin_info.get('walletBalance', 0)) if coin_info.get('walletBalance') not in ['', None] else 0.0,
                'free': float(coin_info.get('free', 0)) if coin_info.get('free') not in ['', None] else 0.0,
                'locked': float(coin_info.get('locked', 0)) if coin_info.get('locked') not in ['', None] else 0.0,
                'spot_hedging_qty': float(coin_info.get('spotHedgingQty', 0)) if coin_info.get('spotHedgingQty') not in ['', None] else 0.0,
                'borrow_amount': float(coin_info.get('borrowAmount', 0)) if coin_info.get('borrowAmount') not in ['', None] else 0.0,
                'available_to_withdraw': float(coin_info.get('availableToWithdraw', 0)) if coin_info.get('availableToWithdraw') not in ['', None] else 0.0,
                'accrued_interest': float(coin_info.get('accruedInterest', 0)) if coin_info.get('accruedInterest') not in ['', None] else 0.0,
                'unrealised_pnl': float(coin_info.get('unrealisedPnl', 0)) if coin_info.get('unrealisedPnl') not in ['', None] else 0.0,
                'cum_realised_pnl': float(coin_info.get('cumRealisedPnl', 0)) if coin_info.get('cumRealisedPnl') not in ['', None] else 0.0,
                'margin_collateral': coin_info.get('marginCollateral', False),
                'collateral_switch': coin_info.get('collateralSwitch', False),
            })

    return pd.DataFrame(wallet_info)

def parse_coin_balance(response):
    if response.get('retCode') != 0:
        raise ValueError(f"Error in response: {response.get('retMsg', 'Unknown error')}")

    timestamp = response.get('time', 0)
    parsed_time = timestamp_to_datetime(timestamp)

    balance_info = []

    for balance in response.get('result', {}).get('balance', []):
        wallet_balance = float(balance.get('walletBalance', 0))
        if wallet_balance != 0:  # Only include balances where wallet_balance is not 0
            balance_info.append({
                'account_type': response.get('result', {}).get('accountType', ''),
                'member_id': response.get('result', {}).get('memberId', ''),
                'timestamp': parsed_time,
                'coin': balance.get('coin'),
                'wallet_balance': wallet_balance,
                'transfer_balance': float(balance.get('transferBalance', 0)),
                'bonus': float(balance.get('bonus', 0)) if balance.get('bonus') else None
            })

    return pd.DataFrame(balance_info)

def parse_transaction_log(response):
    if response.get('retCode') != 0:
        raise ValueError(f"Error in response: {response.get('retMsg', 'Unknown error')}")

    transactions = []

    for item in response.get('result', {}).get('list', []):
        transaction = {
            'order_link_id': item.get('orderLinkId'),
            'symbol': item.get('symbol'),
            'category': item.get('category'),
            'side': item.get('side'),
            'transaction_time': timestamp_to_datetime(int(item.get('transactionTime'))),
            'type': item.get('type'),
            'qty': float(item.get('qty')),
            'size': float(item.get('size')),
            'currency': item.get('currency'),
            'trade_price': float(item.get('tradePrice', 0)),
            'funding': float(item.get('funding', 0)) if item.get('funding') else None,
            'fee': float(item.get('fee')),
            'cash_flow': float(item.get('cashFlow')),
            'change': float(item.get('change')),
            'cash_balance': float(item.get('cashBalance')),
            'fee_rate': float(item.get('feeRate', 0)) if item.get('feeRate') else None,
            'bonus_change': float(item.get('bonusChange', 0)) if item.get('bonusChange') else None,
            'trade_id': item.get('tradeId'),
            'order_id': item.get('orderId'),
            'id': item.get('id'),
        }
        transactions.append(transaction)

    return pd.DataFrame(transactions)




def parse_order_history(response):
    """
    Parse the order history response from the API.

    :param response: The raw response dictionary from the API.
    :return: A pandas DataFrame containing the parsed order history.
    """
    if response.get('retCode') != 0:
        raise ValueError(f"Error in response: {response.get('retMsg', 'Unknown error')}")

    order_history = []

    for order in response.get('result', {}).get('list', []):
        try:
            order_data = {
                'created_time': timestamp_to_datetime(int(order.get('createdTime', 0))) if order.get('createdTime') else None,
                'order_link_id': order.get('orderLinkId', ''),
                'side': order.get('side', ''),
                'symbol': order.get('symbol', ''),
                'avg_price': float(order.get('avgPrice', 0)) if order.get('avgPrice') not in ['', None] else 0.0,
                'quantity': float(order.get('qty', 0)) if order.get('qty') not in ['', None] else 0.0,
                'order_status': order.get('orderStatus', ''),
                'cum_exec_qty': float(order.get('cumExecQty', 0)) if order.get('cumExecQty') not in ['', None] else 0.0,
                'cum_exec_value': float(order.get('cumExecValue', 0)) if order.get('cumExecValue') not in ['', None] else 0.0,
                'cum_exec_fee': float(order.get('cumExecFee', 0)) if order.get('cumExecFee') not in ['', None] else 0.0,
                'price': float(order.get('price', 0)) if order.get('price') not in ['', None] else 0.0,
                'position_idx': order.get('positionIdx', 0),
                'cancel_type': order.get('cancelType', ''),
                'reject_reason': order.get('rejectReason', ''),
                'leaves_qty': float(order.get('leavesQty', 0)) if order.get('leavesQty') not in ['', None] else 0.0,
                'leaves_value': float(order.get('leavesValue', 0)) if order.get('leavesValue') not in ['', None] else 0.0,
                'time_in_force': order.get('timeInForce', ''),
                'order_type': order.get('orderType', ''),
                'trigger_price': float(order.get('triggerPrice', 0)) if order.get('triggerPrice') not in ['', None] else 0.0,
                'take_profit': float(order.get('takeProfit', 0)) if order.get('takeProfit') not in ['', None] else 0.0,
                'stop_loss': float(order.get('stopLoss', 0)) if order.get('stopLoss') not in ['', None] else 0.0,
                'reduce_only': order.get('reduceOnly', False),
                'close_on_trigger': order.get('closeOnTrigger', False),
                'order_id': order.get('orderId'),
                'updated_time': timestamp_to_datetime(int(order.get('updatedTime', 0))) if order.get('updatedTime') else None,
            }
            order_history.append(order_data)
        except (ValueError, TypeError) as e:
            print(f"Skipping order due to error: {e}")
            continue

    return pd.DataFrame(order_history)
