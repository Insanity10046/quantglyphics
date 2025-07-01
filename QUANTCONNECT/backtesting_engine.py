import QuantConnect as qc;
from datetime import datetime as dt;
from QuantLib import QuantLib as ql;
import pandas as pd; import numpy as np;
import uuid;
#---------------------------------------
#               :HELPER:               #
#---------------------------------------
def ENTRY_TRIGGER(direction,entry, OHLC):
    if direction == 'long' and entry >= OHLC['close']:
        return True;
    if direction == 'short' and entry <= OHLC['close']:
        return True;

def PROCESS(MARKET, IV, DATE):
    return ql.BlackScholesMertonProcess(
        MARKET['values']['spot'],
        ql.YieldTermStructureHandle(ql.FlatForward(DATE,ql.QuoteHandle(MARKET['values']['div']),MARKET['state']['count_of_days'])),
        ql.YieldTermStructureHandle(ql.FlatForward(DATE,ql.QuoteHandle(MARKET['values']['rfr']),MARKET['state']['count_of_days'])),
        IV
        )
#---------------------------------------
#                :CLASS:               #
#---------------------------------------
class METRICS():
    # profitability
    def EQUITY_CURVE(_p):
        _p.performance['equity_curve'] = [_p.initial_cash]
        for trade in _p.trade_history:
            _p.performance['equity_curve'].append(p.performance['equity'][-1] + trade.pnl)
        _p.performance['equity_curve'] = pd.Series(_p.performance['equity_curve'])
    def CAGR(benchmark, _p):
        years = (benchmark.index.max() - benchmark.index.min()).days / 365.25
        _p.performance['cagr'] = (_p.cash / _p.intial_cash) ** (1 / years) - 1 if years > 0 else 0;
    def TOTAL_RETURNS(_p):
        _p.performance['total_returns'] = (_p.cash - _p.intial_cash) / _p.intial_cash
    def NET_PROFIT(_p):
        gross_profit = sum(t.pnl for t in _p.trade_history)
        transaction_costs = sum(t.comission for t in _p.trade_history)
        net_profit = gross_profit - transaction_costs
    # risk
    def SHARPE_SORTINO(equity, period, rfr):
        r = np.diff(equity) / equity[:-1]
        rf = rfr / period
        x = r - rf
        sharpe = np.mean(x) / np.std(x, ddof=1) * np.sqrt(period)
        d = x[x < 0]
        sortino = np.mean(x) / (np.std(d, ddof=1) * np.sqrt(period)) if d.size else 0.0
        return sharpe, sortino
    # drawdowns
    def MAX_DRAWDOWNS(_p):
        previous_peak = _p.performance['equity_curve'].cummax();
        _p.performance['drawdown_series'] = (_p.performance['equity_curve'] - previous_peak) / previous_peak
        _p.performance['max_drawdown'] = _p.performance['drawdown_series'].min()
    def RECOVERY_TIME(e):
        p = e.iloc[0]
        d = None
        r = []
        for i, x in enumerate(e):
            if x >= p:
                if d is not None: r += [i - d]; d = None
                p = x
            elif d is None: d = i
        return max(r, default=0)
    def RUIN_RISK(_p):
        z = (_p.performance['winrate'] * _p.performance['average_win']) - (_p.performance['lossrate'] * _p.performance['average_loss']) ;
        a = (_p.performance['winrate'] * (_p.performance['average_win'])**2 - _p.performance['lossrate'] * (_p.performance['average_loss'])**2)**0.5
        p = 0.5 * ((1+z)/a)
        amount_risked_per_trade = _p.performance['average_win'] / _p.performance['rr_ratio']
        max_risk = amount_risked_per_trade / _p.intial_cash

        _p.performance['risk_of_ruin'] = ((1-p)/p)**(max_risk/a)
    # consistency
    def WINS_LOSSES(_p):
        wins = (sum(t.pnl > 0 for t in _p.trade_history))
        losses = (sum(t.pnl < 0 for t in _p.trade_history))
        return wins,losses;
    def RATE_AVERAGES(_p, wins, losses):
        _p.performance['winrate'] = (wins / _p.trade_history) * 100;
        _p.performance['lossrate'] = (losses / _p.trade_history) * 100;
        _p.performance['average_win'] = _p.performance['winrate'] / _p.intial_cash;
        _p.performance['average_loss'] = _p.performance['lossrate'] / _p.intial_cash;
    def PROFIT_FACTOR(_p):
        profits, profit_loss = 0,0;
        for t in trade_history:
            if t.pnl > 0:
                profit+=t.pnl;
            elif t.pnl < 0:
                profit_loss+=t.pnl;
        _p.performance['profit_factor'] = profits / profit_loss;
        return profits, profit_loss
    # transaction_costs
    def transactions_slippage(_p):
        tp, tc, ts = 0, 0, 0
        for t in _p.trade_history:
            tp += t.pnl
            tc += t.commission
            ts += abs(t.size * (t.fill_price - t.expected_price))
        return {
            "gross_pnl": tp,
            "commission": tc,
            "slippage": ts,
            "net_pnl": tp - tc - ts,
            "cost_pct": (tc + ts) / tp * 100 if tp else 0
        }

    def __init__(self, _p, benchmark, period, rfr):
        wins, losses = self.WINS_LOSSES(_p);
        self.RATE_AVERAGES(_p,wins,losses);
        profit, profit_losses = self.PROFIT_FACTOR(_p)
        self.EQUITY_CURVE(_p);
        self.CAGR(benchmark,_p)
        self.TOTAL_RETURNS(_p)
        self.NET_PROFIT(_p)
        sharpe,sortino = self.SHARPE_SORTINO(_p.performance['equity_curve'],period,rfr)
        self.MAX_DRAWDOWNS(_p);
        recovery_time = self.RECOVERY_TIME(_p);
        self.RUIN_RISK(_p);
        erosion = self.transactions_slippage(_p);
        
        _p.performance['sharpe'] = sharpe;
        _p.performance['sortino'] = sortino;
        _p.performance['erosion'] = erosion;
        _p.performance['expectancy'] = (_p.performance['winrate'] * _p.performance['average_win']) - ((1 - _p.performance['winrate']) * _p.performance['average_loss'])

