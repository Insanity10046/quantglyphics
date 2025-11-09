import uuid as M_UID;

class Position:
    def __init__(self, ORDER_PARAMETER: list, PORTFOLIO: type):
        self.asset = ORDER_PARAMETER['asset'];
        self.comission = 0.0;
        self.leverage = ORDER_PARAMETER['leverage'];
        self.size = ORDER_PARAMETER['size'];
        self.entry_price = ORDER_PARAMETER['entry'];
        self.entry_date = ORDER_PARAMETER['time'];
        self.take_profit = ORDER_PARAMETER.get('take_profit');
        self.stop_loss = ORDER_PARAMETER.get('stop_loss');
        self.direction = ORDER_PARAMETER['direction'];
        self.order_type = ORDER_PARAMETER['order_type'];
        self.executed = False;
        self._last_price = self.entry_price;
        self.pnl = 0;
        self.id = M_UID.uuid4();
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
    def SL_AND_TP_LOGIC(self, CURRENT_PRICE: float) -> bool:
        if not self.take_profit and not self.stop_loss:
            return False;
        if self.direction == 'long':
            if CURRENT_PRICE >= self.take_profit:
                return 'take profit';
            if CURRENT_PRICE <= self.stop_loss:
                return 'stop loss';
        if self.direction == 'short':
            if CURRENT_PRICE <= self.take_profit:
                return 'take_profit';
            if CURRENT_PRICE >= self.stop_loss:
                return 'stop_loss';


