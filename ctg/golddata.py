import numpy as np
import pandas as pd
import yfinance
import pandas_datareader as pdr


yfinance.pdr_override()


class GoldData:
    def __init__(self, start_date = None, end_date = None):        
        if start_date == None:
            self.start_date = pd.Timestamp('2023-05-19')
            
        if end_date == None:
            # Date must be: 
            # synchronized with UTC, but without timezone inside a DataFrame
            # end_date must add 1 day, because yfinance/pandas data-reader API
            # uses end_date exclusive (it is not inclusive)
            self.end_date = pd.Timestamp.today(tz='UTC').normalize()\
                            .tz_localize(None) + pd.Timedelta(1,'day')
            
        self.df = self.initiate_data()
        
    def initiate_data(self):
        """Creates raw gold data"""
        df = pdr.data.get_data_yahoo(
            'GC=F',
            start=self.start_date,
            end=self.end_date
        )        
        df = df.loc[:,'Close'].to_frame()
        df.index.name = 'date'
        df.columns = ['close']        
        return df