class EventManager():
    def __init__(self):
        self.market_status = 'close';
    def MARKET_SCHEDULE(self,DATE):
        self.market_status = 'open' if DATE.weekday() >= 4 else 'close'
    def OPTION_EXPIRIES(self,PORTFOLIO,OHLC,DATE):
        for position in PORTFOLIO.positions:
            contract = position.contract
            contract['dte'] = (contract['expiry'] - DATE).days
            if contract and (contract['dte'] <= 0):
                position.EXERCISE(OHLC['close'])
    def ORDERS_MANAGEMENT(self, PORTFOLIO, OHLC):
        for position in PORTFOLIO.positions:
            if position.executed == False:
                position.ORDER_TYPES(OHLC,OHLC['close']);
    def EVENT_HANDLER(self,DATE,PORTFOLIO,OHLC):
        if self.market_status == 'close':
            return False
        if DATE.weekday() == 4:
            self.OPTION_EXPIRIES(PORTFOLIO,OHLC,DATE);
        if DATE.weekday() <= 4:
            self.ORDERS_MANAGEMENT(PORTFOLIO, OHLC)
        return True

class Position:
    def __init__(self, asset, contract, qty, comission,exec_fees, order_type, stop_loss, direction, entry, portfolio):
        self.id = uuid.uuid4();
        self.asset = asset;
        self.entry = entry;
        self.entry_time = None;
        self.direction = direction;
        self.contract = contract;
        self.size = qty;
        self.order_type = order_type;
        self.comission = comission;
        self.exec_fees = exec_fees;
        self.executed = False;
        self.stop_loss = stop_loss;
        self.parent = portfolio
    def EXECUTE(self, ENTRY):
        self.executed = True;
        self.entry = ENTRY;
        self.order_type = None;
    def ORDER_TYPES(self, OHLC, ENTRY):
        if self.order_type == 'limit' and ENTRY_TRIGGER(self.direction,self.entry, OHLC):
            self.EXECUTE(ENTRY);
            # turn order to market order;
        if self.order_type == 'market_order':
            self.EXECUTE(ENTRY);
        if self.stop_loss and ENTRY_TRIGGER(self.direction,self.stop_loss, OHLC):
            # cancel the market order connected to it or is there a better way like, having self.stop_loss
            return "stop loss triggered"
        if self.order_type == 'stop_limit' and ENTRY_TRIGGER(self.direction,self.stop_loss,OHLC):
            self.order_type = 'limit';
            self.stop_loss = None;
    def MONEYNESS(self, underlying):
        if self.contract['strike'] == underlying: return 'ATM'
        itm = (underlying > self.contract['strike']) if self.classes == 'call' else (self.contract['strike'] > underlying)
        return 'ITM' if (itm and self.direction == 'long') or (not itm and self.direction == 'short') else 'OTM'
    def EXERCISE(self, underlying):
        if self.MONEYNESS(underlying) != 'ITM':
            return self.parent.close_position(self.id)
        if self.direction == 'long':
            self.direction = 'long' if self.contract['class'] == 'call' else 'short'
        else:
            self.direction = 'short' if self.contract['class'] == 'call' else 'long'
        self.size *= 100
        self.entry = self.contract['strike']
        self.classes = None
        self.contract = None
        self.parent.cash -= self.exec_fees;

