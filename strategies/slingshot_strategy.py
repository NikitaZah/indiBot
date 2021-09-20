from indicators.slingshot import slingshot
import get
from indicators.lines import ewm
from data import client_v as client
from data import pairs_data
from tqdm import tqdm
import time

from binance.enums import *
from binance.helpers import round_step_size
from binance.client import Client

deposit = 997
dollars = 250
leverage = 5

trading_pairs = list()
order_pairs = list()


def slingshot_strategy():
    while True:
        start = time.time()

        volatile_pairs = get.pairs(client)
        trend_pairs = apply_status(volatile_pairs)

        for pair in tqdm(volatile_pairs, desc='checking volatile pairs'):
            candles = get.candles(client, pair, '1h', limit=1000)
            if intersection(pair, trend_pairs[pair], candles):
                create_order(pair, trend_pairs[pair], candles)
        refresh_time = get.candles(client, 'BTCUSDT', '1h', limit=10)['close_time'][-1]
        check_orders(refresh_time)
        print(f'time: {round(time.time()-start, 1)}')


def apply_status(pairs: list):
    result = dict()
    for pair in tqdm(pairs, desc='applying status to pairs'):
        pair_data = get.candles(client, pair, '4h', limit=1000)
        pair_trend = slingshot(pair_data['close_price'])[-1]
        result[pair] = pair_trend
    return result


def intersection(pair: str, trend: int, pair_data: dict):
    last_trend = slingshot(pair_data['close_price'])[-2]
    new_trend = slingshot(pair_data['close_price'])[-1]

    if last_trend * new_trend < 0:
        print(f'\n{pair}: intersection found!')
        if new_trend == trend:
            return True
        else:
            print('intersection is countertrend')
    return False


def define_script(candles: dict, trend: int):
    if trend == 1:
        ema = ewm(candles['close_price'], 38)
        if candles['open_price'][-1] < ema[-1]:
            return 1
        elif (candles['open_price'][-1] - ema[-1])/candles['open_price'][-1] * 100 < 2:
            return 2
        else:
            return 3
    if trend == -1:
        ema = ewm(candles['close_price'], 38)
        if candles['open_price'][-1] > ema[-1]:
            return 1
        elif (ema[-1] - candles['open_price'][-1]) / candles['open_price'][-1] * 100 < 2:
            return 2
        else:
            return 3


def create_order(symbol: str, order_kind: int, candles: dict):
    lev = client.futures_change_leverage(symbol=symbol, leverage=leverage)
    script = define_script(candles, order_kind)
    price = candles['open_price'][-1]
    if script == 1:
        tp = price + 0.08*price if order_kind == 1 else price - 0.08*price
        trailing = price + 0.05 * price if order_kind == 1 else price - 0.05 * price
        sl = price - 0.03*price if order_kind == 1 else price + 0.03*price

        tp = round_step_size(tp, float(pairs_data[symbol]['PRICE_FILTER']))
        trailing = round_step_size(trailing, float(pairs_data[symbol]['PRICE_FILTER']))
        sl = round_step_size(sl, float(pairs_data[symbol]['PRICE_FILTER']))

        result = place_order(symbol, price, tp, sl, order_kind)
    if script == 2:
        tp = price + 0.06 * price if order_kind == 1 else price - 0.06 * price
        sl = price - 0.05 * price if order_kind == 1 else price + 0.05 * price

        tp = round_step_size(tp, float(pairs_data[symbol]['PRICE_FILTER']))
        sl = round_step_size(sl, float(pairs_data[symbol]['PRICE_FILTER']))
        result = place_order(symbol, price, tp, sl, order_kind)

    if script == 3:
        ema = ewm(candles['close_price'], 38)
        limit_price = round_step_size(ema[-1], float(pairs_data[symbol]['PRICE_FILTER']))
        tp = limit_price + 0.08 * limit_price if order_kind == 1 else limit_price - 0.08 * limit_price
        sl = limit_price - 0.03 * limit_price if order_kind == 1 else limit_price + 0.03 * limit_price

        tp = round_step_size(tp, float(pairs_data[symbol]['PRICE_FILTER']))
        sl = round_step_size(sl, float(pairs_data[symbol]['PRICE_FILTER']))
        result = place_order(symbol, limit_price, tp, sl, order_kind, limit=True)

    if result:
        print(f'{symbol}: order created successfully:\norder kind: {order_kind}\nprice: {price}\nscript={script}\n')


