#quantilyphics
"""
integrated backtester
ver.1 options
-- using quanconnect
"""
import QuantConnect as qc
from datetime import datetime, timedelta
from QuantLib import QuantLib as ql
import py_vollib
import yfinance as yf
import numpy as np
# ---- PORTFOLIO(quantconnect) ------
start = datetime(2020,1,1)
end = datetime(2022,1,1)

qb = qc.Research.QuantBook();
#qb.SetStartDate(2020, 1, 1);
#qb.SetEndDate(2022,1,1);
qb.SetCash(100);
# -----------------------------------
# ----------- DATA ------------------
TICKER = qb.add_equity("SPY");
#for raw data
TICKER.set_data_normalization_mode(DataNormalizationMode.RAW)
OPTION = qb.add_option(TICKER.symbol);
# test
OPTION.price_model = OptionPriceModels.binomial_cox_ross_rubinstein()
INTEREST_RATE = qb.history(
    qb.add_data(Fred,'DFF').symbol,
    start,
    end,
    Resolution.DAILY
)
DIVIDEND_YIELD = qb.history(Dividend, TICKER.symbol, start,end, Resolution.DAILY)
DIVIDEND_YIELD['dividend'] = DIVIDEND_YIELD['distribution'] / DIVIDEND_YIELD['referenceprice']
rfr = INTEREST_RATE.iloc[0]['value']
div = DIVIDEND_YIELD.iloc[0]['dividend']

price_data = qb.history(TICKER.symbol, start, end, Resolution.DAILY);
option_data = qb.GetOptionHistory(OPTION.symbol, start, end, Resolution.DAILY)
# -----------------------------------
# ---------- FUNCTION ---------------
def GET_OPTIONS(date, symb, topic):
    if topic == 'get':
        chain = qb.option_chain(symb.value)
        return chain
    if topic == 'history':
        OHLC = qb.History(symb.symbol,365, Resolution.DAILY)
        return OHLC

def GET_MARKET_DATA(root1,root2, _d, underlying):
    global rfr, div;
    # marketdata[0] - calendar
    # marketdata[1] - count
    # marketdata[2] - spot
    # marketdata[3] - rfr [0] - value [1] - ql wrapper
    # marketdata[4] - div [0] - v
    calendar = getattr(ql, root1)(ql.UnitedStates.NYSE)
    count = getattr(ql,root2)()
    date = ql.Date(_d.day, _d.month, _d.year)
    # get interest rate
    spot = ql.QuoteHandle(ql.SimpleQuote(underlying[0]['close']))
    find = pd.Timestamp(_d)
    if ('DFF.Fred', find.normalize()) in INTEREST_RATE.index:
        rfr = INTEREST_RATE.loc[('DFF.Fred', find.normalize()), 'value']
    else:
        rfr = rfr
    if ('SPY', find.normalize()) in DIVIDEND_YIELD.index:
        div = DIVIDEND_YIELD.at[('SPY', find.normalize()), 'dividend']
    else:
        div = div
    #print(calendar,count,spot,rfr,div)
    return [calendar,count,spot,rfr,div]
# -----------------------------------
# ---------- METRICS ----------------
def BINOMIAL_PRICING_MODEL(row, underlying, iv, market_data):
    _d = underlying[1].to_pydatetime()
    date = ql.Date(_d.day, _d.month, _d.year)
    ql.Settings.instance().evaluationDate = date;
    if not market_data:
        market_data = GET_MARKET_DATA("UnitedStates", "Actual365Fixed", _d, underlying)
    #
    #print(market_data[3], market_data[4])
    market_data[3] = ql.YieldTermStructureHandle(
        ql.FlatForward(date, market_data[3], market_data[1])
    )
    market_data[4] = ql.YieldTermStructureHandle(
        ql.FlatForward(date, market_data[4], market_data[1])
    )
    #
    option_type = ql.Option.Call if row.right == 0 else ql.Option.Put
    option = ql.VanillaOption(
        ql.PlainVanillaPayoff(option_type, row.strike),
        ql.AmericanExercise(date, ql.Date(row.expiry.day, row.expiry.month, row.expiry.year))
    )
    implied_vol = ql.BlackVolTermStructureHandle(
        ql.BlackConstantVol(date, market_data[0], row.implied_volatility, market_data[1])
    )
    if iv:
        implied_vol = ql.BlackVolTermStructureHandle(
            ql.BlackConstantVol(date, market_data[0], iv, market_data[1])
        )
    bsm_process = ql.BlackScholesMertonProcess(
        market_data[2],market_data[4],market_data[3],implied_vol
    )
    ENGINE = ql.BinomialVanillaEngine(bsm_process,"crr", 100)
    option.setPricingEngine(ENGINE)
    return option
    