class MarketEnvironment:
    def __init__(self, START, END, RESOLUTION):
        self.domain = qc.Research.QuantBook();
        self.start, self.end = START, END;
        self.resolution = RESOLUTION;
    def GET_OPTION_CONTRACTS(self,SYMBOL):
        return qb.option_chain(SYMBOL.value)
    def DATA_RETRIEVAL(self,COUNTRY, DATECOUNT, MARKET_STATE,MARKET, UNDERLYING, CURRENT_DATE):
        MARKET['state']['calendar'] = getattr(ql, COUNTRY)(MARKET_STATE);
        MARKET['state']['count_of_days'] = getattr(ql,DATECOUNT)();
        date = pd.Timestamp(CURRENT_DATE).normalize();
        MARKET['values']['spot'] = ql.QuoteHandle(ql.SimpleQuote(UNDERLYING));
        rfr = MARKET['chart']['interests'].xs(date, level='time')['value'].iloc[0]
        MARKET['state']['rfr'] = ql.SimpleQuote(rfr) if not isinstance(rfr, ql.SimpleQuote) else rfr
        div = MARKET['chart']['dividends'].at[(MARKET['ticker'].Symbol.value,date), 'dividend'] if ('SPY',date) in MARKET['chart']['dividends'].index else MARKET['values']['div']
        MARKET['values']['div']  = ql.SimpleQuote(div) if not isinstance(div, ql.SimpleQuote) else div
        #,count,spot,rfr,div
    def SET_ENVIRONMENT(self,SYMBOL):
        ticker = self.domain.add_equity(SYMBOL);
        interest_rate = self.domain.history(self.domain.add_data(qc.DataSource.Fred, 'DFF').symbol,self.start, self.end, self.resolution)
        dividend_yield = self.domain.history(qc.Data.Market.Dividend, ticker.symbol, self.start,self.end, self.resolution);
        dividend_yield['dividend'] = dividend_yield['distribution'] / dividend_yield['referenceprice'];
        market = { 
            'ticker': ticker,
            'chart': {'price':self.domain.History(ticker.symbol,self.start,self.end,self.resolution), 'interests':interest_rate, 'dividends':dividend_yield},
            'values': {'rfr': None, 'div': None, 'spot': None},
            'state': {'calendar': None, 'count_of_days': None}
        }
        market['values']['rfr'] = market['chart']['interests'].iloc[0]['value'];
        market['values']['div'] = market['chart']['dividends'].iloc[0]['dividend'];
        return market;