def place_order(symbol: str, price: float, tp: float, sl: float, order_kind: int, order=None, limit=False, can_num=0):
    global trading_pairs, order_pairs
    qty = round_step_size(dollars * leverage / price, float(pairs_data[symbol]['MARKET_LOT_SIZE']))
    if order_kind == 1:
        if order is None:
            for i in range(30):
                try:
                    if not limit:
                        order = client.futures_create_order(symbol=symbol, side=Client.SIDE_BUY,
                                                            type=Client.ORDER_TYPE_MARKET, quantity=qty)
                    else:
                        order = client.futures_create_order(symbol=symbol, side=Client.SIDE_BUY, price=price,
                                                            timeInForce=TIME_IN_FORCE_GTC,
                                                            type=Client.ORDER_TYPE_LIMIT, quantity=qty)
                        order_pairs.append(dict(symbol=symbol, orderId=order['orderId'], candle=can_num))
                        return True
                    break
                except Exception as err:
                    print(f'cannot place market order. Error: {err}\n')
                    time.sleep(1)
                    if i == 29:
                        return False
        while True:
            try:
                sl_order = client.futures_create_order(symbol=symbol, side=Client.SIDE_SELL, stopPrice=sl,
                                                       closePosition=True, type=Client.FUTURE_ORDER_TYPE_STOP_MARKET)
                break
            except Exception as err:
                print(f'{symbol}: ATTENTION! Cannot place stop loss!')
        while True:
            try:
                tp_order = client.futures_create_order(symbol=symbol, side=Client.SIDE_SELL, stopPrice=tp,
                                                       closePosition=True,
                                                       type=Client.FUTURE_ORDER_TYPE_TAKE_PROFIT_MARKET)
                break
            except Exception as err:
                print(f'{symbol}: ATTENTION! Cannot place take profit!')
        trading_pairs.append(dict(symbol=symbol, orderId=order['orderId'], tpId=tp_order['orderId'],
                                  slId=sl_order['orderId']))
        return True
    else:
        if order is None:
            for i in range(30):
                try:
                    if not limit:
                        order = client.futures_create_order(symbol=symbol, side=Client.SIDE_SELL,
                                                            type=Client.ORDER_TYPE_MARKET, quantity=qty)
                    else:
                        order = client.futures_create_order(symbol=symbol, side=Client.SIDE_SELL, price=price,
                                                            timeInForce=TIME_IN_FORCE_GTC,
                                                            type=Client.ORDER_TYPE_LIMIT, quantity=qty)
                        order_pairs.append(dict(symbol=symbol, orderId=order['orderId'], candle=can_num))
                        return True
                    break
                except Exception as err:
                    print(f'cannot place market order. Error: {err}\n')
                    time.sleep(1)
                    if i == 29:
                        return False
        while True:
            try:
                sl_order = client.futures_create_order(symbol=symbol, side=Client.SIDE_BUY, stopPrice=sl,
                                                       closePosition=True, type=Client.FUTURE_ORDER_TYPE_STOP_MARKET)
                break
            except Exception as err:
                print(f'{symbol}: ATTENTION! Cannot place stop loss!\nerror: {err}')
        while True:
            try:
                tp_order = client.futures_create_order(symbol=symbol, side=Client.SIDE_BUY, stopPrice=tp,
                                                       closePosition=True,
                                                       type=Client.FUTURE_ORDER_TYPE_TAKE_PROFIT_MARKET)
                break
            except Exception as err:
                print(f'{symbol}: ATTENTION! Cannot place take profit!\nerror: {err}')
        trading_pairs.append(dict(symbol=symbol, orderId=order['orderId'], tpId=tp_order['orderId'],
                                  slId=sl_order['orderId']))
        return True


