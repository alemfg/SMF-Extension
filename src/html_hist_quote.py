#  html_hist_quote.py - Retrieve historical data from Yahoo Finance for the SMF Extension.
#
#  Copyright 2017 by Dave Hocker as TheAgency (AtHomeX10@gmail.com)
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
#  7/1/2017
#  Added support for the Intrinio financial data service (https://intrinio.com)
#  This support provides a closing quote for a stock on a given day.
#
#############################################
#
#  Research for possible stock data sources
#
#  http://www.programmableweb.com/news/96-stocks-apis-bloomberg-nasdaq-and-etrade/2013/05/22
#
#  http://www.eoddata.com/products/default.aspx
#
#############################################
#
#  http://www.google.com/finance/historical?q=ticker
#  Implemented
#
##############################
#
#  https://intrinio.com
#  Implemented
#  Requires sign up. Currently, historical price quotes are free with a limit of 500 calls per day.
#
##############################

import urllib.request
import urllib.parse
import urllib.error
from html.parser import HTMLParser
import ssl
import datetime
import json
import os
import os.path
import app_logger
import sys
import threading

# Logger init
app_logger.EnableLogging()
logger = app_logger.getAppLogger()
# logger.debug("Python system path: %s", sys.path)

# Configuration lock
dialog_lock = threading.Lock()

class QConfiguration:
    """
    Encapsulates Intrinio configuration including credentials.
    """
    auth_user = ""
    auth_passwd = ""
    cacerts = ""
    # Base URL for Intrinio services
    base_url = "https://api.intrinio.com"
    macOS = False
    # Full path to the intrinio.conf file
    full_file_path = ""

    @classmethod
    def load(cls):
        """
        Load credentials from configuration file. The location of the intrinio.conf
        file is OS dependent. The permissions of the intrinio.conf file should allow
        access ONLY by the user.
        :return:
        """
        global logger
        file_name = "intrinio.conf"
        file_path = ""
        if os.name == "posix":
            # Linux or OS X
            file_path = "{0}/libreoffice/intrinio/".format(os.environ["HOME"])
            if os.uname()[0] == "Darwin":
                QConfiguration.macOS = True
        elif os.name == "nt":
            # Windows
            file_path = "{0}\\libreoffice\\intrinio\\".format(os.environ["LOCALAPPDATA"])
        QConfiguration.full_file_path = file_path + file_name

        # Read credentials
        try:
            cf = open(QConfiguration.full_file_path, "r")
            cfj = json.loads(cf.read())
            cls.auth_user = cfj["user"]
            cls.auth_passwd = cfj["password"]
            # certifi is required for macOS
            if QConfiguration.macOS:
                if "certifi" in cfj:
                    cls.cacerts = cfj["certifi"]
                    if not os.path.exists(cls.cacerts):
                        logger.error("certifi path does not exist: %s", cls.cacerts)
                        cls.cacerts = ""
                else:
                    logger.error("intrinio.conf does not contain a definition for certifi")
            cf.close()
            logger.debug("intrinio.conf loaded")
        except FileNotFoundError as ex:
            logger.debug("%s was not found", QConfiguration.full_file_path)
        except Exception as ex:
            logger.debug("An exception occurred while attempting to load intrinio.conf")
            logger.debug(str(ex))

    @classmethod
    def save(cls, username, password):
        """
        Save configuraton back to intrinio.conf
        :return:
        """
        QConfiguration.auth_user = username
        QConfiguration.auth_passwd = password

        conf = {}
        conf["user"] = QConfiguration.auth_user
        conf["password"] = QConfiguration.auth_passwd
        conf["certifi"] = QConfiguration.cacerts

        cf = open(QConfiguration.full_file_path, "w")
        json.dump(conf, cf, indent=4)
        cf.close()

        if os.name == "posix":
            import stat
            # The user gets R/W permissions
            os.chmod(QConfiguration.full_file_path, stat.S_IRUSR | stat.S_IWUSR)
        else:
            pass

    @classmethod
    def is_configured(cls):
        """
        Intrinio is configured if there is a user and password in the intrinio.conf file.
        :return:
        """
        if QConfiguration.macOS:
            return QConfiguration.auth_user and QConfiguration.auth_passwd and QConfiguration.cacerts
        return QConfiguration.auth_user and QConfiguration.auth_passwd

