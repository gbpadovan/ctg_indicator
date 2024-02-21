import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


class Chart:
    @staticmethod
    def roc_chart(data, start_date=None, end_date=None, token_name=''):
        """Creates a chart for ROC"""
        df = data.copy()
        df.set_index('date',inplace=True) # sets column 'date' as index
        
        if not start_date:
            start_date = df.index[0].strftime("%Y-%m-%d")

        if not end_date:
            end_date = df.index[-1].strftime("%Y-%m-%d")        
        
        df = df.loc[df.index.isin(pd.date_range(start_date,end_date))]
        
        y = df['roc_p4']        
        x = df.index
        
        fig = plt.figure(figsize=(14,7))
        plt.plot(x, y)
        #plt.xscale('log')
        
        plt.title(f"{token_name} ROC Period 4W")
        #plt.ylim([-30, 50])
        plt.grid(True)
        return