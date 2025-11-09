import yfinance as M_YF;
import pandas as M_PD;
import datetime as M_DT;
import uuid as M_UID

import sys, os;
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
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

from class_files.broker import Broker;
from class_files.position import Position;
from class_files.portfolio import Portfolio;
from class_files.eventmanager import EventManager;
from class_files.marketenvironment import MarketEnvironment;
from class_files import statistic_analysis;
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
                