# Initialize Intrinio configuration
QConfiguration.load()


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

class IntrinioBase:

    @staticmethod
    def setup_authorization(url_string):
        passman = urllib.request.HTTPPasswordMgrWithDefaultRealm()
        passman.add_password(None, url_string, QConfiguration.auth_user, QConfiguration.auth_passwd)
        authhandler = urllib.request.HTTPBasicAuthHandler(passman)

        if QConfiguration.macOS:
            # The LO version of python does not have any cacerts. certifi as an alternate.
            # This works on macOS 10.12.5 Sierra. Why is unclear. It literally took days to
            # find this as a working solution.
            # See: https://github.com/certifi/python-certifi and https://pypi.python.org/pypi/certifi
            if not QConfiguration.cacerts:
                logger("Intrinio call will fail because intrinio.conf certfi key is invalid or missing")
            ssl_ctx = ssl.create_default_context(cafile=QConfiguration.cacerts)
            httpshandler = urllib.request.HTTPSHandler(context=ssl_ctx)
            opener = urllib.request.build_opener(httpshandler, authhandler)
        else:
            opener = urllib.request.build_opener(authhandler)

        urllib.request.install_opener(opener)


    @staticmethod
    def exec_request(url_string):
        """

        :param url_string:
        :return:
        """
        global logger
        print(url_string)
        Quote.setup_authorization(url_string)
        try:
            logger.debug("Calling Intrinio API: %s", url_string)
            res = urllib.request.urlopen(url_string).read()
            res = str(res, "utf-8")
        except urllib.error.HTTPError as ex:
            logger.debug("Exception attempting to call Intrinio API")
            logger.debug(ex.msg)
            raise ex

        return json.loads(res)

class Quote(IntrinioBase):
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
            logger.debug("Calling Google Finance: %s", url_string)
            html_lines = urllib.request.urlopen(url_string).readlines()
            html_str = ""
            for line in html_lines:
                html_str += str(line, "utf-8")
        except urllib.error.HTTPError as ex:
            logger.debug("Exception attempting to call Google Finance")
            logger.debug(ex.msg)
            return None

        # Run parser over page source, extracting data of interest
        parser = HistQuoteHTMLParser()
        parser.feed(html_str)

        print (parser.quote_data)

        return Quote(ticker, start_date, float(parser.quote_data["close"].replace(",", "")))

    @staticmethod
    def get_intrinio_quote(ticker, start_date):
        """

        :param ticker:
        :param instrument_type:
        :param start_date:
        :return:
        """

        template_url = "{0}/historical_data?identifier={1}&item=close_price&start_date={2}&end_date={3}"
        url_string = template_url.format(QConfiguration.base_url, ticker, start_date, start_date)
        res = Quote.exec_request(url_string)
        # Extract closing price from json result
        return Quote(ticker, start_date, float(res["data"][0]["value"]))


def fetch_data(self, ticker, tgtdate):
    """
    Retrieve historical stock quote from Google web page
    :param ticker: string - stock ticker symbol (e.g XOM)
    :param tgtdate: string or float (libreoffice date) - for date of interest
    :return: For numeric values returns a float. Otherwise, returns a string.
    """

    # Resolve date. It can be a LibreCalc date as a float or a string date
    if type(tgtdate) == float:
        eff_date = __float_to_date_str(tgtdate)
    elif type(tgtdate) == str:
        # Assumed to be a string in ISO format.
        eff_date = tgtdate
    else:
        logger.debug("Unsuported date format type: {0} value: {1}".format(type(tgtdate), tgtdate))
        return "Unsuported date format type: {0} value: {1}".format(type(tgtdate), tgtdate)

    # return "type: {0} value: {1}".format(type(tgtdate), eff_date)

    # Look for cache hit first...
    # Since historical data should be constant, only one web call is
    # needed for a ticker/date combination.
    cr = __lookup_symbol_by_date(ticker, eff_date)
    if cr:
        logger.debug("Google Finance cache hit for %s %s", ticker, eff_date)
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


