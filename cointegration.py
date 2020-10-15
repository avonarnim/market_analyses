import numpy as np
import statsmodels.api as sm
import statsmodels.tsa.api as tsa
import pandas as pd

import quantopian.optimize as opt
import quantopian.algorithm as algo

def initialize(context):
    # Quantopian backtester specific variables
    set_slippage(slippage.FixedSlippage(spread=0))
    set_commission(commission.PerTrade(cost=1))
    set_symbol_lookup_date('2014-01-01')

    context.stock_pairs = [(symbol('AMZN'), symbol('MSFT')),
                           (symbol('F'), symbol('GM')),
                           (symbol('ABGB'), symbol('FSLR')),
                           (symbol('CSUN'), symbol('ASTI'))]

    context.stocks = symbols('AMZN', 'MSFT', 'F', 'GM', 'ABGB', 'FSLR', 'CSUN', 'ASTI')

    context.num_pairs = len(context.stock_pairs)
    # strategy specific variables
    context.lookback = 20 # used for regression
    context.z_window = 20 # used for zscore calculation, must be <= lookback
    context.coint_window = 28
    context.confidence_threshold = 0.05

    context.target_weights = pd.Series(index=context.stocks, data=0.125)
    context.cointegrated_pairs = [False] * context.num_pairs

    context.spread = np.ndarray((context.num_pairs, 0))
    context.inLong = [False] * context.num_pairs
    context.inShort = [False] * context.num_pairs

    # Only do work 30 minutes before close
    schedule_function(func=check_pair_status, date_rule=date_rules.every_day(), time_rule=time_rules.market_close(minutes=30))
    schedule_function(func=cointegration_test, date_rule=date_rules.month_start(), time_rule=time_rules.market_close(minutes=60))

# Will be called on every trade event for the securities you specify.
def handle_data(context, data):
    # Our work is now scheduled in check_pair_status
    pass

# Engle-Granger Cointegration Test
def cointegration_test(context, data):
    """
    Using lookback windown's closing prices for the test
    Note: lookback is only 28 to correspond with min. month length
    """

    prices = data.history(context.stocks, 'price', 35, '1d').iloc[-context.coint_window::]
    passing_pairs = []
    correlations = []

    for i in range(context.num_pairs):
        (stock_y, stock_x) = context.stock_pairs[i]
        Y = prices[stock_y]
        X = prices[stock_x]
        score, pvalue, _ = tsa.coint(X, Y)

        if pvalue < context.confidence_threshold:
            passing_pairs.append(i) # all potential pair indices
            correlations.append(X.corr(Y)) # used to find top 2 correlations

    maxPairIndexes = [] # two pairs w/ highest correlation
    if len(correlations) == 1:
        # storing pair index of max correlation
        maxPairIndexes.append(passing_pairs[correlations.index(max(correlations))])
    elif len(correlations) >= 2:
        # storing pair indices of max correlations (2)
        maxPairIndexes.append(passing_pairs[correlations.index(max(correlations))])
        correlations.remove(max(correlations))
        maxPairIndexes.append(passing_pairs[correlations.index(max(correlations))])
    context.cointegrated_pairs = maxPairIndexes
    print("---CONSTRUCTED PAIRS---", context.cointegrated_pairs)

