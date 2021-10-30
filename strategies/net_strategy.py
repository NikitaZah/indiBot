import get
from binance.helpers import round_step_size
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException
from data import client_v as client
from data import pairs_data, all_pairs
from data import Pair
import time
import pandas as pd


tf = '15m'
symbol = '1000SHIBUSDT'
base_percent = 5
max_lines = 11


def net(diameter: float):
    pair = Pair(symbol=symbol)
    lev = client.futures_change_leverage(symbol=pair.symbol, leverage=20)
    if diameter:
        diameter /=100
    while True:
        acc_info = client.futures_account_information()
        total_balance = float(acc_info['totalWalletBalance'])
        base_bet = total_balance * base_percent/100
        pair.clear_data()

        if not diameter:
            candles = pd.DataFrame()
            while candles.empty:
                candles = get.candles(client, symbol=symbol, interval='15m', limit=100)

            max_volatility = (candles['high'].max() - candles['low'].min())/candles['low'].min()
            print(max_volatility)
            if 0.3 <= max_volatility:
                d = max_volatility/30
            elif 0.2 <= max_volatility < 0.3:
                d = max_volatility/20
            elif 0.1 <= max_volatility < 0.2:
                d = max_volatility/10   # net diameter
            else:
                print('too small volatility! Please choose another symbol')
                return 0
            print(f'our current diameter = {d * 100}%')

        trade_data = create_base_orders(pair, diameter, base_bet)
        if not trade_data:
            continue

        pair.put_data(trade_data)

        side = define_side(pair)
        if side == 'CANCELED':
            time.sleep(600)
            continue
        side = client.SIDE_BUY if side == 'BUY' else client.SIDE_SELL
        trade_data = create_net(pair, side, diameter)
        pair.clear_data()
        pair.put_data(trade_data)

        result = waiting_profit(pair, diameter, side)
        if result == 'FAIL':
            break


def create_base_orders(pair, diameter, base_bet):
    trades = None
    while not trades:
        try:
            trades = client.futures_recent_trades(symbol=pair.symbol, limit=10)
        except Exception as err:
            print(f'cant get trades: {err}')

    price = float(trades[-1]['price'])
    print(price)
    price_buy = round_step_size(price - diameter * price, pair.price_filter)
    price_sell = round_step_size(price + diameter * price, pair.price_filter)
    print(price_buy, price_sell)

    qty_buy = round_step_size(base_bet/price_buy, pair.market_lot_size)
    qty_sell = round_step_size(base_bet/price_sell, pair.market_lot_size)

    try:
        long = client.futures_create_order(symbol=pair.symbol, side=client.SIDE_BUY, price=price_buy,
                                           timeInForce=client.TIME_IN_FORCE_GTC,
                                           type=Client.ORDER_TYPE_LIMIT, quantity=qty_buy)
    except Exception as err:
        print(f'error during creating base long position:\n{err}\nbreaking up')
        return None

    try:
        short = client.futures_create_order(symbol=pair.symbol, side=client.SIDE_SELL, price=price_sell,
                                            timeInForce=client.TIME_IN_FORCE_GTC,
                                            type=Client.ORDER_TYPE_LIMIT, quantity=qty_sell)
    except Exception as err:
        print(f'error during creating base short position:\n{err}\nbreaking up')
        cancel = None
        while not cancel:
            try:
                cancel = client.futures_cancel_order(symbol=symbol, orderId=long['orderId'])
            except Exception as error:
                print(f'failed to cancel order after unsuccessful creating short order\nerror = {error}')
        return None

    trade_data = {'base_buy': long['orderId'], 'base_sell': short['orderId']}
    return trade_data


def define_side(pair):
    long = pair.trade_data['base_buy']
    short = pair.trade_data['base_sell']
    result = None
    while True:
        status_sell = None
        status_buy = None
        while not status_buy:
            try:
                status_buy = client.futures_get_order(symbol=pair.symbol, orderId=long)['status']
            except Exception as err:
                print(f'cant get status buy!\nerr={err}')
        while not status_sell:
            try:
                status_sell = client.futures_get_order(symbol=pair.symbol, orderId=short)['status']
            except Exception as err:
                print(f'cant get status sell!\nerr={err}')

        if status_buy == 'FILLED':
            print('we bought shiba!')
            result = client.SIDE_BUY
        elif status_sell == 'FILLED':
            print('we sold shiba!')
            result = client.SIDE_SELL
        elif status_buy == 'CANCELED' or status_sell == 'CANCELED':
            result = 'CANCELED'

        if result:
            try:
                cancel = client.futures_cancel_all_open_orders(symbol=pair.symbol)
            except Exception as err:
                print(f'failed to cancel all orders too. order during defining side\nerror = {err}')

            return result


