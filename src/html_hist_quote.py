#  html_hist_quote.py - Retrieve historical data from Yahoo Finance for the SMF Extension.
#
#  Copyright 2017 by Dave Hocker (AtHomeX10@gmail.com)
#
#  license: GNU LGPL
#
#  This library is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 3 of the License, or (at your option) any later version.
#
#  NOTE
#  On or about 5/15/2017 Yahoo discontinued the service that was originally used
#  to obtain historical quotes. After some research, it was decided to use
#  a Google service at https://www.google.com/finance/historical?q=usibx...
#  This URL produces a web page which is scraped for stock quote data. There is
#  no guarantee that the page contents will not change over time. It may
#  break periodically and changes to the scraping code (parsing of the
#  web page HTML) may be required.
#

import urllib.request
import urllib.parse
import urllib.error
import datetime
from html.parser import HTMLParser


class HistQuoteHTMLParser(HTMLParser):
    """
    Customized parser class for web page scraping historical stock quotes.
    See the reference information at the bottom of this file to see
    how the HTML from the Google service looks.
    """
    def __init__(self):
        HTMLParser.__init__(self)
        # Parser state controls
        self.table_on = False
        self.th_on = False
        self.td_on = False
        self.hdrs = []
        self.col = 0
        self.quote_data = {}

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            if attrs[0][0] == "class" and attrs[0][1] == "gf-table historical_price":
                # print ("Target table start tag:", tag, attrs[0])
                self.table_on = True
        elif tag == "th" and self.table_on:
            # print("Target table th tag:", tag, attrs[0])
            self.th_on = True
        elif tag == "td" and self.table_on:
            # print("Target table td tag:", tag, attrs)
            self.td_on = True

    def handle_endtag(self, tag):
        if tag == "table" and self.table_on:
            # print("Encountered target table end tag :", tag)
            self.table_on = False

    def handle_data(self, data):
        if self.th_on:
            # All column names are saved in lower case
            self.hdrs.append(data.rstrip().lower())
            self.th_on = False
        elif self.td_on:
            # Be sure to remove extraneous white space
            self.quote_data[self.hdrs[self.col]] = data.rstrip()
            self.col += 1
            self.td_on = False

class Quote:
    """
    A historical quote for a given ticker symbol
    """
    def __init__(self, ticker, for_date, close):
        self.close = close
        self.for_date = for_date
        self.ticker = ticker

    @staticmethod
    def get_quote(ticker, start_date):
        url_string = "http://www.google.com/finance/historical?q={0}".format(ticker)
        url_string += "&startdate={0}&enddate={0}&output=html".format(
                          start_date)
        # print (url_string)

        # Get the web page source
        try:
            html_lines = urllib.request.urlopen(url_string).readlines()
            html_str = ""
            for line in html_lines:
                html_str += str(line, "utf-8")
        except urllib.error.HTTPError as ex:
            print (ex.msg)
            return None

        # Run parser over page source, extracting data of interest
        parser = HistQuoteHTMLParser()
        parser.feed(html_str)

        print (parser.quote_data)

        return Quote(ticker, start_date, float(parser.quote_data["close"].replace(",", "")))


def fetch_data(self, ticker, tgtdate):
    """
    Retrieve historical stock quote from Google web page
    :param ticker: string - stock ticker symbol (e.g XOM)
    :param tgtdate: string or float (libreoffice date) - for date of interest
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

    # Look for cache hit first...
    # Since historical data should be constant, only one web call is
    # needed for a ticker/date combination.
    cr = __lookup_symbol_by_date(ticker, eff_date)
    if cr:
        print ("Cache hit")
        cv = cr["Close"]
        try:
            v = float(cv)
        except:
            v = str(cv)
        return v

    # Use Google to get historical data
    q = Quote.get_quote(ticker, eff_date)

    # Cache the quote
    __insert_symbol(ticker, eff_date, q.close)

    return float(q.close)

#
# This code was imported from the original yahoo_hist.py file
#

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


def __insert_symbol(symbol, tgtdate, close):
    """
    Insert a new cache record in the cache DB. The Google service does not
    produce all data values for every symbol (e.g. mutual funds only have closing prices).
    to preserve backward compatiblity in the cache DB zero values are used for unavailable values.
    :param symbol:
    :param tgtdate:
    :param close:
    :return:
    """
    conn = __open_yh_cache()
    print ("Cache data:", symbol, tgtdate, close)
    conn.execute("INSERT INTO SymbolDate values (?,?,?,?,?,?,?,?)", [symbol, tgtdate, 0, 0, 0, close, 0, 0])
    conn.commit()
    conn.close()

"""
Test code
"""
if __name__ == "__main__":
    q = Quote.get_quote("usibx", "2017-05-31")
    print (q.close)
    q = Quote.get_quote("vym", "2017-05-31")
    print (q.close)
    q = Quote.get_quote("INDEXDJX:.DJI", "2017-05-31")
    print (q.close)
    q = Quote.get_quote("INDEXSP:.INX", "2017-05-31")
    print (q.close)
    q = Quote.get_quote("INDEXNASDAQ:.IXIC", "2017-05-31")
    print (q.close)


"""
Examples of HTML for different ticker symbols

USIBX
view-source:https://www.google.com/finance/historical?q=usibx&startdate=2017-05-31&enddate=2017-05-31&output=text
<table class="gf-table historical_price">
<tr class=bb>
<th class="bb lm lft">Date
<th class="rgt bb rm">Close
<tr>
<td class="lm">May 31, 2017
<td class="rgt rm">10.68
</table>

//*[@id="prices"]/table/tbody/tr[1]
//*[@id="prices"]/table/tbody/tr[1]/th[1]
//*[@id="prices"]/table/tbody/tr[2]
//*[@id="prices"]/table/tbody/tr[2]/td[1]

.IXIC (NASDAQ)
view-source:https://www.google.com/finance/historical?q=.ixic&startdate=2017-05-31&enddate=2017-05-31&output=text
<table class="gf-table historical_price">
<tr class=bb>
<th class="bb lm lft">Date
<th class="rgt bb">Open
<th class="rgt bb">High
<th class="rgt bb">Low
<th class="rgt bb">Close
<th class="rgt bb rm">Volume
<tr>
<td class="lm">May 31, 2017
<td class="rgt">6,221.63
<td class="rgt">6,221.99
<td class="rgt">6,164.07
<td class="rgt">6,198.52
<td class="rgt rm">-
</table>
"""