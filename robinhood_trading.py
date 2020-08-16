import robin_stocks as rob
import time
import requests
import lxml.html as lh
from datetime import datetime
from threading import Timer
import time

def manage(num_symbols):

    might_buy = find_biggest_losers(num_symbols)
    should_buy = check_to_buy(might_buy)
    will_buy = []
    for idx in range(len(might_buy)):
        if should_buy[idx] != 0:
            will_buy.append((might_buy[idx], should_buy[idx]))

    buy_all(will_buy)
    holdings_info = rob.build_holdings()
    stocks_remaining = monitor_stocks(holdings_info)
    if len(stocks_remaining) != 0:
        sell_all_stocks()

    return

def find_biggest_losers(url='https://finance.yahoo.com/losers/', nunm_symbols):
    webpage = requests.get(url)
    webpage_content = lh.fromstring(webpage.content)
    tr_elements = webpage_content.xpath('//tr')
    tickers = []
    for idx in range(1, 12):
        row = tr_elements[idx]
        data = row[0].text_content()
        tickers.append(data)
    return tickers

def buy_all(tickers):
    for ticker in tickers:
        rob.order_buy_market(tickers[0],tickers[1])
    return

def check_to_buy(candidates):
    budget_per_stock = overall budget / 10
    how_manies = []
    for candidate in candidates:
        get stock profile
        num_to_buy = int(budget_per_stock/price)    # should be 0 if the stock price is over the max to invest
        how_manies.append(num_to_buy)
    return how_manies

def find_highs(symbols):
    highs = []
    for symbol in symbols:
        current_price = rob.current_price(symbol)
        if current price > highs[idx]:
            highs[idx] = current_price
    return

def check_sell(symbols, highs):
    percentage_relative = (current_price - high)/high
    if percentage_relative < -1*LOSS_WILLINGNESS:
        return True
    else:
        return False

def sell_stock(symbol, profile):
    DAILY_PROFIT += profile['quantity']*(profile['price']-profile['average_buy_price'])
    rob.order_sell_market(symbol, shares)
    return

def monitor_stocks(holdings):
    positions_after_buying = rob.build_holdings()
    highs = {}
    for ticker, info in positions_after_buying:
        highs[ticker] = info['price']

    start_time = time.time() # should be roughly 4:30 PM
    end_of_day = start_time + 3600*1.5  # should be 6
    new_day = end_of_day + 3600*15 # should be 9
    end_time = new_day + 3600*4 # should be 1

    time.sleep(3600*1.5)   # can't trade because of pattern day trader restrictions
    time.sleep(3600*15)
    while time.time() < end_time:
        monitor_stocks_internal()
    return

def monitor_stocks_internal():
    rebuilt = rob.build_holdings()
    for ticker, info in rebuilt:
        if info['price'] > highs[ticker]:
            highs[ticker] = ['price']
        should_sell = check_sell(ticker, highs[ticker])
        if should_sell:
            sell_stock(ticker)
    return

def sell_all_stocks():
    still_holding = rob.build_holdings()
    for stock in still_holding:
        sell_stock(key, value)
    return



if __name__ == '__main__':

    rob.login('<username','<password>')
    day_of_the_week = datetime.datetime.today().weekday()
    if day_of_the_week >= 4:    # avoids trading fridays
        return
    trading_day = rob.get_market_today_hours()
    if trading_day['is_open'] == False:
        return

    DAILY_PROFIT = 0
    LOSS_WILLINGNESS_NEG = 0.02
    LOSS_WILLINGNESS_POS = 0.01

    manage(number_of_tickers_to_handle)
    print(DAILY_PROFIT)
    return
