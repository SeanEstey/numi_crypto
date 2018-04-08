"""docs.scratchpad

Unfinished or non-implemented code.
"""

#------------------------------------------------------------------------------
def _unfinished():
    # *********************************************************************
    # Calculate Z-Scores, store in dataframe/mongodb
    # ops=[]
    # for pair in pairs:
    #    candle = candles.newest(pair, freq_str, df=dfc)
    #    scores = signals.z_score(
    #        dfc.loc[pair,freq], candle, mkt_ma=mkt_ma)
    #    name = 'ZSCORE_' + freq_str.upper()
    #   dfc[name].loc[pair,freq][-1] = scores['CLOSE']['ZSCORE'].round(3)
    #   ops.append(UpdateOne({"open_time":candle["OPEN_TIME"],
    #       "pair":candle["PAIR"], "freq":candle["FREQ"]},
    #       {'$set': {name: scores['CLOSE']['ZSCORE']}}
    #   ))
    #   db.candles.bulk_write(ops)
    #
    #   if c2['OPEN_TIME'] < c1['OPEN_TIME']:
    #       return False
    # *********************************************************************

    # ********************************************************************
    # A. Profit loss
    # if c2['CLOSE'] < c1['CLOSE']:
    #    if 'Resistance' not in holding['buy']['details']:
    #        return sell(holding, c2, scores)
    #    margin = signals.adjust_support_margin(freq_str, mkt_ma)
    #    if (c2['CLOSE'] * margin) < c1['CLOSE']:
    #        return sell(holding, c2, scores)
    # B. Maximize profit, make sure price still rising.
    # p_max = df.loc[slice(c1['OPEN_TIME'], df.iloc[-2].name)]['CLOSE'].max()
    # elif not np.isnan(p_max) and candle['CLOSE'] < p_max:
    #   return sell(holding, c2, scores)
    # ********************************************************************

    # ********************************************************************
    # Open Trades (If Sold at Present Value)
    # pct_change_hold = []
    # active = list(db.trades.find({'status':'open'}))
    # for hold in active:
    #    candle = candles.newest(hold['pair'], freq_str, df=dfc)
    #    pct_change_hold.append(pct_diff(hold['buy']['candle']['CLOSE'], candle['CLOSE']))
    #
    # if len(pct_change_hold) > 0:
    #     pct_change_hold = sum(pct_change_hold)/len(pct_change_hold)
    # else:
    #     pct_change_hold = 0.0
    #
    # siglog("Holdings: {} Open, {:+.2f}% Mean Value".format(len(active), pct_change_hold))
    # siglog('-'*80)
    # ********************************************************************
    pass

#-----------------------------------------------------------------------------
def print_tickers():
    # *********************************************************************
    # TODO: Create another trading log for detailed ticker tarding signals.
    # Primary siglog will be mostly for active trading/holdings.
    # *********************************************************************
    pass

#-----------------------------------------------------------------------------
def thresh_adapt():
    # ********************************************************************
    # TODO: Optimize by trying to group period logically via new "settled"
    # price range, if possible.
    # If bull/bear market, shorten historic period range
    #if abs(mkt_ma) > 0.05 and abs(mkt_ma) < 0.1:
    #    shorten = 0.75
    #elif abs(mkt_ma) >= 0.1 and abs(mkt_ma) < 0.15:
    #    shorten = 0.6
    #elif abs(mkt_ma) > 0.15:
    #    shorten = 0.5
    #
    # Correct for distorted Z-Score values in sudden bearish/bullish swings.
    # A volatile bearish swing pushes Z-Scores downwards faster than the mean
    # adjusts to represent the new "price level", creating innacurate deviation
    # values for Z-Scores. Offset by temporarily lowering support threshold.
    #
    # A) Breakout (ZP > Threshold)
    #   breakout = strats['Z-SCORE']['BUY_BREAK_REST']
    #   if z_score > breakout:
    #       msg="{:+.2f} Z-Score > {:.2f} Breakout.".format(z_score, breakout)
    #    return open_holding(candle, scores, extra=msg)
    # ********************************************************************
    #z_thresh = RULES[freq_str]['Z-SCORE']['THRESH']
    # Example: -0.1% MA and -2.0 support => -3.0 support
    if mkt_ma < 0:
        return z_thresh * (1 + (abs(mkt_ma) * 5))
    # Example: +0.1% MA and +2.0 support => +0.83 support
    else:
        return z_thresh * (1 - (mkt_ma * 1.75))

