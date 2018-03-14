# app.trades
import logging
import app
from app import candles
from app.utils import utc_datetime as now
from docs.data import FREQ_TO_STR as freqtostr, PER_TO_STR as pertostr,\
VOLUME as VOL, BINANCE_TRADE_FEE_PCT as FEE_PCT

log = logging.getLogger('trades')
def siglog(msg): log.log(100, msg)
def keystostr(keys): return (keys[0], freqtostr[keys[1]], pertostr[keys[2]])

#------------------------------------------------------------------------------
def update_position(keys, wascore, df_z):
    """Create or update existing position for zscore above threshold value.
    @keys: (pair, freq, period) tuple
    @wascore: weighted average trade signal score
    @df_z: dataframe w/ stat analysis & candle component z-scores
    """
    db = app.get_db()
    idx = dict(zip(['pair', 'freq', 'period'], keys))
    curs = db.trades.find({**idx, **{'status': 'open'}})

    # Open new position
    if curs.count() == 0:
        candle = candles.last(idx['pair'], freqtostr[idx['freq']])
        fee_amt = (FEE_PCT/100) * VOL * candle['close']
        buy_amt = (VOL * candle['close']) - fee_amt

        db.trades.insert_one({**idx, **{
            'status': 'open',
            'exchange': 'Binance',
            'start_time': now(),
            'buy_price': candle['close'],
            'buy_vol': VOL,
            'buy_amt': buy_amt,
            'total_fee_pct': FEE_PCT,
            'candles':{'start': candle},
            'scores': {'start': {
                'wascore':wascore,
                'zscores': df_z.to_dict()
            }}
        }})
        siglog("Opened trade for (%s, %s, %s)." % keys)
    # Update open position
    else:
        #record = list(curs)[0]
        #db.trades.update_one({"_id":record["_id"]}, {"$set":{"last_zscore":zscore}})
        siglog("Updated trade zscore for (%s,%s,%s)." % keys)

#------------------------------------------------------------------------------
def close_position(keys, wascore, df_z):
    """Close off existing position and calculate earnings.
    @keys: (pair, freq, period) tuple
    @wascore: weighted average trade signal score
    @df_z: dataframe w/ stat analysis & candle component z-scores
    """
    db = app.get_db()
    idx = dict(zip(['pair', 'freq', 'period'], keys))
    curs = db.trades.find({**idx, **{'status': 'open'}})

    if curs.count() == 0:
        return False
    else:
        trade = list(curs)[0]
        siglog('Closing (%s, %s, %s) trade.' % keystostr(keys))

    candle = candles.last(idx['pair'], freqtostr[idx['freq']])
    end_time = now()
    fee_amt = (FEE_PCT/100) * VOL * candle['close']
    sell_amt = (VOL * candle['close']) - fee_amt
    price_pct_change = (candle['close'] - trade['buy_price']) / trade['buy_price']
    gross_earn = (candle['close'] * VOL) - (trade['buy_price'] * VOL)
    net_earn = gross_earn - (fee_amt * 2)

    db.trades.update_one(
        {"_id": trade['_id']},
        {"$set": {
            'status': 'closed',
            'end_time': end_time,
            'sell_price': candle['close'],
            'sell_amt': sell_amt,
            'total_fee_pct': FEE_PCT * 2,
            'price_pct_change': price_pct_change,
            'gross_earn':gross_earn,
            'net_earn': net_earn,
            'candles.end': candle,
            'scores.end': {
                'wascore': wascore,
                'zscores': df_z.to_dict()
            }
        }}
    )

    siglog('Closing (%s, %s, %s) trade.' % keys)
    siglog('Price change: %s%%' % round(price_pct_change,2))

#------------------------------------------------------------------------------
def summarize():
    db = app.get_db()

    closed = list(db.trade_stats.find({"end_time":{"$ne":False}}))
    n_loss, n_gain = 0, 0
    pct_gross_gain = 0
    pct_net_gain = 0
    pct_trade_fee = 0.05

    for n in closed:
        if n['pct_change'] > 0:
            n_gain += 1
        else:
            n_loss += 1
        pct_gross_gain += n['pct_change']

    win_ratio = n_gain/len(closed)
    pct_net_gain = pct_gross_gain - (len(closed) * pct_trade_fee)
    n_open = db.trade_stats.find({"end_time":False}).count()

    log.log(100, "Trade summary: %s closed, %s win ratio, %s%% gross earn, %s%% net earn. %s open." %(
        len(closed), round(win_ratio,2), round(pct_gross_gain,2), round(pct_net_gain,2), n_open))
    log.log(100, '-'*80)
    log.debug('%s win trades, %s loss trades.', n_gain, n_loss)
