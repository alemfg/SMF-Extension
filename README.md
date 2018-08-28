SMF Extension for LibreOffice Calc (Forked Version)
===================================================
The SMF extension allows you to create customized spreadsheets with stock market data directly from the web.
Currently supported online sources include
* [Morningstar](http://morningstar.com)
* [Yahoo Finance](http://finance.yahoo.com)
* [Google Historical Finance](http://www.google.com/finance/historical)
* [Intrinio](https://www.intrinio.com)

### Download   
You can download the latest version of the SMF Extension [here](https://github.com/dhocker/SMF-Extension/releases/latest).

**NOTE**: The extension itself is SMF.oxt.  The example .ods worksheets demonstrate how to use the extension.

### Before Installing

LibreOffice runs on multiple operating systems. For unknown reasons, the content of a LibreOffice install is
different depending on the operating system. In particular, LibreOffice ships with an embedded version of
Python and the configuration of the embedded version varies significantly.

#### Windows

The forked SMF Extension uses Sqlite3 to cache historical price quotes. Unfortunately, the Windows version
of LibreOffice does not come with Sqlite3. If you want to use the forked SMF Extension on Windows, you will
need to install Python 3 and set up PYTHONPATH according to your installation. See the prerequisite installation
instructions below.

#### macOS

Some of the web services used by the forked SMF Extension require secure connections through HTTPS.
The urllib package in the embedded version of Python does not recognize or use the CA certificates
installed under macOS. To compensate for this issue you will need to install the
[certifi package](https://github.com/certifi/python-certifi) and create an intrinio.conf file.
Refer to the prerequisite installation instructions below.

#### Linux/Ubuntu

To be determined.

#### Intrinio Service

If you want to use the Intrinio historical quote function you will need to obtain a free [Intrinio](https://www.intrinio.com)
account. Once you have signed up for an account you can get the [username and password keys](https://intrinio.com/account)
that are required to access the Intrinio service. These keys need to go into the intrinio.conf file as described
in the prerequisite installation instructions below.

### Installation

There are two major steps for installation.

1. Install/setup prerequisites.
1. Install the extension under LibreOffice

#### Install/Setup Prerequisites

##### Windows

If you want to run the SMF Extension under Windows,
you need to install the full version of [Python 3](https://www.python.org/downloads/)
that is used with LibreOffice. For LibreOffice 5 and 6 Python 3.5.1 should work.
Be sure to note where you install it. For simplicity, you might consider
installing to C:\python35 or C:\Program Files\python35. Be sure to install the 
x86_64 version (aka the 64-bit version).

After you install Python 3.5.1, go to the Control Panel and set up the
PYTHONPATH variable. Open the menu and type **environment variables**.
This should lead you to the System Properties dialog box. Click on the
**Environment Variables** button.

Create a new **user** variable named PYTHONPATH. Set the value to the following.
```
c:\python35;c:\python35\Lib;c:\python35\Lib\site-packages;c:\python35\Lib\sqlite3;c:\python35\DLLs
```
This assumes you installed Python 3.5.1 to C:\python35. If you installed to a
different directory, adjust accordingly.

##### macOS

If you want to use the Intrinio service, you need to install the [certifi package](https://github.com/certifi/python-certifi)
package. The easiest way to do this is to open a terminal and enter the following commmand.

```
pip install certifi
```

This will install the certifi package for the system. If you are using Python virtual environments,
you can install certifi in a VENV by activating the VENV and running the
same command. The important file in the certifi package is cacert.pem.

On a stock macOS system the cacert.pem file should be found at
```
/Library/Python/X.X/site-packages/certifi/cacert.pem
```
where X.X is the version of Python. Typically the version will be something
like 2.7. You will need the location of the cacert.pem file to set
up the Intrinio service.

##### Linux/Ubuntu

To be determined.

##### Intrinio

In order to use the Intrinio service you must set up an intrinio.conf file.
For Windows, this file goes in the LOCALAPPDATA directory.

```
c:\Users\username\AppData\Local\libreoffice\intrinio\intrinio.conf
```

Here, username will be whatever your Windows user name is.

For macOS and Linux, this file goes in the home directory.

```
~/username/libreoffice/intrinio/intrinio.conf
```

The intrinio.conf file is JSON formatted text specifying the Intrinio username and
password plus the full path to the cacert.pem file. Note that the path
to the cacert.pem file is only required for macOS. Here's an example.

```
{
"user":"intrinio-user-id-goes-here",
"password":"intrinio-password-goes-here",
"certifi":"/for/macOS/path/to/certifi/cacert.pem"
}
```

Once you have created the intrinio.conf file, you should set its file
permissions so only you have read/write access to it. Otherwise, your
Intrinio username and password could be exposed.

If you open a LibreOffice Calc file containing Intrinio references before
creating the intrinio.conf file, the extension will prompt you for Intrinio
access credentials. However, it does not do anything with the cacert.pem
file. In this case, the intrinio.conf file will be created for you. If
you are on Windows all you will have to do is set the file permissions
on intrinio.conf. On macOS you will still need to edit the intrinio.conf
file for the cacert.pem location.

#### Install Extension

Once you have dealt with the prerequisites you can install the extension.
If you have not fulfilled the prerequisites, you are likely to encounter
errors and LibreOffice does not seem to handle errors very gracefully.

1. Download the latest version of SMF.oxt [here](https://github.com/dhocker/SMF-Extension/releases/latest).
1. Start LibreOffice.
1. Select Menu -> Tools -> Extension Manager.
1. Click the Add button.
1. In the file selection dialog, navigate to where you downloaded SMF.oxt and select it.
1. LibreOffice will install the extension. This may take some time.

### Usage

The SMF Extension adds several new functions to Calc:
```
GETYAHOO(Ticker,Datacode) 
GETMORNINGKEY(Ticker,Datacode) 
GETMORNINGFIN(Ticker,Datacode)
GETMORNINGQFIN(Ticker,Datacode)
GETHISTORICALQUOTE(Ticker, Date)
GETINTRINIOQUOTE(Ticker, Date)
```  

Quotes **must** be used when entering the ticker directly ex: ```GETYAHOO("AAPL",1)```, but are **not** needed when referencing another cell ex: ```GETYAHOO(A1,1)```.

In the latter case the data in A1 should be ```AAPL```, not ```"AAPL"```.

**NOTE**: The full set of datacodes are demonstrated in the example .ods worksheets included with the release.

Dates should be in ISO format YYYY-MM-DD.

### Notes

Somewhere around 5/15/2017 Yahoo terminated its historical stock data service. As a result the Yahoo historical data
function was removed and partially replaced by two new functions.

* A Google based function that can return the closing price for a given stock on a given date.
* An [Intrinio](https://www.intrinio.com) based function that can return the closing price for a given stock on a given date.

Intrinio is a relatively new service that can provide a vast amount of stock
market related data. Some data is free (like the API used to get historical stock quotes) but
has limitations on quantity. For example, with a free account you can request 500 data points
per day. While the free account has limitations, the service is reliable.
Refer to the web site for details.

### Support

For general support please visit the [forums](http://forum.openoffice.org/en/forum/index.php).
If you find a bug or wish to request a feature please file an issue at the [issue tracker](http://github.com/dhocker/SMF-Extension/issues).

### Contribute

Help is always welcome with development.  If you would like to contribute you will need to fork the main repo,
make your changes, and send a [pull request](http://github.com/dhocker/SMF-Extension/pulls) to have your
changes moderated and merged back into the main repo. Details on that process can be found
[here](https://help.github.com/articles/set-up-git/).


### License

The SMF Extension is released under the [![][shield:LGPL3]][License:3.0] which in layman's terms means:  

* You are permitted to use, copy and redistribute the work "as-is".
* You may adapt, remix, transform and build upon the material, releasing any derivatives under your own name.
* You may use the material for commercial purposes as long as the derivative is licenced under the GPL.
* You must track changes you make in the source files.
* You must include or make available the source code with your release.

### Other Contributors and Thanks!
* Villeroy - conversion from string to float to make the extension useful
* karolus - optimization of keymapping code
* Corey Goldberg - Inspiration with the Yahoo portion of the extension
* Dave Hocker - Google Financial Historical data support, Intrinio historical data support.

[License:3.0]: http://www.gnu.org/licenses/lgpl.html
[shield:release-latest]: http://img.shields.io/github/release/madsailor/SMF-Extension.svg
[shield:LGPL3]: http://img.shields.io/badge/license-LGPL%20v.3-blue.svg
