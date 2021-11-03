from configparser import ConfigParser

import pandas as pd
from binance.client import Client

pairs_data = {'BTCUSDT': {'PRICE_FILTER': '0.01', 'LOT_SIZE': '0.001', 'MARKET_LOT_SIZE': '0.001'}, 'ETHUSDT': {'PRICE_FILTER': '0.01', 'LOT_SIZE': '0.001', 'MARKET_LOT_SIZE': '0.001'}, 'BCHUSDT': {'PRICE_FILTER': '0.01', 'LOT_SIZE': '0.001', 'MARKET_LOT_SIZE': '0.001'}, 'XRPUSDT': {'PRICE_FILTER': '0.0001', 'LOT_SIZE': '0.1', 'MARKET_LOT_SIZE': '0.1'}, 'EOSUSDT': {'PRICE_FILTER': '0.001', 'LOT_SIZE': '0.1', 'MARKET_LOT_SIZE': '0.1'}, 'LTCUSDT': {'PRICE_FILTER': '0.01', 'LOT_SIZE': '0.001', 'MARKET_LOT_SIZE': '0.001'}, 'TRXUSDT': {'PRICE_FILTER': '0.00001', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, 'ETCUSDT': {'PRICE_FILTER': '0.001', 'LOT_SIZE': '0.01', 'MARKET_LOT_SIZE': '0.01'}, 'LINKUSDT': {'PRICE_FILTER': '0.001', 'LOT_SIZE': '0.01', 'MARKET_LOT_SIZE': '0.01'}, 'XLMUSDT': {'PRICE_FILTER': '0.00001', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, 'ADAUSDT': {'PRICE_FILTER': '0.00010', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, 'XMRUSDT': {'PRICE_FILTER': '0.01', 'LOT_SIZE': '0.001', 'MARKET_LOT_SIZE': '0.001'}, 'DASHUSDT': {'PRICE_FILTER': '0.01', 'LOT_SIZE': '0.001', 'MARKET_LOT_SIZE': '0.001'}, 'ZECUSDT': {'PRICE_FILTER': '0.01', 'LOT_SIZE': '0.001', 'MARKET_LOT_SIZE': '0.001'}, 'XTZUSDT': {'PRICE_FILTER': '0.001', 'LOT_SIZE': '0.1', 'MARKET_LOT_SIZE': '0.1'}, 'BNBUSDT': {'PRICE_FILTER': '0.010', 'LOT_SIZE': '0.01', 'MARKET_LOT_SIZE': '0.01'}, 'ATOMUSDT': {'PRICE_FILTER': '0.001', 'LOT_SIZE': '0.01', 'MARKET_LOT_SIZE': '0.01'}, 'ONTUSDT': {'PRICE_FILTER': '0.0001', 'LOT_SIZE': '0.1', 'MARKET_LOT_SIZE': '0.1'}, 'IOTAUSDT': {'PRICE_FILTER': '0.0001', 'LOT_SIZE': '0.1', 'MARKET_LOT_SIZE': '0.1'}, 'BATUSDT': {'PRICE_FILTER': '0.0001', 'LOT_SIZE': '0.1', 'MARKET_LOT_SIZE': '0.1'}, 'VETUSDT': {'PRICE_FILTER': '0.000010', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, 'NEOUSDT': {'PRICE_FILTER': '0.001', 'LOT_SIZE': '0.01', 'MARKET_LOT_SIZE': '0.01'}, 'QTUMUSDT': {'PRICE_FILTER': '0.001', 'LOT_SIZE': '0.1', 'MARKET_LOT_SIZE': '0.1'}, 'IOSTUSDT': {'PRICE_FILTER': '0.000001', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, 'THETAUSDT': {'PRICE_FILTER': '0.0010', 'LOT_SIZE': '0.1', 'MARKET_LOT_SIZE': '0.1'}, 'ALGOUSDT': {'PRICE_FILTER': '0.0001', 'LOT_SIZE': '0.1', 'MARKET_LOT_SIZE': '0.1'}, 'ZILUSDT': {'PRICE_FILTER': '0.00001', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, 'KNCUSDT': {'PRICE_FILTER': '0.00100', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, 'ZRXUSDT': {'PRICE_FILTER': '0.0001', 'LOT_SIZE': '0.1', 'MARKET_LOT_SIZE': '0.1'}, 'COMPUSDT': {'PRICE_FILTER': '0.01', 'LOT_SIZE': '0.001', 'MARKET_LOT_SIZE': '0.001'}, 'OMGUSDT': {'PRICE_FILTER': '0.0001', 'LOT_SIZE': '0.1', 'MARKET_LOT_SIZE': '0.1'}, 'DOGEUSDT': {'PRICE_FILTER': '0.000010', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, 'SXPUSDT': {'PRICE_FILTER': '0.0001', 'LOT_SIZE': '0.1', 'MARKET_LOT_SIZE': '0.1'}, 'KAVAUSDT': {'PRICE_FILTER': '0.0001', 'LOT_SIZE': '0.1', 'MARKET_LOT_SIZE': '0.1'}, 'BANDUSDT': {'PRICE_FILTER': '0.0001', 'LOT_SIZE': '0.1', 'MARKET_LOT_SIZE': '0.1'}, 'RLCUSDT': {'PRICE_FILTER': '0.0001', 'LOT_SIZE': '0.1', 'MARKET_LOT_SIZE': '0.1'}, 'WAVESUSDT': {'PRICE_FILTER': '0.0010', 'LOT_SIZE': '0.1', 'MARKET_LOT_SIZE': '0.1'}, 'MKRUSDT': {'PRICE_FILTER': '0.10', 'LOT_SIZE': '0.001', 'MARKET_LOT_SIZE': '0.001'}, 'SNXUSDT': {'PRICE_FILTER': '0.001', 'LOT_SIZE': '0.1', 'MARKET_LOT_SIZE': '0.1'}, 'DOTUSDT': {'PRICE_FILTER': '0.001', 'LOT_SIZE': '0.1', 'MARKET_LOT_SIZE': '0.1'}, 'DEFIUSDT': {'PRICE_FILTER': '0.1', 'LOT_SIZE': '0.001', 'MARKET_LOT_SIZE': '0.001'}, 'YFIUSDT': {'PRICE_FILTER': '1', 'LOT_SIZE': '0.001', 'MARKET_LOT_SIZE': '0.001'}, 'BALUSDT': {'PRICE_FILTER': '0.001', 'LOT_SIZE': '0.1', 'MARKET_LOT_SIZE': '0.1'}, 'CRVUSDT': {'PRICE_FILTER': '0.001', 'LOT_SIZE': '0.1', 'MARKET_LOT_SIZE': '0.1'}, 'TRBUSDT': {'PRICE_FILTER': '0.010', 'LOT_SIZE': '0.1', 'MARKET_LOT_SIZE': '0.1'}, 'YFIIUSDT': {'PRICE_FILTER': '0.1', 'LOT_SIZE': '0.001', 'MARKET_LOT_SIZE': '0.001'}, 'RUNEUSDT': {'PRICE_FILTER': '0.0010', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, 'SUSHIUSDT': {'PRICE_FILTER': '0.0010', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, 'SRMUSDT': {'PRICE_FILTER': '0.0010', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, 'BZRXUSDT': {'PRICE_FILTER': '0.0001', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, 'EGLDUSDT': {'PRICE_FILTER': '0.010', 'LOT_SIZE': '0.1', 'MARKET_LOT_SIZE': '0.1'}, 'SOLUSDT': {'PRICE_FILTER': '0.0010', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, 'ICXUSDT': {'PRICE_FILTER': '0.0001', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, 'STORJUSDT': {'PRICE_FILTER': '0.0001', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, 'BLZUSDT': {'PRICE_FILTER': '0.00001', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, 'UNIUSDT': {'PRICE_FILTER': '0.0010', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, 'AVAXUSDT': {'PRICE_FILTER': '0.0010', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, 'FTMUSDT': {'PRICE_FILTER': '0.000010', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, 'HNTUSDT': {'PRICE_FILTER': '0.0010', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, 'ENJUSDT': {'PRICE_FILTER': '0.00010', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, 'FLMUSDT': {'PRICE_FILTER': '0.0001', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, 'TOMOUSDT': {'PRICE_FILTER': '0.0001', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, 'RENUSDT': {'PRICE_FILTER': '0.00001', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, 'KSMUSDT': {'PRICE_FILTER': '0.010', 'LOT_SIZE': '0.1', 'MARKET_LOT_SIZE': '0.1'}, 'NEARUSDT': {'PRICE_FILTER': '0.0001', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, 'AAVEUSDT': {'PRICE_FILTER': '0.010', 'LOT_SIZE': '0.1', 'MARKET_LOT_SIZE': '0.1'}, 'FILUSDT': {'PRICE_FILTER': '0.001', 'LOT_SIZE': '0.1', 'MARKET_LOT_SIZE': '0.1'}, 'RSRUSDT': {'PRICE_FILTER': '0.000001', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, 'LRCUSDT': {'PRICE_FILTER': '0.00001', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, 'MATICUSDT': {'PRICE_FILTER': '0.00010', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, 'OCEANUSDT': {'PRICE_FILTER': '0.00001', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, 'CVCUSDT': {'PRICE_FILTER': '0.00001', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, 'BELUSDT': {'PRICE_FILTER': '0.00010', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, 'CTKUSDT': {'PRICE_FILTER': '0.00100', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, 'AXSUSDT': {'PRICE_FILTER': '0.01000', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, 'ALPHAUSDT': {'PRICE_FILTER': '0.00010', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, 'ZENUSDT': {'PRICE_FILTER': '0.001', 'LOT_SIZE': '0.1', 'MARKET_LOT_SIZE': '0.1'}, 'SKLUSDT': {'PRICE_FILTER': '0.00001', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, 'GRTUSDT': {'PRICE_FILTER': '0.00001', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, '1INCHUSDT': {'PRICE_FILTER': '0.0001', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, 'BTCBUSD': {'PRICE_FILTER': '0.1', 'LOT_SIZE': '0.001', 'MARKET_LOT_SIZE': '0.001'}, 'AKROUSDT': {'PRICE_FILTER': '0.00001', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, 'CHZUSDT': {'PRICE_FILTER': '0.00001', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, 'SANDUSDT': {'PRICE_FILTER': '0.00001', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, 'ANKRUSDT': {'PRICE_FILTER': '0.000010', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, 'LUNAUSDT': {'PRICE_FILTER': '0.0010', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, 'BTSUSDT': {'PRICE_FILTER': '0.00001', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, 'LITUSDT': {'PRICE_FILTER': '0.001', 'LOT_SIZE': '0.1', 'MARKET_LOT_SIZE': '0.1'}, 'UNFIUSDT': {'PRICE_FILTER': '0.001', 'LOT_SIZE': '0.1', 'MARKET_LOT_SIZE': '0.1'}, 'DODOUSDT': {'PRICE_FILTER': '0.001', 'LOT_SIZE': '0.1', 'MARKET_LOT_SIZE': '0.1'}, 'REEFUSDT': {'PRICE_FILTER': '0.000001', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, 'RVNUSDT': {'PRICE_FILTER': '0.00001', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, 'SFPUSDT': {'PRICE_FILTER': '0.0001', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, 'XEMUSDT': {'PRICE_FILTER': '0.0001', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, 'BTCSTUSDT': {'PRICE_FILTER': '0.001', 'LOT_SIZE': '0.1', 'MARKET_LOT_SIZE': '0.1'}, 'COTIUSDT': {'PRICE_FILTER': '0.00001', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, 'CHRUSDT': {'PRICE_FILTER': '0.0001', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, 'MANAUSDT': {'PRICE_FILTER': '0.0001', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, 'ALICEUSDT': {'PRICE_FILTER': '0.001', 'LOT_SIZE': '0.1', 'MARKET_LOT_SIZE': '0.1'}, 'HBARUSDT': {'PRICE_FILTER': '0.00001', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, 'ONEUSDT': {'PRICE_FILTER': '0.00001', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, 'LINAUSDT': {'PRICE_FILTER': '0.00001', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, 'STMXUSDT': {'PRICE_FILTER': '0.00001', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, 'DENTUSDT': {'PRICE_FILTER': '0.000001', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, 'CELRUSDT': {'PRICE_FILTER': '0.00001', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, 'HOTUSDT': {'PRICE_FILTER': '0.000001', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, 'MTLUSDT': {'PRICE_FILTER': '0.0001', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, 'OGNUSDT': {'PRICE_FILTER': '0.0001', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, 'BTTUSDT': {'PRICE_FILTER': '0.000001', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, 'NKNUSDT': {'PRICE_FILTER': '0.00001', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, 'SCUSDT': {'PRICE_FILTER': '0.000001', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, 'DGBUSDT': {'PRICE_FILTER': '0.00001', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, '1000SHIBUSDT': {'PRICE_FILTER': '0.000001', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, 'ICPUSDT': {'PRICE_FILTER': '0.01', 'LOT_SIZE': '0.01', 'MARKET_LOT_SIZE': '0.01'}, 'BAKEUSDT': {'PRICE_FILTER': '0.0001', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, 'GTCUSDT': {'PRICE_FILTER': '0.001', 'LOT_SIZE': '0.1', 'MARKET_LOT_SIZE': '0.1'}, 'ETHBUSD': {'PRICE_FILTER': '0.01', 'LOT_SIZE': '0.001', 'MARKET_LOT_SIZE': '0.001'}, 'BTCUSDT_210924': {'PRICE_FILTER': '0.1', 'LOT_SIZE': '0.001', 'MARKET_LOT_SIZE': '0.001'}, 'ETHUSDT_210924': {'PRICE_FILTER': '0.01', 'LOT_SIZE': '0.001', 'MARKET_LOT_SIZE': '0.001'}, 'BTCDOMUSDT': {'PRICE_FILTER': '0.1', 'LOT_SIZE': '0.001', 'MARKET_LOT_SIZE': '0.001'}, 'KEEPUSDT': {'PRICE_FILTER': '0.0001', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, 'TLMUSDT': {'PRICE_FILTER': '0.0001', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, 'BNBBUSD': {'PRICE_FILTER': '0.010', 'LOT_SIZE': '0.01', 'MARKET_LOT_SIZE': '0.01'}, 'ADABUSD': {'PRICE_FILTER': '0.00010', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, 'XRPBUSD': {'PRICE_FILTER': '0.0001', 'LOT_SIZE': '0.1', 'MARKET_LOT_SIZE': '0.1'}, 'IOTXUSDT': {'PRICE_FILTER': '0.00001', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, 'DOGEBUSD': {'PRICE_FILTER': '0.000010', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, 'AUDIOUSDT': {'PRICE_FILTER': '0.0001', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, 'RAYUSDT': {'PRICE_FILTER': '0.001', 'LOT_SIZE': '0.1', 'MARKET_LOT_SIZE': '0.1'}, 'C98USDT': {'PRICE_FILTER': '0.0001', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, 'MASKUSDT': {'PRICE_FILTER': '0.0001', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, 'ATAUSDT': {'PRICE_FILTER': '0.0001', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, 'SOLBUSD': {'PRICE_FILTER': '0.0010', 'LOT_SIZE': '1', 'MARKET_LOT_SIZE': '1'}, 'FTTBUSD': {'PRICE_FILTER': '0.001', 'LOT_SIZE': '0.1', 'MARKET_LOT_SIZE': '0.1'}}
all_pairs = ['BTCUSDT', 'ETHUSDT', 'DGBUSDT', '1INCHUSDT', 'DEFIUSDT', 'ANKRUSDT', 'KNCUSDT', 'HOTUSDT', 'ZILUSDT', 'LTCUSDT', 'BATUSDT', 'REEFUSDT', 'AKROUSDT', 'ONTUSDT', 'TRBUSDT', 'BELUSDT', 'ATOMUSDT', 'RENUSDT', 'ADAUSDT', 'LRCUSDT', 'BTTUSDT', 'DOGEUSDT', 'SOLUSDT', 'DOTUSDT', 'NKNUSDT', 'STMXUSDT', 'XEMUSDT', 'ICXUSDT', 'SUSHIUSDT', 'DASHUSDT', 'IOTAUSDT', 'IOSTUSDT', 'MKRUSDT', 'WAVESUSDT', 'TLMUSDT', 'CRVUSDT', 'EOSUSDT', 'NEARUSDT', 'ZENUSDT', 'YFIIUSDT', 'LINKUSDT', 'UNFIUSDT', 'BANDUSDT', 'TRXUSDT', 'DENTUSDT', 'RSRUSDT', 'EGLDUSDT', 'SANDUSDT', 'ALPHAUSDT', 'LUNAUSDT', 'MANAUSDT', 'GTCUSDT', 'MATICUSDT', 'KEEPUSDT', 'XMRUSDT', 'ALICEUSDT', 'OMGUSDT', 'IOTXUSDT', 'KAVAUSDT', 'AAVEUSDT', 'ONEUSDT', 'ALGOUSDT', 'COMPUSDT', 'YFIUSDT', 'XRPUSDT', 'GRTUSDT', 'BNBUSDT', 'RVNUSDT', 'VETUSDT', 'SXPUSDT', 'CHRUSDT', 'ZRXUSDT', 'DODOUSDT', 'BTSUSDT', 'LITUSDT', 'SKLUSDT', 'MTLUSDT', 'BLZUSDT', 'HBARUSDT', 'COTIUSDT', 'KSMUSDT', 'HNTUSDT', 'QTUMUSDT', 'BAKEUSDT', 'FILUSDT', 'OCEANUSDT', 'FTMUSDT', 'BZRXUSDT', 'NEOUSDT', 'SNXUSDT', 'RLCUSDT', 'AUDIOUSDT', 'THETAUSDT', 'CVCUSDT', 'CELRUSDT', 'STORJUSDT', 'FLMUSDT', 'ZECUSDT', 'SFPUSDT', 'UNIUSDT', 'ENJUSDT', 'ETCUSDT', 'CTKUSDT', 'XTZUSDT', 'SCUSDT', '1000SHIBUSDT', 'RAYUSDT', 'RUNEUSDT', 'XLMUSDT', 'ICPUSDT', 'SRMUSDT', 'LINAUSDT', 'CHZUSDT', 'BALUSDT', 'OGNUSDT', 'AXSUSDT', 'AVAXUSDT', 'TOMOUSDT', 'BCHUSDT']

config = ConfigParser()
config.read_file(open('config.cfg'))
api_key_v = config.get('BINANCE', 'API_KEY_V')
api_secret_v = config.get('BINANCE', 'API_SECRET_V')
api_key_n = config.get('BINANCE', 'API_KEY_N')
api_secret_n = config.get('BINANCE', 'API_SECRET_N')
api_key_d = config.get('BINANCE', 'API_KEY_D')
api_secret_d = config.get('BINANCE', 'API_SECRET_D')

client_v = Client(api_key_v, api_secret_v)
client_n = Client(api_key_n, api_secret_n)
client_d = Client(api_key_d, api_secret_d)




class Pair:
    def __init__(self, symbol):
        self.symbol = symbol
        self.price_filter = float(pairs_data[symbol]['PRICE_FILTER'])
        self.lot_size = float(pairs_data[symbol]['LOT_SIZE'])
        self.market_lot_size = float(pairs_data[symbol]['MARKET_LOT_SIZE'])
        self.candles_5m = pd.DataFrame()
        self.candles_15m = pd.DataFrame()
        self.candles_1h = pd.DataFrame()
        self.candles_4h = pd.DataFrame()
        self.trend_5m = pd.DataFrame()
        self.trend_15m = pd.DataFrame()
        self.trend_1h = pd.DataFrame()
        self.trend_4h = pd.DataFrame()
        self.in_trade = False
        self.trade_data = {}

    def put_data(self, trade_data: dict):
        self.trade_data = trade_data

    def extract_data(self):
        return self.trade_data

    def clear_data(self):
        self.trade_data.clear()

    def put_candles(self, tf, candles):
        if tf == '5m':
            self.candles_5m = candles
        elif tf == '15m':
            self.candles_15m = candles
        elif tf == '1h':
            self.candles_1h = candles
        elif tf == '4h':
            self.candles_4h = candles
        else:
            print(f'unavailable timeframe')

    def put_trend(self, tf, trend):
        if tf == '15m':
            self.trend_15m = trend
        elif tf == '1h':
            self.trend_1h = trend
        elif tf == '4h':
            self.trend_4h = trend
        else:
            print(f'unavailable timeframe')

    def print(self):
        print(f'symbol: {self.symbol}')
        if not self.candles_4h.empty:
            print(f'candles 4h:\n{self.candles_4h.tail()}')
        if not self.candles_1h.empty:
            print(f'candles 1h:\n{self.candles_1h.tail()}')
        if not self.trend_1h.empty:
            print(f'trend 1h:\n{self.trend_1h}')
        if not self.trend_4h.empty:
            print(f'trend 4h:\n{self.trend_4h}')
        if self.in_trade:
            print(f'trading data:\n{self.trade_data}')