def intrinio_fetch_data(self, ticker, tgtdate):
    """
    Retrieve historical stock quote from Google web page
    :param ticker: string - stock ticker symbol (e.g XOM)
    :param tgtdate: string or float (libreoffice date) - for date of interest
    :return: For numeric values returns a float. Otherwise, returns a string.
    """
    global dialog_lock
    global logger

    # Force Intrinio configuration. Even if the configuration attempt
    # fails, we'll continue on because the request might hit cache.
    # Only if we need to call Intrinio will we fail the request.
    if not QConfiguration.is_configured():
        try:
            if dialog_lock.acquire(blocking=False):
                logger.debug("Calling intrinio_login()")
                res = intrinio_login()
                if res:
                    QConfiguration.save(res[0], res[1])
                else:
                    logger.error("intrinio_login() returned false")
                dialog_lock.release()
            else:
                logger.warn("Intrinio configuration dialog is already active")
        except Exception as ex:
            logger.error("intrinio_login() failed %s", str(ex))

    # Resolve date. It can be a LibreCalc date as a float or a string date
    if type(tgtdate) == float:
        eff_date = __float_to_date_str(tgtdate)
    elif type(tgtdate) == str:
        # Assumed to be a string in ISO format.
        eff_date = tgtdate
    else:
        logger.debug("Unsuported date format type: {0} value: {1}".format(type(tgtdate), tgtdate))
        return "Unsuported date format type: {0} value: {1}".format(type(tgtdate), tgtdate)

    # Look for cache hit first...
    # Since historical data should be constant, only one web call is
    # needed for a ticker/date combination.
    cr = __lookup_symbol_by_date(ticker, eff_date)
    if cr:
        logger.debug("Intrinio cache hit for %s %s", ticker, eff_date)
        cv = cr["Close"]
        try:
            v = float(cv)
        except:
            v = str(cv)
        return v

    # We need intrinio.conf to use Intrinio
    if not QConfiguration.is_configured():
        return "intrinio.conf is missing, incomplete or in error"

    # Use Intrinio to get historical data
    q = Quote.get_intrinio_quote(ticker, eff_date)

    # Cache the quote
    __insert_symbol(ticker, eff_date, q.close)

    return float(q.close)


def __float_to_date_str(float_date):
    """
    Magic algorithm to convert float date
    LibreOffice date as a float (actually the format used by Excel)
    base_date = 1899-12-30 = the float value 0.0
    see this reference: http://www.cpearson.com/excel/datetime.htm
    :param float_date: ddddd.tttttt where d is days from 1899-12-30 and .tttttt is fraction of 24 hours
    :return:
    """
    seconds = (int(float_date) - 25569) * 86400
    d = datetime.datetime.utcfromtimestamp(seconds)
    eff_date = d.strftime("%Y-%m-%d")
    return eff_date


#
# This code was imported from the original yahoo_hist.py file. It implements a caching
# systems using sqlite3 as the backing store.
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

#
# Intrinio login dialog
# Adapted from https://forum.openoffice.org/en/forum/viewtopic.php?f=45&t=56397#p248794
#

try:
    import uno
    logger.debug("Attempt to import uno succeeded")
    # logger.debug("sys.path = %s", sys.path)
except Exception as ex:
    logger.error("Attempt to import uno failed %s", str(ex))
try:
    # https://www.openoffice.org/api/docs/common/ref/com/sun/star/awt/PosSize.html
    from com.sun.star.awt.PosSize import POSSIZE # flags the x- and y-coordinate, width and height
    logger.debug("Attempt to import com.sun.star.awt.PosSize succeeded")
except Exception as ex:
    logger.error("Attempt to import com.sun.star.awt.PosSize failed %s", str(ex))