class Broker:
    def __init__(self, COMISSION, SLIPPAGE, FEES):
        self.comission = COMISSION;
        self.slippage = SLIPPAGE[0];
        self.vol_slippage = SLIPPAGE[1];
        self.reg_fee = sum(FEES);
        self.execution_fee = FEES[3];
    def BA_SPREAD(self, BID, ASK, ORDER_SIZE):
        spread = BID - ASK;
        execution_price = ASK if ORDER_SIZE > 0 else BID;
        mid_price = (ASK + BID) / 2
        return spread, execution_price, mid_price;
    def SLIPPAGE(self,ROW, ORDER_SIZE, VOLUME,BID, ASK, DAILY_VOL):
        AVG_VOLUME = ROW['volume'].rolling(window=20).mean();
        spread, execution_price, mid_price = self.BA_SPREAD(BID,ASK,ORDER_SIZE);
        size_ratio = min(abs(ORDER_SIZE) / max(AVG_VOLUME, 1), 1.0)
        impact = DAILY_VOL * math.sqrt(size_ratio) * spread
        slippage = impact if ORDER_SIZE > 0 else -impact
        raw_price = execution_price + slippage
        lower = bid - abs(impact)
        upper = ask + abs(impact)
        exec_price = max(min(raw_price, upper), lower)
        return exec_price
    def EXECUTION_MODEL(self, PORTFOLIO, O_P, OHLC, DATA):
        if O_P['decision'] == 'open':
            entry = SLIPPAGE(OHLC, O_P['qty'], OHLC['volume'],DATA['bid'], DATA['ask'], DATA['daily_vol']) if O_P['order_type'] == 'market_order' else O_P['entry']
            order = Position(O_P['asset'],O_P['contract'],O_P['qty'],self.comission,self.execution_fee,O_P['order_type'],O_P['stop_loss'],O_P['entry'],PORTFOLIO);
            PORTFOLIO.cash -= self.comission
            order.entry_time = OHLC.name[1].to_pydatetime();
            PORTFOLIO.positions.append(order);
        else:
            position = next((obj for obj in PORTFOLIO.positions if obj.id == O_P['order']), None);
            if position.type == 'long':
                pnl = position.size * (OHLC['close'] - position.entry);
            else:
                pnl = position.size * (position.entry - OHLC['close']);
            PORTFOLIO.trade_history.append({
                'id': position.id,
                'type': position.type,
                'size': position.size,
                'entry': position.entry,
                'exit': OHLC['close'],
                'entry_time': position.entry_time,
                'exit_time': settings,
                'pnl': pnl,
                'return_pct': (pnl / (position.size * position.entry)) * 100,
                'comission': position.commission
            })
            PORTFOLIO.positions.remove(position)
            return pnl;
class Portfolio:
    """
    settings[0] - starting cash
    """
    def __init__(self, strategy, portfolio_settings, broker):
        self.strategy = strategy;
        self.intial_cash = portfolio_settings[0];
        self.cash = self.intial_cash;
        self.positions = [];
        self.trade_history = [];
        self.performance = {};
        self.broker = broker;
#---------------------------------------
#             :FUNCTION:               #
#---------------------------------------
def OPTION_CONTRACT(CONTRACT, EVAL_DATE, EXERCISE_TYPE):
    opt_type = ql.Option.Call if CONTRACT.right == 0 else ql.Option.Put;
    payoff = ql.PlainVanillaPayoff(opt_type, CONTRACT.strike);
    exercise = EXERCISE_TYPE(ql.Date(EVAL_DATE.day, EVAL_DATE.month, EVAL_DATE.year), ql.Date(CONTRACT.expiry.day, CONTRACT.expiry.month, CONTRACT.expiry.year));
    return {
        "model" : ql.VanillaOption(payoff, exercise),
        "price" : CONTRACT.last_price,
        "volume" : CONTRACT.volume,
        "open_interest" : CONTRACT.open_interest,
        'class': 'call' if CONTRACT.right == 0 else 'put',
        "iv": None,
        "greeks" : None,
        "eval_date": EVAL_DATE,
        "expiry": CONTRACT.expiry,
        "dte": (CONTRACT.expiry - EVAL_DATE).days
    }