def IV(row, option, underlying):
    _d = underlying[1].to_pydatetime()
    date = ql.Date(_d.day, _d.month, _d.year)
    ql.Settings.instance().evaluationDate = date
    market_data = GET_MARKET_DATA("UnitedStates","Actual365Fixed", _d, underlying)
    #
    market_data[3] = ql.YieldTermStructureHandle(
        ql.FlatForward(date, market_data[3], market_data[1])
    )
    market_data[4] = ql.YieldTermStructureHandle(
        ql.FlatForward(date, market_data[4], market_data[1])
    )
    #
    dummy_vol = ql.BlackVolTermStructureHandle(
        ql.BlackConstantVol(date,market_data[0], 0.20, market_data[1])
    )
    bsm_process = ql.BlackScholesMertonProcess(
        market_data[2],market_data[4],market_data[3],dummy_vol
    )
    try:
        iv = option.impliedVolatility(row.last_price,bsm_process,
        1e-4,10000,1e-4,4.0
        )
        return iv
    except:
        return 0.0

def GREEKS(option,iv, underlying, row):
    _d = underlying[1].to_pydatetime()
    p0 = option.NPV()
    market_data = GET_MARKET_DATA("UnitedStates", "Actual365Fixed", _d, underlying)
    print(market_data[3], market_data[4])
    h = 0.0001
    r = market_data[3]
    market_data[3] = market_data[3] + h
    option = BINOMIAL_PRICING_MODEL(row, underlying, iv, market_data)
    p_plus = option.NPV()
    market_data[3] = r
    rho = (p_plus - p0) / h
    vega = iv + h
    option = BINOMIAL_PRICING_MODEL(row, underlying, vega, None)
    p_plus = option.NPV()
    vega = (p_plus - p0) / h
    return [option.delta(), option.theta(),option.gamma(),vega,rho]
# -----------------------------------
# --------- BACKTESTER --------------
for (_symb, _d), ROW in price_data.iterrows():
    qb.set_date_time(_d.to_pydatetime())
    #print(_d.to_pydatetime())
    #print(type(_symb), type(_d))
    _TABLE = [ROW, _d, _symb]

    chain = GET_OPTIONS(_d, _symb, 'get');
    #print(chain)
    for C_ROW in chain:
        #print(C_ROW)
        """
        if save != None:
            print("break1")
            break
        """
        if C_ROW.volume > 10000 and C_ROW.open_interest > 0:
            #print(C_ROW.last_price, ROW['close'], C_ROW.strike)
            qb.add_option_contract(C_ROW.symbol)
            C_ROWi = qb.Securities[C_ROW.symbol]
            ROW_OHLC = qb.History(C_ROW.symbol,Resolution.DAILY);
            DTE = abs((C_ROW.expiry - _d.to_pydatetime()).days) 
            #
            option = BINOMIAL_PRICING_MODEL(C_ROW, _TABLE, None, None)
            iv = IV(C_ROW, option, _TABLE)
            if iv > 0:
                option = BINOMIAL_PRICING_MODEL(C_ROW, _TABLE, iv, None)
                greeks = GREEKS(option, iv, _TABLE, C_ROW)
            #
                #print(C_ROW.last_price, C_ROW.strike, ROW['close'], C_ROW.right, DTE)
                #print(_d.to_pydatetime(), C_ROW.expiry)
                #print(f'{C_ROW.implied_volatility} {iv}')
                #print(f'{greeks[0]} {C_ROW.greeks.delta}')
                #print(greeks)
                break
            #break
        #break
    break
