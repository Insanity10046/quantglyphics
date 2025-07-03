# ------------------------`--`-----------
def O_P_FUNC(CURRENT, CONTRACT, QTY, ORDER_TYPE, STOP_LOSS, DECISION, DIRECTION):
    return {
        'asset': CURRENT.name[0],
        'contract': CONTRACT,
        'qty': QTY,
        'order_type': ORDER_TYPE,
        'stop_loss': STOP_LOSS,
        'decision': DECISION,
        'direction': DIRECTION
    }
def ON_DATA_FUNC(UNDERLYING, DATA):
    return {
        'daily_vol': UNDERLYING['vol'],
        'bid': DATA['bid'],
        'ask': DATA['ask']
    }
def STRATEGY(ENVIRONMENT,PORTFOLIO, MARKET, CURRENT):
    # -- VARIABLE -- #
    current_date = CURRENT.name[1].to_pydatetime();
    ENVIRONMENT.DATA_RETRIEVAL("UnitedStates", "Actual365Fixed", ql.UnitedStates.NYSE,MARKET, CURRENT['close'], current_date)
    option_chain = ENVIRONMENT.GET_OPTION_CONTRACTS(MARKET['ticker'].symbol)
    for contract in option_chain:
        if contract.volume > 1000000:
            c = OPTION_CONTRACT(contract, current_date, ql.AmericanExercise);
            PORTFOLIO.broker.EXECUTION_MODEL(
                PORTFOLIO,
                O_P_FUNC(CURRENT, c, 1, 'market_order', None, 'open', 'long'),
                CURRENT,
                ON_DATA_FUNC(CURRENT,c)
                )
    print(PORTFOLIO.positions)

start = datetime(1999,1,1)
end = datetime(2024,1,1)
Environment = MarketEnvironment(start,end, Resolution.DAILY);
Market = Environment.SET_ENVIRONMENT('SPY')
My_broker = Broker(
    0.65, # comission
    [0.4,1], # normal slippage, high vol slippage
    [0.03, 0.025, 0.65, 0.006] # ORF, OOC, contract fees, FINRA/CAT/ETC
);
My_portfolio = Portfolio(STRATEGY, [1000], My_broker)

BACKTESTER(Environment,Market,My_portfolio)

# BUG : doesnt locate rfr, and dividend