def IV(ARG, DATE):
    """
     arg[0] - option, arg[1] - MARKET
     arg[2] - range, arg[3] - step
     arg[4] - maximum, arg[5] - dummy vol
    """
    dummy_vol = ql.BlackVolTermStructureHandle(ql.BlackConstantVol(DATE,ARG[1]['state']['calendar'],ARG[5],ARG[1]['state']['count_of_days']))
    bsm_process = PROCESS(ARG[1],dummy_vol, DATE)
    try:
        return ql.SimpleQuote(ARG[0]['model'].impliedVolatility(ARG[0]['price'],bsm_process,ARG[2][0],ARG[3],ARG[2][1],ARG[4]))
    except:
        #print('Error calculation of iv, this means the option contract is problematic')
        return ql.SimpleQuote(0.0)

def PRICING_MODEL(OPTION, MARKET, MODEL, ADJUSTMENT, IV, IV_ARGUEMENT, DATE):
    """
    adjustment - 0: model type; 1: steps
    model - pricing model e.g ql.BinomialVanillaEngine
    iv - iv calculator function; iv_arguememts: parameter
    """
    OPTION['iv'] = IV(IV_ARGUEMENT, DATE); 
    implied_vol = ql.BlackVolTermStructureHandle(ql.BlackConstantVol(DATE, MARKET['state']['calendar'], ql.QuoteHandle(OPTION['iv']) , MARKET['state']['count_of_days']))
    bsm_process = PROCESS(MARKET, implied_vol, DATE)
    ENGINE = MODEL(bsm_process,ADJUSTMENT[0], ADJUSTMENT[1])
    OPTION['model'].setPricingEngine(ENGINE)
    return OPTION

def GREEKS(OPTION,TYPE,VALUES,H):
    greeks = {'delta': OPTION['model'].delta(), 'gamma': OPTION['model'].gamma(), 'theta': OPTION['model'].theta(), 'rho': None, 'vega': None}
    p0 = OPTION['model'].NPV();
    #print(p0)
    r = VALUES['rfr'].value(); VALUES['rfr'].setValue(r + H);
    rho = (OPTION['model'].NPV() - p0) / H; VALUES['rfr'].setValue(r);
    print(rho, p0)
    iv = OPTION['iv'].value(); OPTION['iv'].setValue(iv + H);
    vega = (OPTION['model'].NPV() - p0) / H; OPTION['iv'].setValue(iv)
    greeks['vega'] = vega if type == 'american' else OPTION['model'].vega();
    greeks['rho'] = rho if type == 'american' else OPTION['model'].rho();
    return greeks
#---------------------------------------
#             :BACKTEST:               #
#---------------------------------------
def BACKTESTER(ENVIRONMENT,MARKET, PORTFOLIO):
    _EVENTMANAGER = EventManager();
    for (_symb, _d), ROW in MARKET['chart']['price'].iterrows():
        _d = _d.to_pydatetime()
        ENVIRONMENT.domain.set_date_time(_d);
        ql.Settings.instance().evaluationDate = ql.Date(_d.day,_d.month,_d.year);
        # HANDLE THE EVENTS
        _EVENTMANAGER.MARKET_SCHEDULE(_d);
        if _EVENTMANAGER.EVENT_HANDLER(_d,PORTFOLIO, ROW):
            # after the events are handled, run the strategy
            PORTFOLIO.strategy(ENVIRONMENT,PORTFOLIO, MARKET, ROW);
