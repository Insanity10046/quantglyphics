import numpy as M_NP;
import pandas as M_PD;
from scipy import stats as M_STATS;
import plotext as M_PLT;

# CORE PERFORMANCE
def TOTAL_RETURN(initial_capital, ending_capital):
    return round(
            ((ending_capital - initial_capital) / initial_capital)
            );

def RETURN_ON_CAPITAL(total_pnl, total_capital_used):
    return round((total_pnl/total_capital_used) * 100);

def CALCULATE_RETURNS(equity_curve):
    returns_series = M_PD.Series(equity_curve).pct_change().dropna();
    return returns_series;


def ANNUALIZED_VOLATILITY(returns_series):#ending_capital):
    return returns_series.std() * M_NP.sqrt(252);
    #M_NP.std(ending_capital) * M_NP.sqrt(252);

def ANNUALIZED_RETURN(ending_capital, initial_capital, returns_series):
    total_return = TOTAL_RETURN(initial_capital, ending_capital);
    n_periods = len(returns_series);
    return (1+total_return)**(n_periods/252) - 1;
    #number_of_days = len(CHART);
    #return (ending_capital - initial_capital)^(1/(number_of_days/365.25)) - 1;


def SHARPE_RATIO(annualized_volatility, annualized_return, interest):
    rfr = interest.mean();
    return (annualized_return - rfr) / annualized_volatility;

def SORTINO_RATIO(returns_series, annualized_return, interest):
    rfr = interest.mean();
    mar = 0 # rfr / 252;
    downside_returns = returns_series[returns_series < mar];
    if len(downside_returns) == 0:
        return M_NP.inf;
    downside_vol = downside_returns.std() * M_NP.sqrt(252);
    if downside_vol == 0:
        return M_NP.inf;
    return (annualized_return - rfr) / downside_vol;

# DRAWDOWN ANALYSIS:
def MAXIMUM_DRAWDOWN(returns_series):
    cumulative = (1 + returns_series).cumprod();
    peak_return = cumulative.expanding().max(); # .cummax();
    drawdown = (peak_return - cumulative) / peak_return;
    return drawdown.max();

def CALMAR_RATIO(annualized_return, maximum_drawdown):
    return annualized_return / maximum_drawdown;

def AVERAGE_DRAWDOWN(equity_curve):
    # Calculate running max and drawdown series
    cumulative =(1 + equity_curve).cumprod();
    running_max = cumulative.expanding().max()
    drawdown_series = (running_max - cumulative) / running_max
    
    # Identify drawdown events: where we are not at a new high
    in_drawdown = drawdown_series > 0
    
    # Find the start and end of each contiguous drawdown block
    drawdown_start = (in_drawdown & ~in_drawdown.shift(1).fillna(False))
    drawdown_end = (~in_drawdown & in_drawdown.shift(1).fillna(False))
    
    start_indices = cumulative.index[drawdown_start]
    end_indices = cumulative.index[drawdown_end]
    
    # If the series ends in a drawdown, we ignore the last event for recovery length
    if len(start_indices) > len(end_indices):
        start_indices = start_indices[:-1]
    
    events = []
    for start, end in zip(start_indices, end_indices):
        event_drawdown_series = drawdown_series.loc[start:end]
        max_drawdown = event_drawdown_series.max()
        trough_time = event_drawdown_series.idxmax() # idxmax returns the index of the maximum drawdown
        peak_to_trough_duration = trough_time - start
        peak_to_recovery_duration = end - start
        
        events.append({
            'max_drawdown': max_drawdown,
            'peak_to_trough_duration': peak_to_trough_duration,
            'peak_to_recovery_duration': peak_to_recovery_duration
        })
    
    # Convert to DataFrame for easy analysis
    events_df = M_PD.DataFrame(events)
    if events_df.empty:
        return 0, 0, 0, None;
    # Calculate Averages
    avg_drawdown = events_df['max_drawdown'].mean()
    avg_drawdown_length_trough = events_df['peak_to_trough_duration'].mean()
    avg_recovery_length = events_df['peak_to_recovery_duration'].mean()
    
    return avg_drawdown, avg_drawdown_length_trough, avg_recovery_length, events_df

def VALUE_AT_RISK(return_series, holding_period, confidence_interval, ending_capital):
    if holding_period > 1:
        return_series = return_series.rolling(window=holding_period).sum().dropna();
    var_percentage = -M_NP.percentile(return_series, (1 - confidence_interval)*100);
    var_currency = var_percentage * ending_capital;
    return var_percentage, var_currency;

def CONDITIONAL_VAR(return_series, confidence_interval, var_percentage):
    sorted_returns = return_series.sort_values();
    var_index = int((1 - confidence_interval) * len(sorted_returns));
    var_sorted = sorted_returns[var_index];
    tail_returns = return_series[return_series <= -var_percentage];
    cvar = -tail_returns.mean();
    return tail_returns, cvar;

# TRADE ANALYSIS & EFFICIENCY

