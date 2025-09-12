import yfinance as M_YF;
import pandas as M_PD;
import datetime as M_DT;

#---------------------------------------
#               :HELPER:               #
#---------------------------------------
FIELDS = ['Open', 'High', 'Low', 'Close'];
#---------------------------------------
#                :CLASS:               #
#---------------------------------------
class Context:
    def __init__(self, BROKERS: None, PORTFOLIOS: None, MARKET: type):
        self.BrokerageModel = BROKERS;
        self.Portfolio = PORTFOLIOS;
        self.MarketEnvironment = MARKET;

class EventManager:
    def __init__(self):
        self.market_status: str = 'close';
    def MARKET_SCHEDULE(self,DATE: M_DT.datetime) -> bool:
        self.market_status: str = 'open' if DATE.weekday() >= 4 else 'close';
    def ORDER_MANAGEMENT(self, QLCONTEXT: type, CURRENT_PRICE: float) -> list:
        return [position for position in QLCONTEXT.Portfolio.positions if position.executed == False];
    def ON_NEW_PRICE(self, QLCONTEXT: type, PRICE: None) -> None:
        QLCONTEXT.BrokerageModel.MARK_TO_MARKET(QLCONTEXT.Portfolio, PRICE);
    def EVENT_MANAGEMENT(self, TIME: M_DT.datetime, QLCONTEXT: type, PRICE: float) -> bool:
        self.MARKET_SCHEDULE(DATE=TIME);
        if self.market_status == 'open':
            if TIME.weekday() <= 4:
                orders_to_process = self.ORDER_MANAGEMENT(QLCONTEXT, PRICE);
                for position in orders_to_process:
                    QLCONTEXT.BrokerageModel.HANDLE_ORDER_TYPE(position, PRICE)
            return True;
        self.ON_NEW_PRICE(QLCONTEXT, PRICE);
        return False;

class MarketEnvironment:
    def __init__(self,TICKER: str,CHART: M_PD.DataFrame, START: M_DT.datetime, END: M_DT.datetime, RESOLUTION: str):
        self.ticker = TICKER;
        self.chart = CHART;
        self.start = START;
        self.end = END;
        self.resolution = RESOLUTION;
        self.current_slice = None;
    def SET_DATA_ATTRIBUTES(self,INTEREST: None,DIVIDEND: None) -> dict:
        # Reindex interest and dividend data to match the chart index and forward fill missing values
        self.interest = INTEREST.reindex(self.chart.index, method='ffill')
        self.dividend = DIVIDEND.reindex(self.chart.index, method='ffill')
    def GET_INTEREST_RATE(self,TARGET) -> list:
        return self.interest.loc[TARGET];
    def GET_DIVIDEND_YIELD(self,TARGET) -> list:
        return self.dividend.loc[TARGET];
    def GET_VALUE(self,DATA_TYPE: type,FIELD: None, DATE: M_DT.datetime) -> type:
        return next(value for value in FIELD if isinstance(value, DATA_TYPE));
    def UPDATE(self, SLICE: None) -> None:
        self.current_slice = SLICE;
    def GET_CURRENT_DATE(self) -> M_DT.datetime:
        return self.current_slice.name;

class Position:
    def __init__(self, ORDER_PARAMETER: list, PORTFOLIO: type):
        self.asset = ORDER_PARAMETER['asset'];
        self.comission = 0.0;
        self.leverage = ORDER_PARAMETER['leverage'];
        self.size = ORDER_PARAMETER['size'];
        self.entry_price = ORDER_PARAMETER['entry'];
        self.entry_date = ORDER_PARAMETER['time'];
        self.stop_loss = ORDER_PARAMETER['stop_loss'];
        self.direction = ORDER_PARAMETER['direction'];
        self.order_type = ORDER_PARAMETER['order_type'];
        self.executed = False;
        self._last_price = self.entry_price;
        self.pnl = 0;
        self.parent = PORTFOLIO;
    def UPDATE_PNL(self, CURRENT_PRICE: float) -> None:
        self._last_price = CURRENT_PRICE;
        calculation = (self._last_price - self.entry_price) if self.direction == 'long' else (self.entry_price - self._last_price);
        self.pnl = calculation * (self.size * self.leverage) - self.comission;
    def EXECUTE(self, ENTRY_PRICE: float) -> bool:
        self.executed = True;
        self.entry_price = ENTRY_PRICE;
        self.order_type = None;
    def ENTRY_TRIGGER(self,COMPARING_PRICE: float,CURRENT_PRICE: float) -> bool:
        if self.direction == 'long' and COMPARING_PRICE >= CURRENT_PRICE:
            return True;
        if self.direction == 'short' and self.entry_price <= CURRENT_PRICE:
            return True;
        return False;

