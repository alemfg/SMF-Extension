import urllib.request
import urllib.parse
import urllib.error
from html.parser import HTMLParser
import datetime


class HistQuoteHTMLParser(HTMLParser):
    """
    Customized parser class for web page scraping historical stock quotes.
    See the reference information at the bottom of this file to see
    how the HTML from the Google service looks.
    """
    def __init__(self):
        HTMLParser.__init__(self)
        # Parser state controls
        self.th_on = False
        self.td_on = False
        self.hdrs = []
        self.col = 0
        self.quote_data = {}

    def handle_starttag(self, tag, attrs):
        if tag == "th":
            # print("Target table th tag:", tag, attrs[0])
            self.th_on = True
        elif tag == "td":
            # print("Target table td tag:", tag, attrs)
            self.td_on = True

    def handle_endtag(self, tag):
        pass

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
    def __init__(self, ticker, for_date, close):
        self.close = close
        self.for_date = for_date
        self.ticker = ticker

    @staticmethod
    def __get_quote(ticker, country, exchange, instrument_type, wsj_type, start_date):
        """
        Deprecated in favor of new method with simpler interface.
        :param ticker:
        :param start_date:
        :return:
        """
        template_url = "http://quotes.wsj.com/ajax/historicalprices{0}/4/{1}?MOD_VIEW=page&ticker={1}&country={2}&exchange={3}&instrumentType={4}&num_rows=1&range_days=1&startDate=0{5}&endDate={6}"
        # {0} = WSJ uri type ("", etf, fund)
        # {1} = ticker
        # {2} = country
        # {3} = exchange
        # {4} = instrumentType
        # {5} = startDate
        # {6} = endDate
        url_string = template_url.format(wsj_type, ticker, country, exchange, instrument_type, start_date, start_date)
        print (url_string)

        try:
            html_lines = urllib.request.urlopen(url_string).readlines()
            html_str = ""
            for line in html_lines:
                html_str += str(line, "utf-8")
            #print (html_str)
        except urllib.error.HTTPError as ex:
            print (ex.msg)
            return None

        # Run parser over page source, extracting data of interest
        parser = HistQuoteHTMLParser()
        parser.feed(html_str)

        print (parser.quote_data)

        return Quote(ticker, start_date, float(parser.quote_data["close"].replace(",", "")))


    @staticmethod
    def get_quote(ticker, instrument_type, start_date):
        """
        This works for all of the ticker symbols in our portfolio. However,
        it is not likely to work for non-US securities.
        :param ticker:
        :param instrument_type:
        :param start_date:
        :return:
        """
        # Infer the required WSJ parameters from the symbol type
        if instrument_type == "mutf":
            wsj_type = "FUND"
            url_type = "fund"
        elif instrument_type == "etf":
            wsj_type = "FUND"
            url_type = "etf"
        else:
            wsj_type = "STOCK"
            url_type = ""

        template_url = "http://quotes.wsj.com/ajax/historicalprices{0}/4/{1}?MOD_VIEW=page&ticker={1}&instrumentType={2}&num_rows=1&range_days=1&startDate=0{3}&endDate={4}"
        # {0} = WSJ uri type ("", etf, fund)
        # {1} = ticker
        # {2} = WSJ instrumentType (STOCK or FUND)
        # {3} = startDate
        # {4} = endDate
        url_string = template_url.format(url_type, ticker, wsj_type, start_date, start_date)
        # print (url_string)

        try:
            html_lines = urllib.request.urlopen(url_string).readlines()
            html_str = ""
            for line in html_lines:
                html_str += str(line, "utf-8")
            #print (html_str)
        except urllib.error.HTTPError as ex:
            print (ex.msg)
            return None

        # Run parser over page source, extracting data of interest
        parser = HistQuoteHTMLParser()
        parser.feed(html_str)

        if len(parser.quote_data) == 0:
            print ("Empty response")
            return None

        return Quote(ticker, start_date, float(parser.quote_data["close"].replace(",", "")))

#Quote.get_quote("VOO", "2017-05-30")
#Quote.get_quote("VPU", "2017-05-30")
#Quote.get_quote("VDC", "2017-05-30")
#Quote.get_quote("SO", "2017-05-30")
#Quote.get_quote("MLPI", "2017-05-30")1Dobby1$

#Quote.get_quote("INDEXDJX:.DJI", "2017-05-30")
#Quote.get_quote("INDEXSP:.INX", "2017-05-30")
#Quote.get_quote("INDEXNASDAQ:.IXIC", "2017-05-30")
#Quote.get_quote("usibx", "2017-05-30")
#get_quote("USSBX", "2017-05-30")