def WIN_RATE(trade_history):
    wins = 0;
    for position in trade_history:
        if position['pnl'] > 0:
            wins+=1;
    return wins / len(trade_history);

def PROFIT_FACTOR(trade_history):
    win_profit = 0;
    loss_profit = 0;
    for position in trade_history:
        if position['pnl'] > 0:
            win_profit+=position['pnl'];
        else:
            loss_profit+=position['pnl'];
    return  M_NP.absolute(win_profit) / M_NP.absolute(loss_profit);

def AVERAGE_WIN_LOSSES(trade_history):
    avg_win = 0;
    total_win = 0;
    avg_loss = 0;
    total_loss = 0;
    for position in trade_history:
        if position['pnl'] > 0:
            avg_win += position['pnl'];
            total_win+=1;
        if position['pnl'] < 0:
            avg_loss += position['pnl'];
            total_loss+=1;
    avg_win = avg_win / total_win;
    avg_loss = avg_loss / total_loss;
    return avg_win, avg_loss;

def EXPECTED_VALUE_PER_TRADE(win_rate, avg_win, avg_loss):
    return (win_rate * avg_win) + ((1 - win_rate) * avg_loss);#(win_rate * avg_win) - ((1 - win_rate) * avg_loss);

def K_RATIO(return_series):
    #if return_series.iloc[0] != 0:
    #    return_series = return_series / return_series.iloc[0] - 1
    y = M_NP.log(1 + return_series);
    x = M_NP.arange(1, len(y) + 1);
    slope, intercept, r_value, p_value, std_err = M_STATS.linregress(x,y);
    k_ratio = slope / std_err;
    return k_ratio;

# STATISTICAL ROBUSTNESS
def ALPHA_BETA(return_series, benchmark_return, interest, days):
    # Use the minimum length between the two series
    min_length = min(len(return_series), len(benchmark_return))
    
    return_series_trimmed = return_series.iloc[:min_length] if hasattr(return_series, 'iloc') else return_series[:min_length]
    benchmark_return_trimmed = benchmark_return.iloc[:min_length] if hasattr(benchmark_return, 'iloc') else benchmark_return[:min_length]
    
    rfr = interest.mean();
    strategy_excess = return_series_trimmed - rfr
    benchmark_excess = benchmark_return_trimmed - rfr
    
    X = M_NP.column_stack([M_NP.ones(len(benchmark_excess)), benchmark_excess])
    alpha, beta = M_NP.linalg.lstsq(X, strategy_excess, rcond=None)[0]
    
    if days > 252:
        alpha = alpha * 252
    return alpha, beta
"""
def ALPHA_BETA(return_series, benchmark_return, interest, days):
    rfr = interest.mean() * 252;
    strategy_excess = return_series - rfr;
    benchmark_excess = benchmark_return - rfr;
    X = M_NP.column_stack([M_NP.ones(len(benchmark_excess)), benchmark_excess]);
    alpha, beta = M_NP.linalg.lstsq(X, strategy_excess, rcond=None)[0];
    if days > 252:
        alpha = alpha * 252;
    return alpha, beta;
"""

def T_STATISTICS(annualized_return, annualized_volatility, number_of_years):
    return annualized_return / annualized_volatility / M_NP.sqrt(number_of_years);

def SKEW(return_series):
    return M_STATS.skew(return_series, bias=False);

def KURTOSIS(return_series):
    return M_STATS.kurtosis(return_series, bias=False);

def NORMALISE_TO_BASE(return_series):
    cumulative_return =  (1 +  return_series).cumprod();
    cumulative_return = cumulative_return.replace([M_NP.inf, -M_NP.inf], M_NP.nan).dropna()
    return cumulative_return / cumulative_return.iloc[0] * 100;

def BENCHMARK(return_series, benchmark_return, width=60, height=20):
    M_PLT.clear_figure();
    M_PLT.plot(NORMALISE_TO_BASE(return_series), label='trading strategy return');
    M_PLT.plot(benchmark_return, label='benchmark');
    M_PLT.title('Benchmark v Trading Strategy Return');
    M_PLT.xlabel("Time Period");
    M_PLT.ylabel("Performance");
    M_PLT.clear_color();
    M_PLT.show();

def EQUITY_CURVE(initial_capital, trade_history):
    portfolio_value = [initial_capital];
    current_value = initial_capital;
    for position in trade_history:
        current_value+=position['pnl'];
        portfolio_value.append(current_value);
    return portfolio_value;

def CALCULATE_TOTAL_MONEY_USED(trade_history):
    total_capital_used = 0;
    for position in trade_history:
        total_capital_used+=position['comission'];
    return total_capital_used;