def check_pair_status(context, data):

    prices = data.history(context.stocks, 'price', 35, '1d').iloc[-context.lookback::]
    new_spreads = np.ndarray((context.num_pairs, 1))

    for i in range(context.num_pairs):

        (stock_y, stock_x) = context.stock_pairs[i]
        Y = prices[stock_y]
        X = prices[stock_x]

        # Comment explaining try block
        try:
            hedge = hedge_ratio(Y, X, add_const=True)
        except ValueError as e:
            log.debug(e)
            return

        context.target_weights = get_current_portfolio_weights(context, data)

        new_spreads[i, :] = Y[-1] - hedge * X[-1]

        if context.spread.shape[1] > context.z_window:
            # Keep only the z-score lookback period
            spreads = context.spread[i, -context.z_window:]

            zscore = (spreads[-1] - spreads.mean()) / spreads.std()

            if context.inShort[i] and zscore < 0.0:
                context.target_weights[stock_y] = 0
                context.target_weights[stock_x] = 0

                context.inShort[i] = False
                context.inLong[i] = False

                record(X_pct=0, Y_pct=0)
                allocate(context, data)
                return

            if context.inLong[i] and zscore > 0.0:
                context.target_weights[stock_y] = 0
                context.target_weights[stock_x] = 0


                context.inShort[i] = False
                context.inLong[i] = False

                record(X_pct=0, Y_pct=0)
                allocate(context, data)
                return

            if zscore < -1.0 and (not context.inLong[i]):
                # Only trade if NOT already in a trade
                y_target_shares = 1
                X_target_shares = -hedge
                context.inLong[i] = True
                context.inShort[i] = False

                (y_target_pct, x_target_pct) = computeHoldingsPct(y_target_shares,X_target_shares, Y[-1], X[-1])

                context.target_weights[stock_y] = y_target_pct * (1.0/context.num_pairs)
                context.target_weights[stock_x] = x_target_pct * (1.0/context.num_pairs)

                record(Y_pct=y_target_pct, X_pct=x_target_pct)
                allocate(context, data)
                return


            if zscore > 1.0 and (not context.inShort[i]):
                # Only trade if NOT already in a trade
                y_target_shares = -1
                X_target_shares = hedge
                context.inShort[i] = True
                context.inLong[i] = False

                (y_target_pct, x_target_pct) = computeHoldingsPct( y_target_shares, X_target_shares, Y[-1], X[-1] )

                context.target_weights[stock_y] = y_target_pct * (1.0/context.num_pairs)
                context.target_weights[stock_x] = x_target_pct * (1.0/context.num_pairs)

                record(Y_pct=y_target_pct, X_pct=x_target_pct)
                allocate(context, data)
                return

    context.spread = np.hstack([context.spread, new_spreads])

def hedge_ratio(Y, X, add_const=True):
    if add_const:
        X = sm.add_constant(X)
        model = sm.OLS(Y, X).fit()
        return model.params[1]
    model = sm.OLS(Y, X).fit()
    return model.params.values

def computeHoldingsPct(yShares, xShares, yPrice, xPrice):
    yDol = yShares * yPrice
    xDol = xShares * xPrice
    notionalDol =  abs(yDol) + abs(xDol)
    y_target_pct = yDol / notionalDol
    x_target_pct = xDol / notionalDol
    return (y_target_pct, x_target_pct)

def get_current_portfolio_weights(context, data):
    positions = context.portfolio.positions
    positions_index = pd.Index(positions)
    share_counts = pd.Series(
        index=positions_index,
        data=[positions[asset].amount for asset in positions]
    )

    current_prices = data.current(positions_index, 'price')
    current_weights = share_counts * current_prices / context.portfolio.portfolio_value
    return current_weights.reindex(positions_index.union(context.stocks), fill_value=0.0)

def align_target_weights_with_cointegration_test(context, data):
    if len(context.cointegrated_pairs) == 0:
        context.target_weights = pd.Series(index=context.stocks, data=0)
        return
    else:
        new_weights = [0]*len(context.stocks)
        a = context.cointegrated_pairs[0]*2
        b = context.cointegrated_pairs[0]*2+1

        if len(context.cointegrated_pairs) == 1:
            aWeight, bWeight = reproportion(context.target_weights[a], context.target_weights[b], 1)
        elif len(context.cointegrated_pairs) == 2:
            aWeight, bWeight = reproportion(context.target_weights[a], context.target_weights[b], .5)
            c = context.cointegrated_pairs[1]*2
            d = context.cointegrated_pairs[1]*2+1
            cWeight, dWeight = reproportion(context.target_weights[a], context.target_weights[b], .5)
            new_weights[c] = cWeight
            new_weights[d] = dWeight
        new_weights[a] = aWeight
        new_weights[b] = bWeight
        context.target_weights = pd.Series(index=context.stocks, data=new_weights)
        return

def reproportion(propA, propB, total):
    reproportion_divisor = abs(propA) + abs(propB)
    if reproportion_divisor == 0:
        reproportion_multiplier = total/1
    else:
        reproportion_multiplier = total/reproportion_divisor
    rePropA = propA*reproportion_multiplier
    rePropB = propB*reproportion_multiplier
    return rePropA, rePropB

def allocate(context, data):
    # Set objective to match target weights as closely as possible, given constraints
    print("---ALLOCATED---")
    print(context.target_weights)
    align_target_weights_with_cointegration_test(context, data)
    print("---REALLOCATING---")
    print(context.target_weights)
    objective = opt.TargetWeights(context.target_weights)

    # Define constraints
    constraints = []
    constraints.append(opt.MaxGrossExposure(1.0))


    algo.order_optimal_portfolio(
        objective=objective,
        constraints=constraints,
    )
