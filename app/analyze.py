# app.analyze

import logging
from pprint import pprint
import pandas as pd
from app import get_db
from app.timer import Timer
log = logging.getLogger('analyze')

#------------------------------------------------------------------------------
def top_symbols(rank):
    """Get list of ticker symbols within given rank.
    """
    db = get_db()
    _date = list(db.tickers_5m.find().sort("date",-1).limit(1))[0]["date"]
    cursor = db.tickers_5m.find({"date":_date, "rank":{"$lte":rank}}).sort("rank",1)
    return [n["symbol"] for n in list(cursor)]

#------------------------------------------------------------------------------
def corr(symbols):
    """Generate price correlation matrix for given list of symbols.
    """
    db = get_db()
    t1 = Timer()
    cursor = db.tickers_1d.aggregate([
        {"$group":{
            "_id":"$symbol",
            "date":{"$push":"$date"},
            "price":{"$push":"$close"}
        }}
    ])

    t_aggr = t1.clock(t='ms')
    t1.restart()
    df = pd.DataFrame(list(cursor))
    df.index = df["_id"]
    t_df = t1.clock(t='ms')
    t1.restart()

    log.debug("tickers aggregated in %s ms, dataframe built in %s ms",
        t_aggr, t_df)

    dfs = []
    for sym in symbols:
        dfs.append(
            pd.DataFrame(
                columns=[sym],
                index=df.loc[sym]["date"],
                data=df.loc[sym]["price"]
            ).sort_index()
        )

    big_df = dfs[0]
    for _df in dfs[1:]:
        big_df = big_df.join(_df)

    corr = big_df.corr()
    log.debug("concat + corr calculated in %s ms", t1.clock(t='ms'))
    return corr

#------------------------------------------------------------------------------
def corr_min_max(symbol, max_rank):
    """Find lowest & highest price correlation symbols (within max_rank) with
    given ticker symbol.
    """
    db = get_db()
    symbols = top_symbols(max_rank)
    df = corr(symbols)
    col = df[symbol]
    del col[symbol]
    return {
        "symbol":symbol,
        "min_correlation": {
            col.idxmin(): col[col.idxmin()]
        },
        "max_correlation": {
            col.idxmax(): col[col.idxmax()]
        }
    }