class Portfolio:
    def __init__(self, DEPOSIT: float, STRATEGY):
        self.capital = DEPOSIT
        self.intial_capital = self.capital;
        self.positions = [];
        self.trade_history = [];
        self.strategy = STRATEGY;

class Broker:
    def __init__(self, COMISSION: float, TRANSACTION_COST: float, EXPECTED_SLIPPAGE: float, EXPECTED_VOL_SLIPPAGE: float):
        self.comission = COMISSION;
        self.transaction_cost = TRANSACTION_COST;
        self.slippage = EXPECTED_SLIPPAGE;
        self.vol_slippage = EXPECTED_VOL_SLIPPAGE;
    #
    def MARK_TO_MARKET(self, PORTFOLIO: type, CURRENT_PRICE: float) -> None:
        for position in PORTFOLIO.positions:
            if position.executed:
                position.UPDATE_PNL(CURRENT_PRICE)

    def ORDER_LIMIT(self,POSITION: type, CURRENT_PRICE: float) -> None:
        if POSITION.ENTRY_TRIGGER(POSITION.entry_price,CURRENT_PRICE):
            POSITION.EXECUTE(CURRENT_PRICE);
    def MARKET_ORDER(self,POSITION: type,CURRENT_PRICE: float) -> None:
        POSITION.EXECUTE(CURRENT_PRICE);
    def STOPLOSS_HIT(self,POSITION: type, CURRENT_PRICE: float) -> None:
        if POSITION.stop_loss and POSITION.ENTRY_TRIGGER(POSITION.stop_loss,CURRENT_PRICE):
            ...
    def STOP_LIMIT(self,POSITION: type, CURRENT_PRICE: float) -> None:
        if POSITION.ENTRY_TRIGGER(POSITION.stop_loss, CURRENT_PRICE):
            self.order_type = 'limit';
            self.stop_loss = None;

    def HANDLE_ORDER_TYPE(self,POSITION: type, CURRENT_PRICE: float) -> None:
        if POSITION.order_type == 'limit':
            self.ORDER_LIMIT(POSITION,CURRENT_PRICE);
        if POSITION.order_type == 'stop_limit':
            self.STOP_LIMIT(POSITION,CURRENT_PRICE);
        if POSITION.order_type == 'market_order':
            self.MARKET_ORDER(POSITION,CURRENT_PRICE);
    #
    def CLOSE_ORDER(self,PORTFOLIO: type, EXIT_PRICE: float, TIME: M_DT.datetime, POSITION: type) -> list:
        PORTFOLIO.trade_history.append({
            'id': POSITION.id,
            'type': position.type,
            'size': POSITION.size,
            'entry': POSITION.entry,
            'exit': EXIT_PRICE,
            'entry_time': POSITION.entry_time,
            'exit_time': TIME,
            'pnl': POSITION.pnl,
            'comission': POSITION.commission
        })
        PORTFOLIO.positions.remove(position)
    def OPEN_ORDER(self,PORTFOLIO: type, ORDER_PARAMETER: list) -> list:
        order = Position(ORDER_PARAMETER, PORTFOLIO);
        order.commission = self.comission;
        PORTFOLIO.positions.append(order);
    # :VVV:
    def EXECUTION_MODEL(self,PORTFOLIO: type, ORDER_PARAMETER: list, MARKET: None) -> int:
        if ORDER_PARAMETER['decision'] == 'close':
            date = MARKET.GET_CURRENT_DATE();
            position = next((obj for obj in PORTFOLIO.positions if obj.id == ORDER_PARAMETER['order']), None);
            self.CLOSE_ORDER(PORTFOLIO, MARKET.GET_VALUE(float, MARKET.current_slice['Close'], date),date, position);
            return position.CALCULATE_PNL()
        PORTFOLIO.capital -= self.comission;
        self.OPEN_ORDER(PORTFOLIO,ORDER_PARAMETER);

#---------------------------------------
#                :MODEL:               #
#---------------------------------------
def BACKTEST(MARKET,QLCONTEXT):
    EventManagement = EventManager();
    QLCONTEXT.MarketEnvironment = MARKET;
    t = 0;
    for row_tuple in MARKET.chart.itertuples():
        date = row_tuple.Index.to_pydatetime()
        MARKET.UPDATE(SLICE=MARKET.chart.loc[date])
        # HANDLE THE EVENTS
        if EventManagement.EVENT_MANAGEMENT(date,QLCONTEXT, MARKET.GET_VALUE(float,MARKET.current_slice['Close'],date)):
            # after the events are handled, run the strategy
            if QLCONTEXT.Portfolio.capital > 0:
                QLCONTEXT.Portfolio.strategy(QLCONTEXT);
