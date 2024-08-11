"""
Projeto: AlfaTrader AI
Objetivo: Realização de download de dados on-chain e OHLCV por hora, com splits de treinamento e teste.
Autor: Valter Rebelo

"""

###############################################################################
################################### Imports ###################################
###############################################################################


import os
import pandas as pd
import pandas_ta as ta
import numpy as np
import requests
import re
import logging
from binance.spot import Spot
from pybit.unified_trading import HTTP
import time
from datetime import datetime, timedelta
import warnings
from dotenv import load_dotenv

load_dotenv()
warnings.filterwarnings('ignore')


###############################################################################
######################### Classe DataManager ##################################
###############################################################################

class DataManager:
    
    def __init__(self):
        self.glassnode_api_key = os.getenv('GLASSNODE_API_KEY')
        self.bybit_api_key = os.getenv('BYBIT_API_KEY')
        self.bybit_api_secret = os.getenv('BYBIT_API_SECRET')
        self.bybit_session = HTTP(testnet=False, api_key=self.bybit_api_key, api_secret=self.bybit_api_secret)
        self.binance_session = Spot()
        logging.basicConfig(level=logging.INFO)

    @staticmethod
    def datetime_to_unix(date):
        """Convert a datetime object to a Unix timestamp."""
        return int(date.timestamp())

    def _fetch_glassnode_data(self, endpoint, start, end, frequency):
        params = {
            'a': 'BTC',
            's': self.datetime_to_unix(start),
            'u': self.datetime_to_unix(end),
            'i': frequency,
            'f': 'JSON',
            'api_key': self.glassnode_api_key  
        }
        
        base_url = 'https://api.glassnode.com/v1/metrics'
        url = f"{base_url}/{endpoint}"
        name = re.search(r'/([^/]*)$', endpoint).group(1)

        for attempt in range(3):
            try:
                response = requests.get(url, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    df = pd.DataFrame(data)
                    if 't' in df.columns:
                        df['t'] = pd.to_datetime(df['t'], unit='s')
                    df.rename(columns={'v': name}, inplace=True)
                    logging.info(f"Successfully fetched data for endpoint: {endpoint}")
                    return df
                else:
                    logging.error(f"Failed to fetch data: {response.status_code} - {response.text}")
            except Exception as e:
                logging.error(f"Attempt {attempt + 1}: Exception occurred while fetching data: {e}")

        raise Exception(f"Failed to fetch data after 3 attempts for endpoint: {endpoint}")
    
    def _fetch_and_merge_glassnode_data(self, endpoints, start, end, frequency):
        data_frames = []

        for endpoint in endpoints:
            try:
                df = self._fetch_glassnode_data(endpoint, start, end, frequency)
                if df is not None and not df.empty:
                    data_frames.append(df.set_index('t'))
                else:
                    logging.warning(f"No data found for endpoint: {endpoint}")
            except Exception as e:
                logging.error(f"Failed to fetch data for endpoint: {endpoint} with error: {e}")

        if data_frames:
            merged_df = pd.concat(data_frames, axis=1, join='outer')
            merged_df.reset_index(inplace=True)
            merged_df.set_index('t', inplace=True)
            logging.info("Successfully merged data from all endpoints.")
            return merged_df
        else:
            logging.warning("No data frames to merge.")
            return None
    
    def get_trigger_data(self, start, end, frequency='1h'):
        short_term_endpoints = [
            os.getenv('BTC_PRICE'),
            os.getenv('SSR'),
            os.getenv('CVD'),
            os.getenv('SUPPLY_IN_PROFIT'),
            os.getenv('BTC_HASH_RATE')
        ]
        return self._fetch_and_merge_glassnode_data(short_term_endpoints, start, end, frequency)

    def get_context_data(self, start, end, frequency='24h'):
        contextual_endpoints = [
            os.getenv('BTC_PRICE'),
            os.getenv('BTC_REALIZED_PRICE'),
            os.getenv('PUELL_MULTIPLE'),
            os.getenv('MVRV_Z_SCORE'),
            os.getenv('ENTITY_ADJ_NUPL'),
            os.getenv('ENTITY_ADJ_DORMANCY_FLOW'),
            os.getenv('SUPPLY_IN_PROFIT')
        ]
        return self._fetch_and_merge_glassnode_data(contextual_endpoints, start, end, frequency)

    def get_bybit_data(self, symbol='BTCUSDT', interval=60, start_time=None, end_time=None):
        try:
            start_time_unix = self.datetime_to_unix(start_time) * 1000 if start_time else None
            end_time_unix = self.datetime_to_unix(end_time) * 1000 if end_time else None
            all_data = []
            fetched_rows = 0

            while end_time_unix > start_time_unix:
                params = {
                    'category': 'spot',
                    'symbol': symbol,
                    'interval': interval,
                    'start': start_time_unix,
                    'end': end_time_unix,
                    'limit': 1000
                }

                response = self.bybit_session.get_kline(**params)

                if response['retCode'] == 0:
                    data = response['result']['list']
                    if not data:
                        logging.info("No more data returned.")
                        break

                    df = pd.DataFrame(data, columns=['start_time', 'open', 'high', 'low', 'close', 'volume', 'turnover'])
                    df['start_time'] = pd.to_datetime(df['start_time'], unit='ms')
                    all_data.append(df)
                    fetched_rows += len(df)

                    logging.info(f"Fetched {len(df)} rows, total fetched: {fetched_rows}")

                    if len(df) < 1000:
                        logging.info("Fetched less than 1000 rows, ending loop.")
                        break  # All data within the range has been retrieved

                    # Update end_time_unix for the next call to avoid overlapping data
                    earliest_timestamp = df['start_time'].iloc[-1].timestamp() * 1000
                    end_time_unix = int(earliest_timestamp) - (interval * 60 * 1000)  # Decrement by interval in milliseconds
                    #logging.info(f"Updated end_time_unix to {end_time_unix} for the next API call.")

                    # Wait for 5 seconds before the next API call
                    time.sleep(1)

                else:
                    logging.error(f"Failed to fetch ByBit data: {response['retMsg']}")
                    break

            if all_data:
                # Concatenate all data frames
                final_df = pd.concat(all_data).drop_duplicates().sort_index()
                final_df.set_index('start_time', inplace=True)
                final_df.drop(columns='volume', inplace=True)
                final_df = final_df.astype(float)  # Convert all columns to float
                #logging.info(f"Successfully fetched {fetched_rows} rows of ByBit data.")
                return final_df
            
            else:
                logging.warning("No data was fetched from ByBit.")
                return None

        except Exception as e:
            logging.error(f"Exception occurred while fetching ByBit data: {e}")
            return None

    def get_binance_data(self, symbol='BTCUSDT', interval='1h', start_time=None, end_time=None):
            start_time_unix = self.datetime_to_unix(start_time) * 1000 if start_time else None
            end_time_unix = self.datetime_to_unix(end_time) * 1000 if end_time else None
            all_data = []
            fetched_rows = 0

            while start_time_unix < end_time_unix:
                klines = self.binance_session.klines(
                    symbol=symbol,
                    interval=interval,
                    startTime=start_time_unix,
                    endTime=end_time_unix,
                    limit=1000
                )

                if not klines:
                    logging.info("No more data returned.")
                    break

                data = []
                for kline in klines:
                    data.append({
                        'start_time': pd.to_datetime(kline[0], unit='ms'),
                        'open': float(kline[1]),
                        'high': float(kline[2]),
                        'low': float(kline[3]),
                        'close': float(kline[4]),
                        'volume': float(kline[5])
                    })

                df = pd.DataFrame(data)
                all_data.append(df)
                fetched_rows += len(df)

                logging.info(f"Fetched {len(df)} rows, total fetched: {fetched_rows}")

                if len(df) < 1000:
                    logging.info("Fetched less than 1000 rows, ending loop.")
                    break  # All data within the range has been retrieved

                # Update start_time_unix for the next call to avoid overlapping data
                last_timestamp = df['start_time'].iloc[-1].timestamp() * 1000
                start_time_unix = int(last_timestamp) + (3600 * 1000)  # Increment by 1 hour in milliseconds
                #logging.info(f"Updated start_time_unix to {start_time_unix} for the next API call.")

                # Wait for 5 seconds before the next API call
                time.sleep(1)

            if all_data:
                # Concatenate all data frames
                final_df = pd.concat(all_data).drop_duplicates().sort_index()
                final_df.set_index('start_time', inplace=True)
                #xfinal_df.drop(columns='volume', inplace=True)
                final_df = final_df.astype(float)  # Convert all columns to float
                #logging.info(f"Successfully fetched {fetched_rows} rows of Binance data.")
                return final_df
            else:
                logging.warning("No data was fetched from Binance.")
                return None


    def compute_triggers(self, start, end):
        start = datetime.strptime(start, '%Y-%m-%d')
        end = datetime.strptime(end, '%Y-%m-%d')
        
        # Retrieve trigger data and ByBit data
        trigger_data = self.get_trigger_data((start - timedelta(hours=8640)), end)
        binance_data = self.get_binance_data(start_time=(start - timedelta(hours=8640/2)), end_time=end)
        binance_data.rename_axis('t', inplace=True)
        
        
        # Merge ByBit data with trigger data
        if binance_data is not None:
            trigger_data = trigger_data.merge(binance_data, left_index=True, right_index=True, how='outer')
        
        
        # Calculate indicators
        trigger_data['rsi_ssr_smoothed'] = ta.ema(ta.rsi(trigger_data['ssr_oscillator'], length=336), length=800)
        trigger_data['rsi_ssr_smoothed_median'] = trigger_data['rsi_ssr_smoothed'].rolling(window=240).median()
        trigger_data['srs'] = trigger_data['rsi_ssr_smoothed'] - trigger_data['rsi_ssr_smoothed_median']
        trigger_data['hash_30'] = trigger_data['hash_rate_mean'].rolling(window=30).mean()
        trigger_data['hash_60'] = trigger_data['hash_rate_mean'].rolling(window=60).mean()
        trigger_data['hash_ribbon'] = trigger_data['hash_30'] - trigger_data['hash_60']
        trigger_data['cvd_ema24'] = ta.ema(trigger_data['spot_cvd_sum'], length=24)
        
        
        
        # Clean up and filter data
        trigger_data.drop(columns=['ssr_oscillator', 'profit_relative', 'price_usd_close', 'rsi_ssr_smoothed', 
                                   'rsi_ssr_smoothed_median', 'hash_rate_mean', 'hash_30', 'hash_60', 'spot_cvd_sum'], inplace=True)
        
        trigger_data = trigger_data[trigger_data.index >= start]
        
        return trigger_data    
    
    @staticmethod
    def determine_context(row):
        if row['bottom_detection'] != 0 and (row['top_detection'] == 0 or row.name < row.index[row['top_detection'] != 0].max()):
            return int(1)
        elif row['top_detection'] != 0 and (row['bottom_detection'] == 0 or row.name < row.index[row['bottom_detection'] != 0].max()):
            return int(0)
        else:
            return np.nan

    def compute_context(self, start, end):
        
        start = datetime.strptime(start, '%Y-%m-%d')
        end = datetime.strptime(end, '%Y-%m-%d')
        
        # Retrieve context data
        context_data = self.get_context_data(pd.to_datetime('2011-08-1'), end)

        # Market condition calculations
        context_data['28d_mkt_gradient'] = (context_data['price_usd_close'].diff(28) - context_data['price_realized_usd'].diff(28) - 
                                            (context_data['price_usd_close'].diff(28) - context_data['price_realized_usd'].diff(28)).expanding().mean()) / \
                                            (context_data['price_usd_close'].diff(28) - context_data['price_realized_usd'].diff(28)).expanding().std()
        
        context_data['mayer_multiple'] = context_data['price_usd_close'] / context_data['price_usd_close'].rolling(200).mean()
        context_data['price_profit_corr'] = context_data['price_usd_close'].rolling(7).corr(context_data['profit_relative'])

        # Detect market tops and bottoms
        context_data['top_detection'] = (np.where(context_data['mvrv_z_score'] > 3.8, 1, 0) * 
                                         np.where(context_data['mayer_multiple'] >= 1.3, 1, 0) *
                                         np.where(context_data['net_unrealized_profit_loss_account_based'] >= 0.6, 1, 0) *
                                         np.where(context_data['28d_mkt_gradient'] >= 7, 1, 0)) * context_data['price_usd_close']
        
        context_data['bottom_detection'] = (np.where(context_data['mvrv_z_score'] <= 0, 1, 0) * 
                                            np.where(context_data['mayer_multiple'] <= 0.8, 1, 0) *
                                            np.where(context_data['price_usd_close'] <= context_data['price_realized_usd'], 1, 0) *
                                            np.where(context_data['net_unrealized_profit_loss_account_based'] <= 0, 1, 0) *
                                            np.where(context_data['puell_multiple'] <= 0.5, 1, 0) *
                                            np.where(context_data['dormancy_flow'] <= 200000, 1, 0)) * context_data['price_usd_close']

        # Apply context determination
        context_data['context'] = context_data.apply(self.determine_context, axis=1)
        context_data['context'].fillna(method='ffill', inplace=True)
        context_data.drop(columns=['top_detection', 'bottom_detection', 'price_usd_close'], inplace=True)
        context_data = context_data[context_data.index >= start]
        
        return context_data

    def get_data(self, start, end, contextualize=True):
        
        trigger_data = self.compute_triggers(start=start, end=end)
        context_data = self.compute_context(start=start,end=end)
    
        trigger_data.reset_index(inplace=True)
        context_data.reset_index(inplace=True)
        context_data['t'] = context_data['t'].dt.tz_localize(None)  # Ensure no timezone differences
        
        # Merge the datasets
        if contextualize:
            full_data = pd.merge_asof(trigger_data, context_data[['t', 'context']], on='t', direction='forward')
        else: 
            full_data = pd.merge_asof(trigger_data, context_data, on='t', direction='forward')
            full_data.drop(columns='context', inplace=True)
        
        full_data.ffill(inplace=True)
        full_data.set_index('t', inplace=True)
   
        return full_data
    
 
