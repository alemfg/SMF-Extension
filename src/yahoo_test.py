#  yahoo.py - Retrieve data from Yahoo Finance for the SMF Extension.
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
#  Inspired by ystockquote by Corey Goldberg (cgoldberg@gmail.com)
#
import csv
import sys
import datetime

try:
    import urllib.request
    from urllib.error import URLError
except ImportError:
    from urllib2 import Request, urlopen, URLError
from codecs import iterdecode


class SmfImpl:
    """Define the main class for the SMF extension """
    def __init__( self ):
        self.yahoo_flag = ['0', '']


def fetch_data(self, ticker, datacode):
    """Get Yahoo data and return desired element to user"""
    # Check for sane user input for datacode.
    if datacode < 1 or datacode > 53:
        return 'Invalid Datacode'
    # Setup list of Yahoo-defined elements to query with.
    query_list = ['y', 'd', 'r1', 'q', 'p', 'o', 'c1', 'd1', 'c', 't1', 'p2', 'm5', 'm6',
                  'g', 'm7', 'h', 'm8', 'm3', 'l', 'm4', 'l1', 't8', 'm', 'k', 'v', 'j',
                  'j1', 'j5', 'k4', 'j6', 'n', 'k5', 'w', 'x', 'v', 'a5', 'b6', 'k3', 'a2',
                  'e', 'e7', 'e8', 'e9', 's6', 'b4', 'j4', 'p5', 'p6', 'r', 'r5', 'r6',
                  'r7', 's7']
    stat = ''.join(query_list)
    # Check whether flags indicate we already have the data we need.
    if self.yahoo_flag[0] == '1' or self.yahoo_flag[1] != ticker:
        self.yahoo_reader = query_yahoo(self, ticker, stat)
        # Catch errors.
        if self.yahoo_flag[0] == '1':
            return self.yahoo_reader
        # Set flags upon successful query.
        else:
            self.yahoo_flag[0] = '0'
            self.yahoo_flag[1] = ticker
            # Store csv in memory.
            self.yahoo_data = [row for row in self.yahoo_reader]
            cleanup_yahoo(self)
            print(self.yahoo_data)
    return self.yahoo_data[0][int(datacode) - 1]


def cleanup_yahoo(self):
    """Cleanup as many elements as possible to standardized forms"""
    # Format dividend dates to ISO standard.
    self.yahoo_data[0][2] = str((datetime.datetime.strptime
                                 (self.yahoo_data[0][2], '%m/%d/%Y')).date())
    self.yahoo_data[0][3] = str((datetime.datetime.strptime
                                 (self.yahoo_data[0][3], '%m/%d/%Y')).date())
    # Format last trade date to ISO standard.
    self.yahoo_data[0][7] = str((datetime.datetime.strptime
                                 (self.yahoo_data[0][7], '%m/%d/%Y')).date())
    # Format last trade time to ISO standard.
    self.yahoo_data[0][9] = str((datetime.datetime.strptime
                                 (self.yahoo_data[0][9], '%I:%M%p')).time())
    # Strip % from chg in pct, moving avg's, and pct chg from 52wk high/low.
    for index_1 in (10, 12, 16, 29, 31):
        self.yahoo_data[0][index_1] = (self.yahoo_data[0][index_1]
                                       ).translate({ord(i): None for i in '%'})
    # Convert market cap, rev, EBITDA to floats.
    for index_2 in (26, 43, 45):
        big_val = self.yahoo_data[0][index_2]
        if 'B' in big_val:
            self.yahoo_data[0][index_2] = ((float(big_val.translate
                                                  ({ord(i): None for i in 'B'}
                                                   ))) * 1000000000)
        elif 'M' in big_val:
            self.yahoo_data[0][index_2] = ((float(big_val.translate
                                                  ({ord(i): None for i in 'M'}
                                                   ))) * 1000000)
    #print (self.yahoo_data)
    return


def query_yahoo(self, ticker, stat):
    """Query Yahoo for the data we want"""
    url = 'http://download.finance.yahoo.com/d/quotes.csv?s=%s&f=%s' % (ticker, stat)
    # req = Request(url)
    print (url)
    try:
        #response = urllib.request.urlopen(url)
        response_lines = urllib.request.urlopen(url).readlines()
        csv_lines = []
        for line in response_lines:
            one = str(line, "utf-8")
            # print (one)
            csv_lines.append(one)
    # Catch errors.
    except URLError as e:
        self.yahoo_flag[0] = '1'
        if hasattr(e, 'reason'):
            return e.reason
        elif hasattr(e, 'code'):
            return 'Error', e.code
    except Exception as ex:
        return str(ex)
    #print (csv_lines)
    # if sys.version_info.major == 3:
    #     return csv.reader(csv_lines)
    return csv.reader(csv_lines)


if __name__ == "__main__":
    self = SmfImpl()
    #x = query_yahoo(self, "AAPL", "l1")
    x = fetch_data(self, "AAPL", 21)
    print (x)

"""

[['1.69', '2.52', '2017-05-18', '2017-05-11', '148.98', '145.57', '-4.49', '2017-06-12', '-4.49 - -3.01%', '15:06:00', '-3.01', '10.36', '+7.72', '142.51', '-6.56', '146.09', '-4.35', '151.05', '3:06pm - <b>144.49</b>', '134.13', '144.49', '157.36', '142.51 - 146.09', '156.65', '7910588', '91.50', 753350000000.0, '52.99', '-12.16', '+57.91', 'Apple Inc.', '-7.76', '91.50 - 156.65', 'NMS', '7910588', '500', '200', '100', '25435600', '8.52', '8.94', '10.53', '1.89', 220460000000.0, '25.76', 69720000000.0, '3.52', '5.78', '16.95', '1.50', '16.16', '13.72', '2.33']]
"""