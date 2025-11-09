import datetime as M_DT;

class EventManager:
    def __init__(self):
        self.market_status: str = 'close';
    def MARKET_SCHEDULE(self,DATE: M_DT.datetime) -> bool:
        self.market_status: str = 'open' if DATE.weekday() <= 4 else 'close';
    def ORDER_MANAGEMENT(self, QLCONTEXT: type, CURRENT_PRICE: float) -> list:
        return [QLCONTEXT.BrokerageModel.HANDLE_ORDER_TYPE(position,CURRENT_PRICE) for position in QLCONTEXT.Portfolio.positions if position.executed == False];
    def POSITION_MANAGEMENT(self, QLCONTEXT: type, CURRENT_PRICE: float) -> list:
        QLCONTEXT.BrokerageModel.HANDLE_SL_AND_TP(QLCONTEXT, CURRENT_PRICE);
    def ON_NEW_PRICE(self, QLCONTEXT: type, PRICE: None) -> None:
        QLCONTEXT.BrokerageModel.MARK_TO_MARKET(QLCONTEXT.Portfolio, PRICE);
    def EVENT_MANAGEMENT(self, TIME: M_DT.datetime, QLCONTEXT: type, PRICE: float) -> bool:
        self.MARKET_SCHEDULE(DATE=TIME);
        self.ON_NEW_PRICE(QLCONTEXT, PRICE);
        if self.market_status == 'open':
            if 0 < TIME.weekday() <= 4:
                self.POSITION_MANAGEMENT(QLCONTEXT, PRICE);
                self.ORDER_MANAGEMENT(QLCONTEXT, PRICE);
            return True;
        return False;

