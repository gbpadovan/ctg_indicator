import os
import time
import numpy as np
import pandas as pd
import requests
from tqdm import tqdm

from .directories import Directories
from .quoteapis import GeckoAPI, DexScreenerAPI


class TokenData:
    """Fetchs data from CoinGecko & DexScreener API and creates DataFrame
    """    
    def __init__(self):
        self.gkapi = GeckoAPI()
        self.dsapi = DexScreenerAPI()
        self.cols = ['date','token','close','volume','mktcap']
        #self.pkldir = os.path.join(os.getcwd(),'pkl')
        self.pkldir = Directories().token_database
        self.token_pairs = Directories().token_pairs
        self._token_name = None

    @property
    def token_name(self):
        return self._token_name
    
    @token_name.setter
    def token_name(self, new_value):
        self._token_name = new_value
        return self._token_name
    
    @token_name.deleter
    def token_name(self):
        del self._token_name
        

    @staticmethod
    def normalize_date(date):
        """Coverts date to pd.Timestamp

        :param date: str/np.datetime64/pd.Timestamp  
        :return:
            new_date: pd.Timestamp 
        """
        if isinstance(date,np.datetime64):
            new_date = pd.to_datetime(date)
        elif isinstance(date,str):
            new_date = pd.to_datetime(date,dayfirst=True)
        elif isinstance(date, pd.Timestamp):
            new_date = date
        else:
            raise Exception('different data type')
        return new_date


    def load_dataset(self, token):
        """Loads DataFrame saves as pkl in /pkl

        :param token: str representing the token   
        :return:
            df: pd.DataFrame
        """
        df = pd.read_pickle(os.path.join(self.pkldir, f"{token}.pkl"))
        self.token_name = token
        return df

        
    def get_data(
        self, 
        token, 
        date, 
        resp=None, 
        price=np.nan, 
        mktcap=np.nan, 
        volume=np.nan
    ):
        """Creates a row of data using a json response.
        
        :param token: str
        :param date: str
        :param resp: requests.models.Response, Default = None
        :param price: float or np.nan, Default =np.nan, 
        :param mktcap: int or nan, Default =np.nan, 
        :param volume:int or nan, Default =np.nan
        
        :return:
            One row table as pd.DataFrame       
        """
        self.token_name = token
        
        if resp:
            assert isinstance(resp,requests.models.Response)
            price  = resp.json()['market_data']['current_price']['usd']
            mktcap = resp.json()['market_data']['market_cap']['usd']
            volume = resp.json()['market_data']['total_volume']['usd']
        
        df = pd.DataFrame(
            [[                
                self.normalize_date(date),
                token,
                price,
                mktcap,
                volume
            ]],
            columns=self.cols
        )        
        return df
           

    def save_file(self, df):
        """Saves a file as pkl

        :param df: pd.DataFrame to be saved
        """
        token = df.token.values[0]
        path = os.path.join(self.pkldir, f"{token}.pkl")
        df.to_pickle(path)
        return
        

    def generate_dataset(self, token, start_date, end_date, save, data=None):
        """Generates a dataset, can save it as pkl.

        :param token: str
        :param start_date: str or date like object
        :param end_date: str or date like object
        :param save: bool
        :param data: pd.DataFrame, defult =None
        :return:
            token price table as pd.DataFrame       
        """
        if isinstance(data,pd.DataFrame):
            df = data.copy()
        else:          
            df = pd.DataFrame([],dtype=float)
        
        for date in tqdm(pd.date_range(
            self.normalize_date(start_date),
            self.normalize_date(end_date)               
            ).strftime('%d-%m-%Y')
        ):           
            r = self.gkapi.get_raw_hist_data(token=token, date=date)
            
            if not r:
                raise Exception(f"Problems with {token}|{date}")
                
            new_data = self.get_data(token=token, date=date, resp = r) 
            df       = pd.concat([df,new_data])
            time.sleep(2.01) # waits 2 seconds because the api usage is 30 req/min
        
        df.reset_index(drop=True,inplace=True)
        
        if save:
            self.save_file(df=df)
        return df
        

    def update_dataset(self, token, save=False):
        """
        Updates a dataset saved in pkl.

        :param token: str       
        :return:
            token price table as pd.DataFrame        
        """
        dataset = self.load_dataset(token)

        last_date = dataset.date.tail(1).values[0]
        yesterday = pd.Timestamp.today(tz='UTC').normalize() - pd.Timedelta(days=1)
        
        if last_date == yesterday:
            print(f"Dataset {token} is updated until yesterday {yesterday}. Don't need to update.")
            return dataset
        else:
            next_date = last_date + pd.Timedelta(days=1)
            data = self.generate_dataset(token=token, 
                                         start_date=next_date, 
                                         end_date=yesterday.tz_localize(None), #turn it into naive
                                         save=save,
                                         data=dataset
                                        )
            return data
        

    def find_addr_by_token(
        self, 
        token_name:str, 
        quote_token:str='DAI', 
        pool:str ='v1'
    ):
        """Finds pair address by using token_name.
    
        :param token_name: str
        :param quote_token: str Default = 'DAI', 
        :param pool: str Default='v1'
        :return:
            contract address as str
        """
        #token_df = pd.read_excel('token_pairs.xlsx')
        token_df = pd.read_excel(self.token_pairs)
        
        mask =(token_df.token_name == token_name) &\
              (token_df.quote_token == quote_token) &\
              (token_df.pool == pool)
        
        filtered_df = token_df.loc[mask]
        
        try:
            assert not filtered_df.empty
        except:
            raise Exception('DataFrame empty, verify')

        addr = token_df.loc[mask].pair_address.values[0]

        if pd.isna(addr):
            raise Exception(f'No address found for token: {token_name} | quote_token: {quote_token} | pool: {pool}. Verify the support table.')
        
        return addr
    
    
    def include_last_quote(self, token:str, clean_data:bool=False):
        """Includes last price quote from token to the historical dataset.

        OBS: Assumes data is updated.
        
        :param token_name: str
        :param clean_data: bool Default=False
        :return:
            Historical price data as pd.DataFrame
        """
        df = self.load_dataset(token=token)
        chain= 'pulsechain'
        date = pd.Timestamp.today(tz='UTC').normalize().tz_localize(None)
        pair_address = self.find_addr_by_token(token_name=token)
        price = self.dsapi.get_pair_price(chain,pair_address) # usa api da dexscreener
    
        data = self.get_data(token=token, date=date, price=price)
        df = pd.concat([df,data])
        df.reset_index(inplace=True,drop=True)

        if clean_data:
            df.set_index('date',inplace=True)
            df = df.loc[:,'close'].to_frame()
    
        return df