def check_orders(end_time: int):
    global trading_pairs, order_pairs
    while True:
        order_pairs_copy = order_pairs.copy()
        order_pairs.clear()
        for pair in order_pairs_copy:
            try:
                order = client.futures_get_order(symbol=pair['symbol'], orderId=pair['orderId'])
                if order['status'] == 'FILLED':
                    continue
                close = client.futures_cancel_order(symbol=pair['symbol'], orderId=pair['orderId'])
                candle_num = pair['candle'] + 1
                if candle_num > 10:
                    print(f'{pair["symbol"]}: failed to wait the touch. Eliminated')
                    continue
                order_kind = 1 if order['side'] == 'BUY' else -1
                candles = get.candles(client, pair['symbol'], '1h')
                ema = ewm(candles['close_price'], 38)[-1]
                limit_price = round_step_size(ema, float(pairs_data[pair['symbol']]['PRICE_FILTER']))
                tp = limit_price + 0.08 * limit_price if order_kind == 1 else limit_price - 0.08 * limit_price
                sl = limit_price - 0.03 * limit_price if order_kind == 1 else limit_price + 0.03 * limit_price

                tp = round_step_size(tp, float(pairs_data[pair['symbol']]['PRICE_FILTER']))
                sl = round_step_size(sl, float(pairs_data[pair['symbol']]['PRICE_FILTER']))
                res = place_order(pair['symbol'], limit_price, tp, sl, order_kind, limit=True, can_num=candle_num)
                if res:
                    print(f'{pair["symbol"]}: limit moved to price {limit_price}')
                else:
                    print(f'ATTENTION!!! {pair["symbol"]} is unclosed!!')
            except Exception as err:
                print(f'error during first limit orders check: {err}')
                order_pairs = order_pairs_copy.copy()
                order_pairs_copy.clear()
        print(f'order pairs:\n{order_pairs}\ntrading pairs:\n{trading_pairs}')
        try:
            while int(client.get_server_time()["serverTime"]) < end_time:
                print(f'waiting time left: {(end_time - int(client.get_server_time()["serverTime"]))/60000}min')
                if not order_pairs and not trading_pairs:
                    print('no current open orders found. sleeping...')
                    time.sleep((end_time - client.get_server_time()["serverTime"])/1000 - 0.5)
                    return
                for pair in order_pairs:
                    order = client.futures_get_order(symbol=pair['symbol'], orderId=pair['orderId'])
                    if order['status'] == 'FILLED':
                        price = float(order['price'])
                        if order['side'] == 'BUY':
                            order_kind = 1
                            tp = price + 0.08*price
                            sl = price - 0.03*price
                        else:
                            order_kind = -1
                            tp = price - 0.08 * price
                            sl = price + 0.03 * price
                        tp = round_step_size(tp, float(pairs_data[pair['symbol']]['PRICE_FILTER']))
                        sl = round_step_size(sl, float(pairs_data[pair['symbol']]['PRICE_FILTER']))
                        result = place_order(pair['symbol'], price, tp, sl, order_kind, order)
                        if result:
                            print(f'{pair["symbol"]}: order filled.\ntp = {tp}, sl = {sl}')
                            order_pairs.remove(pair)

                for pair in trading_pairs:
                    tp_order = client.futures_get_order(symbol=pair['symbol'], orderId=pair['tpId'])
                    sl_order = client.futures_get_order(symbol=pair['symbol'], orderId=pair['slId'])

                    close = None
                    if tp_order['status'] == 'FILLED':
                        close = client.futures_cancel_order(symbol=pair['symbol'], orderId=pair['slId'])
                        print(f'{pair["symbol"]}: take profit')
                    elif sl_order['status'] == 'FILLED':
                        close = client.futures_cancel_order(symbol=pair['symbol'], orderId=pair['tpId'])
                        print(f'{pair["symbol"]}: take profit')
                    if close:
                        trading_pairs.remove(pair)
                time.sleep(10)
            break

        except Exception as err:
            print(f'\nerror occurred during checking orders: {err}')
            for i in tqdm(range(15), desc='restarting'):
                time.sleep(1)
                continue
