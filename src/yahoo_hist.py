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
    if ticker in self.yahoo_hist_cache and eff_date in self.yahoo_hist_cache[ticker]:
        cv = self.yahoo_hist_cache[ticker][eff_date][c_datacode]
        try:
            v = float(cv)
        except:
            v = str(cv)
        return  v

    # There was no cache it, so we must go to Yahoo to get the historical data
    # Build up url for query
    urlbase = 'https://query.yahooapis.com/v1/public/yql?'
    urlquery ='q=select * from yahoo.finance.historicaldata where symbol in ("{symbol}") and startDate = "{startdate}" and endDate = "{enddate}"&format=json&env=store://datatables.org/alltableswithkeys&callback='

    # The symbol string is everything between the quotes in "{symbol}"
    urlquery1 = urlquery.replace("{symbol}", ticker).replace("{startdate}", eff_date).replace("{enddate}", eff_date)
    url = urlbase + urllib.parse.quote(urlquery1, safe='/=&:')

    try:
        req = urllib.request.Request(url)
        response = urllib.request.urlopen(req)
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
            self.yahoo_hist_cache[ticker] = {}
            self.yahoo_hist_cache[ticker][tgtdate] = q
            try:
                v = float(q[c_datacode])
            except:
                v = str(q[c_datacode])
            lst.append(v)
        return lst
    else:
        # quote is:, type(j["query"]["results"]["quote"])
        q = qr
        self.yahoo_hist_cache[ticker] = {}
        self.yahoo_hist_cache[ticker][tgtdate] = q
        try:
            v = float(q[c_datacode])
        except:
            v = str(q[c_datacode])
        return  v

    return "yahoo_hist unexpected error"