#------------------------------------------------------------------------------
def pca(df):
    """Run Principal Component Analysis (PCA) to identify time-lagged
    price correlations between coins.
    Code author: Dr. Pawel Lachowicz
    Source: https://tinyurl.com/yaswrf9u
    """
    m = df.mean(axis=0)
    s = df.std(ddof=1, axis=0)

    # normalised time-series as an input for PCA
    dfPort = (df - m)/s

    c = np.cov(dfPort.values.T)     # covariance matrix
    co = np.corrcoef(df.values.T)  # correlation matrix

    tickers = list(df.columns)

    # perform PCA
    w, v = np.linalg.eig(c)

    # choose PC-k numbers
    k1 = -1  # the last PC column in 'v' PCA matrix
    k2 = -2  # the second last PC column

    # begin constructing bi-plot for PC(k1) and PC(k2)
    # loadings

    # compute the distance from (0,0) point
    dist = []
    for i in range(v.shape[0]):
        x = v[i,k1]
        y = v[i,k2]
        d = np.sqrt(x**2 + y**2)
        dist.append(d)

    # check and save membership of a coin to
    # a quarter number 1, 2, 3 or 4 on the plane
    quar = []
    for i in range(v.shape[0]):
        x = v[i,k1]
        y = v[i,k2]
        d = np.sqrt(x**2 + y**2)

        #if(d > np.mean(dist) + np.std(dist, ddof=1)):
        # THESE IFS WERE NESTED IN ABOVE IF CLAUSE
        if((x > 0) and (y > 0)):
            quar.append((i, 1))
        elif((x < 0) and (y > 0)):
            quar.append((i, 2))
        elif((x < 0) and (y < 0)):
            quar.append((i, 3))
        elif((x > 0) and (y < 0)):
            quar.append((i, 4))

    for i in range(len(quar)):
        # Q1 vs Q3
        if(quar[i][1] == 1):
            for j in range(len(quar)):
                if(quar[j][1] == 3):
                    # highly correlated coins according to the PC analysis
                    print(tickers[quar[i][0]], tickers[quar[j][0]])
                    ts1 = df[tickers[quar[i][0]]]  # time-series
                    ts2 = df[tickers[quar[j][0]]]
                    # correlation metrics and their p_values
                    slope, intercept, r2, pvalue, _ = stats.linregress(ts1, ts2)
                    ktau, kpvalue = stats.kendalltau(ts1, ts2)
                    print(r2, pvalue)
                    print(ktau, kpvalue)
        # Q2 vs Q4
        if(quar[i][1] == 2):
            for j in range(len(quar)):
                if(quar[j][1] == 4):
                    print(tickers[quar[i][0]], tickers[quar[j][0]])
                    ts1 = df[tickers[quar[i][0]]]
                    ts2 = df[tickers[quar[j][0]]]
                    slope, intercept, r2, pvalue, _ = stats.linregress(ts1, ts2)
                    ktau, kpvalue = stats.kendalltau(ts1, ts2)
                    print(r2, pvalue)
                    print(ktau, kpvalue)

#------------------------------------------------------------------------------
def thresholding_algo(y, lag, threshold, influence):
    """
    """
    signals = np.zeros(len(y))
    filteredY = np.array(y)
    avgFilter = [0]*len(y)
    stdFilter = [0]*len(y)
    avgFilter[lag - 1] = np.mean(y[0:lag])
    stdFilter[lag - 1] = np.std(y[0:lag])

    for i in range(lag, len(y)):
        if abs(y[i] - avgFilter[i-1]) > threshold * stdFilter [i-1]:
            if y[i] > avgFilter[i-1]:
                signals[i] = 1
            else:
                signals[i] = -1

            filteredY[i] = influence * y[i] + (1 - influence) * filteredY[i-1]
            avgFilter[i] = np.mean(filteredY[(i-lag):i])
            stdFilter[i] = np.std(filteredY[(i-lag):i])
        else:
            signals[i] = 0
            filteredY[i] = y[i]
            avgFilter[i] = np.mean(filteredY[(i-lag):i])
            stdFilter[i] = np.std(filteredY[(i-lag):i])

    return dict(signals = np.asarray(signals),
                avgFilter = np.asarray(avgFilter),
                stdFilter = np.asarray(stdFilter))