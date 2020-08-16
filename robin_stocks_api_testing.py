import robin_stocks as rob
import time
import inspect as i
import json

def return_current_holdings():
    my_stocks = rob.build_holdings()
    for key,value in my_stocks.items():
        print(key, value)
    return

def return_movers():
    # learn_about_rob() shows that the get_top_movers_sp500 functions are
    # unsupported despite documentation
    # down = rob.get_top_movers_sp500('down')
    # print(down)
    top = rob.get_top_movers('down')
    for item in top:
        print(item['symbol'])
    return

def learn_about_rob():
    members = i.getmembers(rob)
    print(members)
    return

def get_positions():
    print(rob.get_current_positions())
    return

if __name__ == '__main__':
    rob.login('<username>','<password>')
    return_current_holdings()
    return_movers()
    learn_about_rob()
    get_positions()