#Quote.scrape_quote("usibx", "2017-05-30")
#Quote.lxml_scrape_quote("usibx", "2017-05-30")

"""
The problem with the  WSJ interface is all of the extra details that are required.
The ticker symbol alone is not enough. The country could probably be defaulted
to US, the exchange, instrument_type and wsj_type don't have any easy/simple
way to be determined. At this time the only way to determine these is 
via manual trial on the WSJ web site.

After a number of trials, it was found that the country and exchange could be omitted.
"""
# j = Quote.get_quote("BXMX", "US", "XNYS", "STOCK", "", "2017-05-31")
# print (j)
# j = Quote.get_quote("VYM", "US", "ARCX", "FUND", "fund", "2017-05-31")
# print (j)
# j = Quote.get_quote("VYM", "etf", "2017-05-31")
# print (j.ticker, j.close)
# j = Quote.get_quote("USIBX", "mutf", "2017-05-31")
# print (j.ticker, j.close)
# j = Quote.get_quote("MMM", "", "2017-05-31")
# print (j.ticker, j.close)
# j = Quote.get_quote("PFF", "etf", "2017-05-31")
# print (j.ticker, j.close)
# j = Quote.get_quote("IWO", "etf", "2017-05-31")
# print (j.ticker, j.close)
# j = Quote.get_quote("AAPL", "", "2017-05-31")
# print (j.ticker, j.close)

# A list of all of the symbols currently needed
ticker_list = [
["MMM", ""],
["BRK.B", ""],
["BRK.A", ""],
["PTY", ""],
["ETV", ""],
["ETW", ""],
["VYM", "etf"],
["VIG", "etf"],
["IVE", "etf"],
["IVW", "etf"],
["IWF", "etf"],
["IWO", "etf"],
["IWP", "etf"],
["VBK", "etf"],
["NEA", ""],
["PFF", "etf"],
["FOF", ""],
["PTY", ""],
["QQQX", ""],
["BXMX", ""],
["PZA", "etf"],
["BSCJ", "etf"],
["BSCK", "etf"],
["BSCL", "etf"],
["BSCM", "etf"],
["BSCN", "etf"],
["BSCO", "etf"],
["USIBX", "mutf"],
["USSBX", "mutf"],
["AAPL", ""],
["AMZN", ""],
["GOOG", ""],
["MLPI", ""],
["SO", ""],
["VPU", "etf"],
["VOO", "etf"],
["VDC", "etf"],
["FVD", "etf"]
]

for t in ticker_list:
    j = Quote.get_quote(t[0], t[1], "2017-05-31")
    print(j.ticker, j.close)

"""
http://quotes.wsj.com/ajax/historicalpricesetf/4/PFF?MOD_VIEW=page&ticker=PFF&instrumentType=FUND&num_rows=1&range_days=1&startDate=2017-05-30&endDate=2017-05-30
                                                       ---   ---                      ---                ----                                    
stock                                                  ---   ticker                   ticker             STOCK                                  
mutf                                                   fund  ticker                   ticker             FUND                                    
etf                                                    etf   ticker                   ticker             FUND                                    

<div class="rr_historical module fullpage" id="cr_historical_page" data-ticker="PFF" data-country="US" data-exchange="ARCX" data-type="FUND" data-page="">
	<h1></h1>
	<div class="historical_topnav">
		<div class="dateRange_nav">
			<span><input type="text" value="2017-05-30" class="datePicker" id="selectDateFrom" /></span>
			<span>to</span>
			<span><input type="text" value="2017-05-30" class="datePicker" id="selectDateTo" /></span>
			<span><input type="button" value="go" id="datPickerButton"/></span>
		</div>
		<div class="nav_right">
			<a href="#" class="dl_button" id="dl_spreadsheet">Download a Spreadsheet</a>
		</div>
	</div>
		<div class="scrollHeader">
			<table class="cr_dataTable">
				<thead>
					<tr>
						<th>DATE</th>
						<th>OPEN</th>
						<th>HIGH</th>
						<th>LOW</th>
						<th>CLOSE</th>
					</tr>
				</thead>
			</table>
		</div>
		<div id="historical_data_table">
			<div class="scrollBox">
				<table class="cr_dataTable">
					<tbody>
					<tr>
						<td>05/30/17</td>
					  	<td>39.0700</td>
					  	<td>39.0770</td>
					  	<td>38.9600</td>
					  	<td>38.9900</td>
					</tr>
					</tbody>
				</table>
			</div>
		</div>
		
		</div>"""