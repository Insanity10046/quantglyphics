import datetime as M_DT;
import pandas as M_PD;
import numpy as M_NP;
# ------------------------------- #
#           FUNCTION              #
# ------------------------------- #
def GET_CURRENT_DATE(current_slice) -> M_DT.datetime:
    # Original approach that worked before
    t = next((x for x in current_slice if isinstance(x, (M_PD.Timestamp, M_DT.datetime, M_DT.date, M_NP.datetime64))), None);
    if not t:
        if current_slice.name and isinstance(current_slice.name, (M_PD.Timestamp, M_DT.datetime, M_DT.date, M_NP.datetime64)):
            return current_slice.name;
        if current_slice.index and isinstance(curent_slice.index, (M_PD.Timestamp, M_DT.datetime, M_DT.date, M_NP.datetime64)):
            return current_slice.index;
    return t;

# ------------------------------- #
#           CALIBRATE             #
# ------------------------------- #
class MarketEnvironment:
    def __init__(self,TICKER: str,CHART: M_PD.DataFrame, START: M_DT.datetime, END: M_DT.datetime, RESOLUTION: str):
        self.ticker = TICKER;
        self.chart = CHART;
        self.start = START;
        self.end = END;
        self.resolution = RESOLUTION;
        self.current_slice = None;
    def SET_DATA_ATTRIBUTES(self,INTEREST: None,DIVIDEND: None) -> dict:
        self.interest = INTEREST.reindex(self.chart.index, method='ffill')
        self.dividend = DIVIDEND;
    def GET_INTEREST_RATE(self,TARGET) -> list:
        return self.interest.loc[TARGET];
    def GET_DIVIDEND_YIELD(self,TARGET) -> list:
        return self.dividend.loc[TARGET];
    def GET_VALUE(self,DATA_TYPE: type,FIELD: None, DATE: M_DT.datetime) -> type:
        return next(value for value in FIELD if isinstance(value, DATA_TYPE));
    def UPDATE(self, SLICE: None) -> None:
        self.current_slice = SLICE;
    def GET_CURRENT_DATE(self) -> M_DT.datetime:
        return GET_CURRENT_DATE(self.current_slice);#return next(value for value in self.current_slice if isinstance(value, M_DT.datetime))#self.current_slice.name;


