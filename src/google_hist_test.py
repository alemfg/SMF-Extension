import urllib.request
import urllib.parse
import urllib.error
import datetime
import json
from lxml import html

class Quote:
    def __init__(self, ticker, for_date, close):
        self.close = close
        self.for_date = for_date
        self.ticker = ticker

    @staticmethod
    def get_quote(ticker, start_date):
        url_string = "http://www.google.com/finance/historical?q={0}".format(ticker)
        url_string += "&startdate={0}&enddate={0}&output=csv".format(
                          start_date)
        print (url_string)

        try:
            csv = urllib.request.urlopen(url_string).readlines()
        except urllib.error.HTTPError as ex:
            print (ex.msg)
            return None
        csv.reverse()

        csv_str = str(csv[0], 'utf-8')
        print (csv_str)
        ds, open_, high, low, close, volume = csv_str.rstrip().split(',')
        open_, high, low, close = [float(x) for x in [open_, high, low, close]]
        dt = datetime.datetime.strptime(ds, '%d-%b-%y')
        quote = Quote(ticker, dt, close)

        print (quote.ticker, quote.for_date, quote.close)

        return quote

    @staticmethod
    def scrape_quote(ticker, start_date):
        url_string = "http://www.google.com/finance/historical?q={0}".format(ticker)
        url_string += "&startdate={0}&enddate={0}&output=html".format(
                          start_date)
        print (url_string)

        try:
            html_lines = urllib.request.urlopen(url_string).readlines()
            html = ""
            for line in html_lines:
                html += str(line, 'utf-8')
        except urllib.error.HTTPError as ex:
            print (ex.msg)
            return None
        print (html)
        return html

    @staticmethod
    def lxml_scrape_quote(ticker, start_date):
        url_string = "http://www.google.com/finance/historical?q={0}".format(ticker)
        url_string += "&startdate={0}&enddate={0}&output=html".format(
                          start_date)
        print (url_string)

        try:
            html_lines = urllib.request.urlopen(url_string).readlines()
            html_str = b''
            for line in html_lines:
                html_str += line
            #print (html_str)
            tree = html.fromstring(html_str)
            #table_hdr = tree.xpath('//div[@id="prices"]/table/tbody/tr[1]/th[1]')
            table_hdr = tree.xpath('//div[@id="prices"]/table/tr[1]/th/text()')
            table_row = tree.xpath('//div[@id="prices"]/table/tr[2]/td/text()')
            print (table_hdr)
            print (table_row)
        except urllib.error.HTTPError as ex:
            print (ex.msg)
            return None
        #print (html)
        return html

    @staticmethod
    def get_google_stock_info(ticker):
        """
        Get a current stock quote through Google.
        Seems to work sporadically, acts like it is being throttled.
        :param ticker:
        :return:
        """
        url_string = "https://www.google.com/finance/info?q={0}".format(ticker)
        print (url_string)
        #request = urllib.request.Request(url_string, headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:55.0) Gecko/20100101 Firefox/55.0"})
        json_result = []
        try:
            response = urllib.request.urlopen(url_string).readlines()
            json_data = ""
            for line in response:
                json_data += str(line, "utf-8")
            json_result = json.loads(json_data[3:])
        except urllib.error.HTTPError as ex:
            print (str(ex))
            return str(ex)
        return json_result

#Quote.get_quote("VOO", "2017-05-30")
#Quote.get_quote("VPU", "2017-05-30")
#Quote.get_quote("VDC", "2017-05-30")
#Quote.get_quote("SO", "2017-05-30")
#Quote.get_quote("MLPI", "2017-05-30")
#Quote.get_quote("INDEXDJX:.DJI", "2017-05-30")
#Quote.get_quote("INDEXSP:.INX", "2017-05-30")
#Quote.get_quote("INDEXNASDAQ:.IXIC", "2017-05-30")
#Quote.get_quote("usibx", "2017-05-30")
#get_quote("USSBX", "2017-05-30")

#Quote.scrape_quote("usibx", "2017-05-30")
#Quote.lxml_scrape_quote("usibx", "2017-05-30")
j = Quote.get_google_stock_info("bxmx")
print (j)

"""
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