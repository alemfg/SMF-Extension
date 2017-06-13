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
import unohelper
from com.smf.ticker.getinfo import XSmf
# Add current directory to path to import yahoo and morningstar modules
cmd_folder = os.path.realpath(os.path.abspath
                              (os.path.split(inspect.getfile
                                             ( inspect.currentframe() ))[0]))
if cmd_folder not in sys.path:
    sys.path.insert(0, cmd_folder)

sites_folder = "/usr/local/lib/python3.6/site-packages"
# if sites_folder not in sys.path:
#     sys.path.insert(0, sites_folder)

import yahoo
import morningstar
#import advfn
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
        self.advfn_flag = ['0', '']
        self.yahoo_hist_cache = {}
    #Following functions are called and mapped by LO through the Xsmf.rdb file.
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
            x = float(morningstar.fetch_keyratios(self, ticker, datacode))
        except:
            x = morningstar.fetch_keyratios(self, ticker, datacode)
        return x
    
    def getMorningFin( self, ticker, datacode):
        fin_type = ''
        try:
            x = float(morningstar.fetch_financials(self, fin_type, ticker, datacode))
        except:
            x = morningstar.fetch_financials(self, fin_type, ticker, datacode)
        return x
    
    def getMorningQFin( self, ticker, datacode):
        fin_type = 'qtr'
        try:
            x = float(morningstar.fetch_financials(self, fin_type,  ticker, datacode))
        except:
            x = morningstar.fetch_financials(self, fin_type, ticker, datacode)
        return x
    
#getADVFN is a placeholder - not yet implemented
#    def getADVFN( self, ticker, datacode):
#        try:
#            x = float(advfn.fetch_advfn(self, ticker, datacode))
#        except:
#            x = advfn.fetch_advfn(self, ticker, datacode)
#        return x
    
def createInstance( ctx ):
    return SmfImpl( ctx )

g_ImplementationHelper = unohelper.ImplementationHelper()
g_ImplementationHelper.addImplementation( \
    createInstance,"com.smf.ticker.getinfo.python.SmfImpl",
        ("com.sun.star.sheet.AddIn",),)