def HELPER_FUNCTION(data, check, string):
    if data.get(check) is not None:
        value = data.get(check)
        
        # Define rounding rules based on the metric type
        formatting_rules = {
            # Ratios - keep 4 decimals
            'sharpe_ratio': lambda x: f"{x:.4f}",
            'sortino_ratio': lambda x: f"{x:.4f}",
            'calmar_ratio': lambda x: f"{x:.4f}",
            'profit_factor': lambda x: f"{x:.4f}",
            'k_ratio': lambda x: f"{x:.4f}",
            
            # Percentages - show as percentage with 2 decimals
            'win_rate': lambda x: f"{x:.2%}",
            'total_return': lambda x: f"{x:.2%}",
            'annualized_return': lambda x: f"{x.real:.2%}" if isinstance(x, complex) else f"{x:.2%}",
            'maximum_drawdown': lambda x: f"{x:.2%}",
            'average_drawdown': lambda x: f"{x:.2%}",
            
            # Volatility and similar - 4 decimals
            'annualized_volatility': lambda x: f"{x:.4f}",
            
            # Money values - 2 decimals
            'avg_win': lambda x: f"{x:.2f}",
            'avg_loss': lambda x: f"{x:.2f}",
            'expected_value_per_trade': lambda x: f"{x:.2f}",
            
            # Very small values - 6 decimals
            'value_at_risk': lambda x: f"{x:.6f}",
            'cvar': lambda x: f"{x:.6f}",
            'beta': lambda x: f"{x:.6f}",
            
            # Statistics - 4 decimals
            'alpha': lambda x: f"{x:.4f}",
            'skew': lambda x: f"{x:.4f}",
            'kurtosis': lambda x: f"{x:.4f}",
            
            # Time periods - 1 decimal
            'AVERAGE_DRAWDOWN_LENGTH_TIME': lambda x: f"{x:.1f}",
            'AVERAGE_RECOVERY_LENGTH_TIME': lambda x: f"{x:.1f}",
        }
        
        # Apply formatting if rule exists, otherwise convert to string
        if check in formatting_rules:
            formatted_value = formatting_rules[check](value)
        else:
            formatted_value = str(value)
        
        print(f'# {string}: {formatted_value}')
        return True
    return False

def WRITE_EXTENSIVE_REPORT(data):
    if data['benchmark'] is not None:
        BENCHMARK(data['return_series'], data['benchmark']);
    print("# -------------------------------------------------------- #");
    print("#                      EXTENSIVE REPORT                    #");
    print("# -------------------------------------------------------- #");
    print("+ -------------------- CORE PERFORMANCE ------------------ +");
    HELPER_FUNCTION(data,'total_return', 'TOTAL_RETURN');
    HELPER_FUNCTION(data,'return_on_capital', 'RETURN ON CAPITAL');
    HELPER_FUNCTION(data,'annualized_volatility', 'ANNUALIZED VOLATILITY');
    HELPER_FUNCTION(data,'annualized_return', 'ANNUALIZED RETURN');
    HELPER_FUNCTION(data,'sharpe_ratio', 'SHARPE RATIO');
    HELPER_FUNCTION(data,'sortino_ratio', 'SORTINO RATIO');
    print("+ ------------------- DRAWDOWN ANALYSIS ------------------ +");
    HELPER_FUNCTION(data,'maximum_drawdown', 'MAXIMUM DRAWDOWN');
    HELPER_FUNCTION(data,'calmar_ratio', 'CALMAR RATIO');
    if HELPER_FUNCTION(data,'average_drawdown', 'AVERAGE DRAWDOWN'):
        print(f'# AVERAGE DRAWDOWN LENGTH TIME: {data['average_drawdown_length_trough']}');
        print(f'# AVERAGE RECOVERY LENGTH TIME: {data['average_recovery_length']}');
    HELPER_FUNCTION(data,'value_at_risk', 'VALUE AT RISK(VAR)');
    HELPER_FUNCTION(data,'cvar', 'CONDITIONAL VALUE AT RISK(CVAR)');
    print("+ --------------------- TRADE ANALYSIS ------------------- +");
    HELPER_FUNCTION(data,'win_rate', 'WIN RATE');
    HELPER_FUNCTION(data,'profit_factor', 'PROFIT FACTOR');
    HELPER_FUNCTION(data,'avg_win', 'AVERAGE WIN');
    HELPER_FUNCTION(data,'avg_loss', 'AVERAGE LOSS');
    HELPER_FUNCTION(data,'expected_value_per_trade','EXPECTED VALUE PER TRADE');
    HELPER_FUNCTION(data,'k_ratio', 'K RATIO');
    print("+ ------------------ STATISTIC ROBUSTNESS ---------------- +");
    HELPER_FUNCTION(data,'alpha', 'ALPHA');
    HELPER_FUNCTION(data,'beta', 'BETA');
    HELPER_FUNCTION(data,'t_statistic', 'T STATISTIC');
    HELPER_FUNCTION(data,'skew', 'SKEW');
    HELPER_FUNCTION(data,'kurtosis', 'KURTOSIS');
    print("+ -------------------------------------------------------- +");
    HELPER_FUNCTION(data, 'initial_capital', 'INITIAL CAPITAL');
    HELPER_FUNCTION(data, 'ending_capital', 'ENDING CAPITAL');
    print("+ -------------------------------------------------------- +");

