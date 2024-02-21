import os
import time
import requests
from dotenv import load_dotenv


load_dotenv()  # take environment variables from .env.


class DexScreenerAPI:
    """API calls are limited to 300 requests per minute"""

    def __init__(self):
        self.url = "https://api.dexscreener.com/latest"


    def get_pair_price(self, chain, pair_addr):
        """Performs request.get on pair price

        :param chain: str
        :param pair_addr: str
        :return:
            response: float
        """
        endpoint = f"/dex/pairs/{chain}/{pair_addr}"
        response = requests.get(self.url + endpoint)
        return float(response.json()['pairs'][0]['priceNative'])


class GeckoAPI():
    """GeckoAPI
    - 30 requests/min
    - resp is json
    
    =>Historical price at dd-mm-yyyy on GMT 0:00:00:
    https://api.coingecko.com/api/v3/coins/{TOKEN}/history?date=dd-mm-yyyy 
    """    
    def __init__(self):
        self.url = 'https://api.coingecko.com/api/v3'
        self.api_url_ext = f"&x_cg_demo_api_key={os.getenv('GECKO_API_KEY')}"
        

    def _get_site(self, url, n_attempts=5, wait=5, **kargs):
        """Performs request.get with retries.

        :param url: str
        :param n_attempts: int  
        :param wait: float  
        :return:
            response: request.response
        """
        attempts = 0
        while attempts < n_attempts:
            try:
                response = requests.get(url)
                if response.status_code == 429:
                    print(f"Server too busy, retrying in {wait} seconds...")
                    attempts += 1
                    time.sleep(wait)
                    continue
                return response
            except Exception as e:
                print(f"Error: {e}")
                attempts += 1
        else:
            print("Error: Maximum number of retries reached")
            return
            
    
    def get_raw_hist_data(self,token, date, **kargs):
        """Fechts historical token data (raw request response)
        according to the date, using CoinGeccko API.

        :param token: str
        :param date: str format = %d-%m-%Y  
    
        :return:
            response: request.response

        ---
        Note:
        Get historical data (price, market cap, 24hr volume, ..) at 
        a given date for a coin.The data returned is at 00:00:00 UTC.
        
        The last completed UTC day (00:00) is available 35 minutes 
        after midnight on the next UTC day (00:35).
        """
        endpoint = f"/coins/{token}/history?date={date}"
        r = self._get_site(url=self.url + endpoint + self.api_url_ext)   
        return r