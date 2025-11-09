import sys;
import os;
import yfinance as M_YF;
import datetime as M_DT;
import pandas as M_PD;

current_dir = os.path.dirname(os.path.abspath(__file__));
parent_dir = os.path.dirname(current_dir);
sys.path.insert(0, parent_dir);

from quantglyphics import main as M_QLY;
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
SPY_Interest = M_YF.download(tickers='^IRX',start='2008-01-01', end='2025-01-01',interval='1d');
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

def BACKTEST_METRIC(interest, MyPortfolio, benchmark, number_of_years, days):
    equity_curve = M_QLY.statistic_analysis.EQUITY_CURVE(MyPortfolio.initial_capital, MyPortfolio.trade_history);
    return_series = M_QLY.statistic_analysis.CALCULATE_RETURNS(equity_curve);
    # core performance -- + 
    total_capital_used = M_QLY.statistic_analysis.CALCULATE_TOTAL_MONEY_USED(MyPortfolio.trade_history);
    total_return = M_QLY.statistic_analysis.TOTAL_RETURN(MyPortfolio.initial_capital, MyPortfolio.capital);
    return_on_capital = M_QLY.statistic_analysis.RETURN_ON_CAPITAL(return_series.sum(), total_capital_used);
    annualized_volatility = M_QLY.statistic_analysis.ANNUALIZED_VOLATILITY(return_series);
    annualized_return = M_QLY.statistic_analysis.ANNUALIZED_RETURN(MyPortfolio.capital, MyPortfolio.initial_capital, return_series);
    sharpe_ratio = M_QLY.statistic_analysis.SHARPE_RATIO(annualized_volatility, annualized_return, interest);
    sortino_ratio = M_QLY.statistic_analysis.SORTINO_RATIO(return_series, annualized_return, interest);
    # drawdown analysis -- +
    maximum_drawdown = M_QLY.statistic_analysis.MAXIMUM_DRAWDOWN(return_series);
    calmar_ratio = M_QLY.statistic_analysis.CALMAR_RATIO(annualized_return, maximum_drawdown);
    average_drawdown, avg_drawdown_length_trough, avg_recovery_length, events_df = M_QLY.statistic_analysis.AVERAGE_DRAWDOWN(return_series);
    value_at_risk, var_currency = M_QLY.statistic_analysis.VALUE_AT_RISK(return_series, 1, 0.95, MyPortfolio.capital);
    tail_returns, conditional_var = M_QLY.statistic_analysis.CONDITIONAL_VAR(return_series, 0.95, value_at_risk);
    # trade analysis -- +
    win_rate = M_QLY.statistic_analysis.WIN_RATE(MyPortfolio.trade_history);
    profit_factor = M_QLY.statistic_analysis.PROFIT_FACTOR(MyPortfolio.trade_history);
    avg_win, avg_loss = M_QLY.statistic_analysis.AVERAGE_WIN_LOSSES(MyPortfolio.trade_history);
    expected_value_per_trade = M_QLY.statistic_analysis.EXPECTED_VALUE_PER_TRADE(win_rate, avg_win, avg_loss);
    k_ratio = M_QLY.statistic_analysis.K_RATIO(return_series);
    #statistical robustness
    alpha, beta = M_QLY.statistic_analysis.ALPHA_BETA(return_series, benchmark, interest, days);
    t_statistic = M_QLY.statistic_analysis.T_STATISTICS(annualized_return, annualized_volatility,  number_of_years);
    skew = M_QLY.statistic_analysis.SKEW(return_series);
    kurtosis = M_QLY.statistic_analysis.KURTOSIS(return_series);
    M_QLY.statistic_analysis.WRITE_EXTENSIVE_REPORT(
            {
                'benchmark': benchmark,
                'return_series': return_series,
                'total_return': total_return,
                'return_on_capital': return_on_capital,
                'annualized_volatility': annualized_volatility,
                'annualized_return': annualized_return,
                'sharpe_ratio': sharpe_ratio,
                'sortino_ratio': sortino_ratio,
                'maximum_drawdown': maximum_drawdown,
                'calmar_ratio': calmar_ratio,
                'average_drawdown': average_drawdown,
                'average_drawdown_length_trough': avg_drawdown_length_trough,
                'average_recovery_length': avg_recovery_length,
                'value_at_risk': value_at_risk,
                'cvar': conditional_var,
                'win_rate': win_rate,
                'profit_factor': profit_factor,
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'k_ratio': k_ratio,
                'alpha': alpha,
                'beta': beta,
                'skew': skew,
                'kurtosis': kurtosis,
                'expected_value_per_trade': expected_value_per_trade,
                't_statistic': t_statistic,
                'initial_capital': MyPortfolio.initial_capital,
                'ending_capital': MyPortfolio.capital
            }
            )

number_of_years = (SPY_data.iloc[0].name - SPY_data.iloc[-1].name).days / 365.25;
days = (SPY_data.iloc[0].name - SPY_data.iloc[-1].name).days;
BACKTEST_METRIC(SPY_Interest[('Close', '^IRX')], MyPortfolio, SPY_data[('Close', 'SPY')], number_of_years, days);


