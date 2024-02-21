import numpy as np
import pandas as pd
from ta.momentum import ROCIndicator

from .directories import Directories
from .golddata import GoldData
#from tokendata import TokenData


class CTG:
    """
    Crypto to Gold ROC Indicator

    OBS: After mid/2022 Yahoo Finance changed its API, so pandas-datareader is not
    properly working. There is a workaroud using another library (yfinance) in tandem: 

    conda install conda-forge::yfinance

    see: https://github.com/pydata/pandas-datareader/issues/952
    
    """
    def __init__(self, asset_data):
        self.asset_data = asset_data        
        self.gold_data  = GoldData().df
        self.merge_d    = self.adjust_data()
        self._base_data = None
        
       
    @property
    def base_data(self):
        return self._base_data
    
    @base_data.setter
    def base_data(self, new_value):
        self._base_data = new_value
        return self._base_data
    
    @base_data.deleter
    def base_data(self):
        del self._base_data
        return  
   
    
    def adjust_data(self):
        """Merges Token with Gold Data, interpolates missing gold data and creates new column"""
        merge_d = self.asset_data.merge(
            self.gold_data, 
            on='date', 
            how='outer', 
            suffixes=['_token','_gold']
        )        
        
        merge_d['close_gold'] = merge_d.loc[:,'close_gold'].interpolate('linear')
        merge_d['close_ratio_token_vs_gold'] = merge_d.loc[:,'close_token']\
                                               / merge_d.loc[:,'close_gold']
        
        return merge_d

    
    def _add_signal_and_prices(self, df):
        """can only be activated by _create_base_data_by_periodicity

        needs a coulns called roc_p4        
        """
        #df = indicator.create_base_data()
        df = df.assign(is_positive=df.roc_p4.apply(lambda x:1 if x >=0 else 0))
        df['is_positive_shift']  = df.is_positive.shift(1,fill_value=np.nan)
        df.dropna(inplace=True)
        
        conditions = [
            (df['is_positive'] == 1) & (df['is_positive_shift'] == 0), # buy
            (df['is_positive'] == 0) & (df['is_positive_shift'] == 1), # sell
            (df['is_positive'] == df['is_positive_shift'])             # ---   (do nothing)
        ]
        
        choices = ['buy','sell','---']
        choices2 = [1,-1,0]
        
        df['signal'] = np.select(conditions, choices, default=np.nan)
        df['signaln'] = np.select(conditions, choices2, default=np.nan)
        
        # add prices
        df = df.merge(
            self.merge_d.reset_index(drop=False).loc[:,['date','close_token','close_gold']],
            on='date',
            how='inner'
        )
        return df

    
    def _create_base_data_by_periodicity(self, periodicity, interpolate_data, add_signal):
        """Creates a Data Frame with the value of the asset divided by the price of gold
        and calculates the ROC Indicator.
        
        Args:
        -----
        periodicity: str
            Any "W-SUN","W-MON","W-TUE","W-WED","W-THU","W-FRI","W-SAT"            
            
        interpolate_data: bool
            If true, creates new daily rows with interpolated data.
            
        add_signal: bool
            activates method self._add_signal_and_prices(df)
        
        Returns:
        -------       
        data: pd.dataFrame
        
        ================================================================================
        OBS: Quanto a interpolação de dados no data-frame semanal:
        
        Isso serve para "suavizar a linha", na hora de plotar o grafico.
        O df está c/ data semanal:
        i     date    roc
        0  2023-01-01  -1
        1  2023-01-08   6 
        2  2023-01-15  40
        
        A coluna do ROC calcula a taxa de variacao da semana atual com a semana anterior,
        (2023-01-08 com 2023-01-01 e por ai..)
        
        Podemos reconstruir os valores intermediários fazendo uma interpolação linear:

            i     date    roc
            0  2023-01-01  -1            
        =>  1  2023-01-02   0 
        =>  2  2023-01-03   1 
        =>  3  2023-01-04   2 
        =>  4  2023-01-05   3
        =>  5  2023-01-06   4            
        =>  6  2023-01-07   5 
            7  2023-01-08   6
        
        ================================================================================
        """      
        data = self.merge_d.resample(rule=periodicity)\
                   .apply({'close_ratio_token_vs_gold':'last'}).reset_index()
        
        data['roc_p4'] = ROCIndicator(
            close=data['close_ratio_token_vs_gold'], 
            window = 4).roc()
        
        data.dropna(inplace=True)
        data.iloc[-1,0] = pd.Timestamp.today(tz='UTC').normalize().tz_localize(None)  # replaces the last date to today
        
        if interpolate_data:            
            # adds new daily columns with NaN values
            # maintain the value in the columns
            # interpolate values with linear scale
            data = data.resample(rule='d',on='date')\
                   .apply({'close_ratio_token_vs_gold':'last','roc_p4':'last'})\
                   .interpolate('linear')

            if add_signal:
                data = self._add_signal_and_prices(df=data)            
        
        return data    

    
    def create_base_data(self, periodicity="W-SUN"):
        """Creates a Data Frame with the value of the asset divided by the price of gold
        and calculates the ROC Indicator.
        
        Args:
        -----
        periodicity: str
            either 'all' or any "W-SUN","W-MON","W-TUE","W-WED","W-THU","W-FRI","W-SAT"
            Default = "W-SUN"
                               
        Returns:
        -------
        None (default)
        self.base_data: pd.dataFrame (optional)
        """            
        df = pd.DataFrame([], dtype=float)

        #TODO: ver se esta solução é viável
        if periodicity == 'all':            
            periods = ["W-SUN","W-MON","W-TUE","W-WED","W-THU","W-FRI","W-SAT"]
            interpolate_data = False            
            add_signal = False 
        # esta solução é viável e d="W-SUN" é o padrão
        else:
            periods = [periodicity]
            interpolate_data = True
            add_signal = True
            
        for period in periods:
            data = self._create_base_data_by_periodicity(periodicity=period, 
                                                         interpolate_data=interpolate_data,
                                                         add_signal=add_signal)
            df   = pd.concat([df, data])      
      
        self.base_data = df
        
        return self.base_data 