#  yahoo_hist.py - Retrieve historical data from Yahoo Finance for the SMF Extension.
#
#  Copyright 2015 by Dave Hocker (AtHomeX10@gmail.com)
#
#  license: GNU LGPL
#
#  This library is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 3 of the License, or (at your option) any later version.
#

# Python 3

import ssl
import urllib.request
import urllib.parse
import json


def fetch_data(self, ticker, tgtdate, datacode):
    """
    Retrieve historical stock data from Yahoo Financial web api
    :param ticker: string - stock ticker symbol (e.g XOM)
    :param tgtdate: string or float (libreoffice date) - for date of interest
    :param datacode: string - name of data to be retrieved (Symbol, Date, Open, High, Low, Close, Volume, Adj_Close)
    :return: For numeric values returns a float. Otherwise, returns a string.
    """

    # Resolve date
    # This was an attempt to support LO date types. However,
    # I could not figure out how dates worked and I could find no examples to shed light on the subject.
    if type(tgtdate) == float:
        # LibreOffice date as a float
        # base_date = datetime.date(1900, 1, 1)
        # delta_date = datetime.timedelta(int(tgtdate))
        # act_date = base_date + delta_date
        # eff_date = act_date.strftime("%Y-%m-%d")
        return "Date format not supported"
    else:
        # Assumed to be a string in ISO format.
        # The IDL actually forces this to be a string.
        eff_date = tgtdate

    # Coerce datacode to Xxxxxx...We know that but the user may not get it right
    if datacode.lower() == "adj_close":
        c_datacode = "Adj_Close"
    else:
        c_datacode = datacode.capitalize()

    # Look for cache hit first...
    # Since historical data should be constant, only one web call is
    # needed for a ticker/date combination.
    cr = __lookup_symbol_by_date(ticker, eff_date)
    if cr:
        print ("Cache hit")
        cv = cr[c_datacode]
        try:
            v = float(cv)
        except:
            v = str(cv)
        return v

    # There was no cache it, so we must go to Yahoo to get the historical data
    # Build up url for query
    urlbase = 'https://query.yahooapis.com/v1/public/yql?'
    urlquery ='q=select * from yahoo.finance.historicaldata where symbol in ("{symbol}") and startDate = "{startdate}" and endDate = "{enddate}"&format=json&env=store://datatables.org/alltableswithkeys&callback='

    # The symbol string is everything between the quotes in "{symbol}"
    urlquery1 = urlquery.replace("{symbol}", ticker).replace("{startdate}", eff_date).replace("{enddate}", eff_date)
    url = urlbase + urllib.parse.quote(urlquery1, safe='/=&:')

    try:
        # At some point between LO version 5.0.0.5 and 5.2.4, changes to the embedded python were made
        # and the urlopen() method no longer worked. Supplying a context seemed to fix the problem.
        req = urllib.request.Request(url)
        response = urllib.request.urlopen(req, context=ssl.create_default_context(ssl.Purpose.CLIENT_AUTH))
    except Exception as ex:
        return str(ex)

    # The response is a byte string which we convert to a character string
    bytes = response.read()
    rs = bytes.decode("utf-8")
    # The response is json formatted
    j = json.loads(rs)

    # NOTE: If multiple symbols are specified in the "in" clause,
    # the quote property will be an array of dicts instead of a single
    # dict.
    qr = j["query"]["results"]["quote"]
    if type(qr) == list:
        # quote is a list
        lst = []
        for q in qr:
            __insert_symbol(q["symbol"], eff_date, q["open"], q["high"], q["low"], q["close"], q["volume"], q["adj_close"])
            try:
                v = float(q[c_datacode])
            except:
                v = str(q[c_datacode])
            lst.append(v)
        return lst
    else:
        # quote is:, type(j["query"]["results"]["quote"])
        q = qr
        print ("Cache insert")
        __insert_symbol(ticker, eff_date, q["Open"], q["High"], q["Low"], q["Close"], q["Volume"], q["Adj_Close"])
        try:
            v = float(q[c_datacode])
        except:
            v = str(q[c_datacode])
        return  v

    return "yahoo_hist unexpected error"


import sqlite3
import os

def __open_yh_cache():
    """
    Open a connection to the cache DB. Create the DB if it does not exist.
    :return: Database connection.
    """
    # Determine cache location based on underlying OS
    file_name = "smf_yh_cache.sqlite3"
    if os.name == "posix":
        # Linux or OS X
        file_path = "{0}/libreoffice/smf/".format(os.environ["HOME"])
    elif os.name == "nt":
        # windows
        file_path = "{0}\\libreoffice\\smf\\".format(os.environ["LOCALAPPDATA"])

    # Make the folder
    if not os.path.exists(file_path):
        print ("Create directory")
        os.makedirs(file_path)

    full_file_path = file_path + file_name

    # If DB does not exist, create it
    if not os.path.exists(full_file_path):
        print ("Create database")
        conn = sqlite3.connect(full_file_path)
        conn.execute("CREATE TABLE SymbolDate (Symbol text not null, Date text not null, Open real, High real, Low real, Close real, Volume integer, Adj_Close real, PRIMARY KEY(Symbol,Date))")
    else:
        conn = sqlite3.connect(full_file_path)

    # We use the row factory to get named row columns. Makes handling row sets easier.
    conn.row_factory = sqlite3.Row
    # The default string type is unicode. This changes it to UTF-8.
    conn.text_factory = str

    # return connection to the cache DB
    return conn


def __lookup_symbol_by_date(symbol, tgtdate):
    """
    Look up cached historical data for a given symbol/date pair.
    :param symbol:
    :param tgtdate:
    :return: Returns the cached DB record. If no record is found, returns None.
    """
    conn = __open_yh_cache()
    rset = conn.execute("SELECT * from SymbolDate where Symbol=? and Date=?", [symbol, tgtdate])
    r = rset.fetchone()
    conn.close()
    # r will be None if no record was found
    return r


def __insert_symbol(symbol, tgtdate, open, high, low, close, volume, adj_close):
    """
    Insert a new cache record in the cache DB.
    :param symbol:
    :param tgtdate:
    :param open:
    :param high:
    :param low:
    :param close:
    :param volume:
    :param adj_close:
    :return:
    """
    conn = __open_yh_cache()
    print ("Cache data:", symbol, tgtdate, open, high, low, close, volume, adj_close)
    conn.execute("INSERT INTO SymbolDate values (?,?,?,?,?,?,?,?)", [symbol, tgtdate, open, high, low, close, volume, adj_close])
    conn.commit()
    conn.close()
