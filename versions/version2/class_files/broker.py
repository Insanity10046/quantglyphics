import pandas as M_PD;
import datetime as M_DT;
import sys, os;
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from position import Position;

class Broker:
    def __init__(self, COMISSION: float, TRANSACTION_COST: float, EXPECTED_SLIPPAGE: float, EXPECTED_VOL_SLIPPAGE: float):
        self.comission = COMISSION;
        self.transaction_cost = TRANSACTION_COST;
        self.slippage = EXPECTED_SLIPPAGE;
        self.vol_slippage = EXPECTED_VOL_SLIPPAGE;
    #
    def MARK_TO_MARKET(self, PORTFOLIO: type, CURRENT_PRICE: float) -> None:
        return [position.UPDATE_PNL(CURRENT_PRICE) for position in PORTFOLIO.positions if position.executed == True];

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
            'type': POSITION.order_type,
            'size': POSITION.size,
            'entry': POSITION.entry_price,
            'exit': EXIT_PRICE,
            'entry_time': POSITION.entry_date,
            'exit_time': TIME,
            'pnl': POSITION.pnl,
            'comission': POSITION.commission
        })
        PORTFOLIO.positions.remove(POSITION)
    def OPEN_ORDER(self,PORTFOLIO: type, ORDER_PARAMETER: list) -> list:
        order = Position(ORDER_PARAMETER, PORTFOLIO);
        order.commission = self.comission;
        PORTFOLIO.positions.append(order);
    # :VVV:
    def EXECUTION_MODEL(self,PORTFOLIO: type, ORDER_PARAMETER: list, MARKET: None) -> int:
        date = MARKET.GET_CURRENT_DATE();
        if ORDER_PARAMETER['decision'] == 'close':
            position = next((obj for obj in PORTFOLIO.positions if obj.id == ORDER_PARAMETER['order']), None);
            pnl = position.pnl;
            self.CLOSE_ORDER(PORTFOLIO,MARKET.GET_VALUE(float,MARKET.current_slice['Close'],date),date,position);
            return pnl;
        # MAKE SURE the portfolio has enough money just like in a realistic setting
        if PORTFOLIO.capital > 1:
            PORTFOLIO.capital -= self.comission;
            self.OPEN_ORDER(PORTFOLIO,ORDER_PARAMETER);
    def HANDLE_SL_AND_TP(self, QLCONTEXT, CURRENT_PRICE):
        date = QLCONTEXT.MarketEnvironment.GET_CURRENT_DATE();
        portfolio = QLCONTEXT.Portfolio;
        for position in portfolio.positions:
            if position.executed == True:
                logic = position.SL_AND_TP_LOGIC(CURRENT_PRICE);
                if logic:
                    pnl = self.EXECUTION_MODEL(portfolio,
                                               {
                                                   'decision': 'close',
                                                   'order': position.id
                                                   },
                                               QLCONTEXT.MarketEnvironment
                                               );
                    portfolio.capital += pnl;
