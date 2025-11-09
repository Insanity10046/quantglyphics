class Portfolio:
    def __init__(self, DEPOSIT: float, STRATEGY):
        self.capital = DEPOSIT
        self.initial_capital = self.capital;
        self.positions = [];
        self.trade_history = [];
        self.strategy = STRATEGY;