def add_awt_model(dlg_model, srv, ctl_name, prop_list):
    '''
    Helper function for building dialog
    Insert UnoControl<srv>Model into given DialogControlModel oDM by given sName and properties dProps
    '''
    ctl_model = dlg_model.createInstance("com.sun.star.awt.UnoControl" + srv + "Model")
    while prop_list:
        prp = prop_list.popitem()
        uno.invoke(ctl_model,"setPropertyValue",(prp[0],prp[1]))
        #works with awt.UnoControlDialogElement only:
        ctl_model.Name = ctl_name
    dlg_model.insertByName(ctl_name, ctl_model)


def intrinio_login():
    """
    Ask user for Intrinio login credentials
    :return: If successful, returns username and password as a tuple (something truthy)
    If canceled, returns False.
    """
    # Reference: https://www.openoffice.org/api/docs/common/ref/com/sun/star/awt/module-ix.html
    global logger

    ctx = uno.getComponentContext()
    smgr = ctx.ServiceManager
    dlg_model = smgr.createInstance("com.sun.star.awt.UnoControlDialogModel")
    dlg_model.Title = 'Intrinio Access Keys'
    add_awt_model(dlg_model, 'FixedText', 'lblName', {
        'Label': 'User Name',
    }
                  )
    add_awt_model(dlg_model, 'Edit', 'txtName', {})
    add_awt_model(dlg_model, 'FixedText', 'lblPWD', {
        'Label': 'Password',
    }
                  )
    add_awt_model(dlg_model, 'Edit', 'txtPWD', {
        'EchoChar': 42,
    }
                  )
    add_awt_model(dlg_model, 'Button', 'btnOK', {
        'Label': 'Save',
        'DefaultButton': True,
        'PushButtonType': 1,
    }
                  )
    add_awt_model(dlg_model, 'Button', 'btnCancel', {
        'Label': 'Cancel',
        'PushButtonType': 2,
    }
                  )

    lmargin = 10  # left margin
    rmargin = 10  # right margin
    tmargin = 10  # top margin
    bmargin = 10  # bottom margin
    cheight = 25  # control height
    pad = 5  # top/bottom padding where needed
    theight = cheight + pad  # total height of a control

    # Poor man's grid
    # layout "control-name", [x, y, w, h]
    layout = {
        "lblName": [lmargin, tmargin, 100, cheight],
        "txtName": [lmargin + 100, tmargin, 250, cheight],
        "lblPWD": [lmargin, tmargin + (theight * 1), 100, cheight],
        "txtPWD": [lmargin + 100, tmargin + (theight * 1), 250, cheight],
        "btnOK": [lmargin + 100, tmargin + (theight * 2), 100, cheight],
        "btnCancel": [lmargin + 200, tmargin + (theight * 2), 100, cheight]
    }

    dialog = smgr.createInstance("com.sun.star.awt.UnoControlDialog")
    dialog.setModel(dlg_model)
    name_ctl = dialog.getControl('txtName')
    pass_ctl = dialog.getControl('txtPWD')

    # Apply layout to controls. Must be done within the dialog.
    for name, d in layout.items():
        ctl = dialog.getControl(name)
        ctl.setPosSize(d[0], d[1], d[2], d[3], POSSIZE)

    dialog.setPosSize(300, 300, lmargin + rmargin + 100 + 250, tmargin + bmargin + (theight * 3), POSSIZE)
    dialog.setVisible(True)

    # Run the dialog. Returns the value of the PushButtonType.
    x = dialog.execute()
    logger.debug("intrinio login dialog returned: %s", x)
    if x == 1:
        return (name_ctl.getText(), pass_ctl.getText())
    else:
        return False


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

"""
Test code
"""
# if __name__ == "__main__":
#     q = Quote.get_quote("usibx", "2017-05-31")
#     print (q.close)
#     q = Quote.get_quote("vym", "2017-05-31")
#     print (q.close)
#     q = Quote.get_quote("INDEXDJX:.DJI", "2017-05-31")
#     print (q.close)
#     q = Quote.get_quote("INDEXSP:.INX", "2017-05-31")
#     print (q.close)
#     q = Quote.get_quote("INDEXNASDAQ:.IXIC", "2017-05-31")
#     print (q.close)