def create_net(pair, side, diameter):
    net_orders = []
    close_side = client.SIDE_SELL if side == client.SIDE_BUY else client.SIDE_BUY
    if side == client.SIDE_BUY:
        first_pose = pair.trade_data['base_buy']
    else:
        first_pose = pair.trade_data['base_sell']
    net_orders.append(first_pose)
    while True:
        try:
            first_pose = client.futures_get_order(symbol=pair.symbol, orderId=first_pose)
            break
        except Exception as err:
            print(f'error occurred during getting first pose order\nerr={err}')
    print(first_pose)
    if side == client.SIDE_BUY:
        prices_net = [round_step_size(float(first_pose['avgPrice']) * (1 - i * diameter), pair.price_filter) for i in range(max_lines)]
    else:
        prices_net = [round_step_size(float(first_pose['avgPrice']) * (1 + i * diameter), pair.price_filter) for i in range(max_lines)]

    print(f'price net:\n{prices_net}')
    cum_quote = [float(first_pose['cumQuote'])]
    qty = [float(first_pose['executedQty'])]
    for i in range(1, max_lines-1):
        cum_quote.append(sum(cum_quote) * 1.01)
        quantity = cum_quote[i] / prices_net[i]
        qty.append(round_step_size(quantity, pair.market_lot_size) + 1)
    print(f'qty:\n{qty}')

    tp_price = (1+diameter) * float(first_pose['avgPrice']) if side == client.SIDE_BUY \
        else (1-diameter) * float(first_pose['avgPrice'])

    tp_price = round_step_size(tp_price, pair.price_filter)

    while True:
        try:
            tp = client.futures_create_order(symbol=pair.symbol, side=close_side, stopPrice=tp_price,
                                             type=Client.FUTURE_ORDER_TYPE_TAKE_PROFIT_MARKET, closePosition=True)
            break
        except Exception as err:
            print(f'cant place take profit!\nerror = {err}')

    for i in range(1, max_lines-1):
        order = None
        for j in range(3):
            try:
                order = client.futures_create_order(symbol=pair.symbol, side=side, price=prices_net[i], quantity=qty[i],
                                                    timeInForce=client.TIME_IN_FORCE_GTC, type=Client.ORDER_TYPE_LIMIT)
                break
            except Exception as err:
                print(f'cant place {i+1} order\nerror={err}')
                time.sleep(1)
                continue
        if not order:
            print(f'there will be only {i} lines net!')
            break
        net_orders.append(order['orderId'])
    trade_data = {'net': net_orders, 'tp': tp['orderId'], 'prices': prices_net}
    print(f'we created net! {trade_data}')
    return trade_data


def waiting_profit(pair, diameter, side):
    close_side = client.SIDE_SELL if side == client.SIDE_BUY else client.SIDE_BUY
    line = 1
    max_line = len(pair.trade_data['net'])
    tp_id = pair.trade_data['tp']

    while True:
        while True:
            try:
                tp = client.futures_get_order(symbol=pair.symbol, orderId=tp_id)
                tp_price_new = pair.trade_data['prices'][line-1]
                break
            except Exception as err:
                print(f'cant check take profit\nerror = {err}')

        if tp['status'] == 'FILLED':
            print('yeeeah got monney')
            while True:
                try:
                    cancel = client.futures_cancel_all_open_orders(symbol=pair.symbol)
                    break
                except Exception as err:
                    print(f'failed to close all open orders\nerror = {err}')
            return 'PROFIT'

        while True:
            try:
                order = client.futures_get_order(symbol=pair.symbol, orderId=pair.trade_data['net'][line])
                break
            except Exception as err:
                print(f'cant get order\nerror={err}')

        if order['status'] == 'FILLED':
            while True:
                print(f'old tp_id={tp_id}')
                try:
                    tp_new = client.futures_create_order(symbol=pair.symbol, side=close_side, stopPrice=tp_price_new,
                                                         type=Client.FUTURE_ORDER_TYPE_TAKE_PROFIT_MARKET,
                                                         closePosition=True)
                    tp_id = tp_new['orderId']
                    break
                except Exception as err:
                    print(f'failed to create new take profit\nerror={err}')
            print(f'new tp_id={tp_id}')
            line += 1
            if line == max_line:
                print("RUN YOU, FOOLS!")
                return 'FAIL'

