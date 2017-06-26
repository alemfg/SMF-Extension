#  smf.py - Pyuno/LO bridge to implement new functions for LibreOffice Calc
#
#  Copyright (c) 2013 David Capron (drbluesman@yahoo.com)
#
#  license: GNU LGPL
#
#  This library is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 3 of the License, or (at your option) any later version.
#
import os
import sys
import inspect
import csv
#Try/except is for LibreOffice Python3.x vs. OpenOffice Python2.x.
try:
    from urllib.request import Request, urlopen
    from urllib.error import URLError
except ImportError:
    from urllib2 import Request, urlopen, URLError
from codecs import iterdecode
import unohelper
from com.smf.ticker.getinfo import XSmf
# Add current directory to path to import yahoo, morningstar and advfn modules
cmd_folder = os.path.realpath(os.path.abspath
                              (os.path.split(inspect.getfile
                                             ( inspect.currentframe() ))[0]))
if cmd_folder not in sys.path:
    sys.path.insert(0, cmd_folder)

import yahoo
import morningstar
import advfn
import yahoo_hist
import html_hist_quote

class SmfImpl(unohelper.Base, XSmf ):
    """Define the main class for the SMF extension """    
    def __init__( self, ctx ):
        self.ctx = ctx
        self.nyse_list = []
        self.nasdaq_list = []
        self.amex_list = []
        self.exchange_flag = ['0', '0', '0']
        self.yahoo_flag = ['0', '']
        self.keyratio_flag = ['0', '']
        self.financial_flag = ['0', '']
        self.qfinancial_flag = ['0', '']
        #Setup for url calls to ADVFN in 5 chunks, most recent year first.
        self.advfn_start_list = [21, 16, 11, 6, 1]
        #start_list idx, year_count, total_year_count, ticker, Error, have data.
        self.advfn_flag = [0, 0, 0, '', None, False]
        self.advfn_data = []
        self.old_advfn_data = []
        self.total_advfn_data = []
        self.yahoo_hist_cache = {}
    #Following functions are called and mapped by LO through the Xsmf.rdb file.
    def getIntrinioQuote( self, ticker, tgtdate ):
        try:
            x = html_hist_quote.intrinio_fetch_data(self, ticker, tgtdate)
        except Exception as ex:
            x = str(ex)
        return x
    def getHistoricalQuote( self, ticker, tgtdate ):
        try:
            x = html_hist_quote.fetch_data(self, ticker, tgtdate)
        except Exception as ex:
            x = str(ex)
        return x
    def getYahooHist( self, ticker, tgtdate, datacode ):
        try:
            x = yahoo_hist.fetch_data(self, ticker, tgtdate, datacode)
        except Exception as ex:
            x = str(ex)
        return x

    def getYahoo( self, ticker, datacode ):
        # Retrieve the requested data
        try:
            s = yahoo.fetch_data(self, ticker, datacode)
        except Exception as ex:
            # x = yahoo.fetch_data(self, ticker, datacode)
            return str(ex)
        # If the data was retrieved, if possible, convert it to float
        try:
            x = float(s)
        except:
            x = s
        return x

    def getMorningKey( self, ticker, datacode):
        try:
            s = morningstar.fetch_keyratios(self, ticker, datacode)
        except Exception as ex:
            return str(ex)
        try:
            x = float(s)
        except:
            x = s
        return x
    
    def getMorningFin( self, ticker, datacode):
        fin_type = ''
        try:
            s = morningstar.fetch_financials(self, fin_type, ticker, datacode)
        except Exception as ex:
            return str(ex)
        try:
            x = float(s)
        except:
            x = s
        return x
    
    def getMorningQFin( self, ticker, datacode):
        fin_type = 'qtr'
        try:
            s = morningstar.fetch_financials(self, fin_type,  ticker, datacode)
        except Exception as ex:
            return str(ex)
        try:
            x = float(s)
        except:
            x = s
        return x


    def getADVFN(self, ticker, datacode):
        """Return ADVFN data. Mapped to PyUNO through the Xsmf.rdb file"""
        try:
            x = float(advfn.fetch_advfn(self, ticker, datacode))
        except:
            x = advfn.fetch_advfn(self, ticker, datacode)
        return x

def find_exchange(self, ticker):
    """Determine exchange ticker is traded on for querying data providers"""
    exch_name = ['nasdaq','nyse','amex']
    #Get exchange lists we don't have already, and return ticker's exchange.
    for exch in exch_name:
        if exch == 'nasdaq':
            if self.exchange_flag[0] == '0':
                    query_nasdaq(self, exch)
                    self.exchange_flag[0] = '1'
            for i in self.nasdaq_list:
                if ticker == i[0]:
                    return 'XNAS'
        if exch == 'nyse':
            if self.exchange_flag[1] == '0':
                    query_nasdaq(self, exch)
                    self.exchange_flag[1] = '1'
            for i in self.nyse_list:
                if ticker == i[0]:
                    return 'XNYS'
        if exch == 'amex':
            if self.exchange_flag[2] == '0':
                    query_nasdaq(self, exch)
                    self.exchange_flag[2] = '1'
            for i in self.amex_list:
                if ticker == i[0]:
                    return 'XASE'
    return 'Exchange lookup failed. Only NYSE, NASDAQ, and AMEX are supported.'

def query_nasdaq(self, exch_name):
    """Query Nasdaq for list of tickers by exchange"""
    header = {'user-agent': 'Mozilla/5.0 '\
              '(Macintosh; Intel Mac OS X 10.9; rv:32.0)'\
              ' Gecko/20100101 Firefox/32.0',}
    url = 'http://www.nasdaq.com/screening/companies-by-name.aspx?letter=0'\
          '&exchange=%s&render=download' % (exch_name)
    req = Request(url, headers = header)
    try:
        response = urlopen(req)
    #Catch errors.
    except URLError as e:
        self.exchange_flag[0] = '1'
        if hasattr(e, 'reason'):
            return e.reason
        elif hasattr(e,'code'):
            return 'Error', e.code
    #Setup list(s) of exchange names.
    exch_result = csv.reader(iterdecode(response,'utf-8'))
    if exch_name == 'nasdaq':
        self.nasdaq_list = [row for row in exch_result]
    elif exch_name == 'nyse':
        self.nyse_list = [row for row in exch_result]
    elif exch_name == 'amex':
        self.amex_list = [row for row in exch_result]
    return 'Unknown Exception in query_nasdaq'


def createInstance( ctx ):
    return SmfImpl( ctx )

g_ImplementationHelper = unohelper.ImplementationHelper()
g_ImplementationHelper.addImplementation( \
    createInstance,"com.smf.ticker.getinfo.python.SmfImpl",
        ("com.sun.star.sheet.AddIn",),)
