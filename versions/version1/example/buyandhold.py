import quantglyphics as M_QLY
import yfinance as M_YF
import datetime as M_DT
# ------ test ------
MyPortfolio = M_QLY.Portfolio(DEPOSIT=100000, STRATEGY=None);
IBKR = M_QLY.Broker(
        COMISSION=10,
        TRANSACTION_COST=0.5,
        EXPECTED_SLIPPAGE=0.5,
        EXPECTED_VOL_SLIPPAGE=1.0
);
# get data:
SPY_data = M_YF.download(tickers='SPY', start='2008-01-01', end='2025-01-01',interval='1d',actions=True)
SPY_Environment = M_QLY.MarketEnvironment(
        TICKER='SPY',
        CHART=SPY_data,
        START=M_DT.datetime(2008,1,1),
        END=M_DT.datetime(2025,1,1),
        RESOLUTION='1d'
);
SPY_Interest = M_YF.download(tickers='^TNX',start='2008-01-01', end='2025-01-01',interval='1d');
SPY_Dividend = SPY_Environment.chart['Dividends'];
SPY_Environment.SET_DATA_ATTRIBUTES(SPY_Interest,SPY_Dividend);
QLContext = M_QLY.Context(BROKERS=IBKR,PORTFOLIOS=MyPortfolio,MARKET=None);

def BuyAndHold_Strategy(QLCONTEXT):
    _Market = QLCONTEXT.MarketEnvironment;
    _Portfolio = QLCONTEXT.Portfolio
    current_date = _Market.GET_CURRENT_DATE()

    dividend = _Market.GET_DIVIDEND_YIELD(current_date);
    interest = _Market.GET_INTEREST_RATE(current_date);

    QLCONTEXT.BrokerageModel.EXECUTION_MODEL(
        _Portfolio,
        {
            'asset': _Market.ticker,
            'size': 1,
            'leverage': 1.5,
            'entry': _Market.GET_VALUE(float, _Market.current_slice['Close'], current_date),
            'time': current_date,
            'stop_loss': None,
            'direction': 'long',
            'order_type': 'market_order',
            'decision': 'open'
        }, # -- order_parameter
        _Market
    );
    if current_date == _Market.chart.tail(1)['Close'].index[0]:
        for position in QLCONTEXT.Portfolio.positions:
            QLCONTEXT.Portfolio.capital+=QLCONTEXT.BrokerageModel.EXECUTION_MODEL(
                QLCONTEXT.Portfolio,
                {
                    'decision': 'close',
                    'order': position.id
                },
                QLCONTEXT.MarketEnvironment
            )

MyPortfolio.strategy = BuyAndHold_Strategy;
M_QLY.BACKTEST(SPY_Environment, QLContext)

total_pnl = 0;
for position in MyPortfolio.trade_history:
    total_pnl += position['pnl']
print(f"total pnl:{total_pnl}");
print(MyPortfolio.capital)
