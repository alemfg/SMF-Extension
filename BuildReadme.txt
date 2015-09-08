Notes on Building SMF
---------------------

Consider creating a Python3 virtualenv for working with the extension.
I created one named lo-smf. You can test your code outside of the
world of LO.

Run: /usr/local/share/libreoffice/setsdkenv_unix
to create an SDK environment. This step starts a new bash instance and
sets up a number of environment variables and essentially creates its own environment.

cd ~/Source/SMF-Extension
./compile.sh

Output from compile script looks like this:

bash-3.2$ ./compile.sh
mkdir: /Users/dhocker/Source/SMF-Extension-0.7.0/SMF/: File exists
mkdir: /Users/dhocker/Source/SMF-Extension-0.7.0/SMF/META-INF/: File exists
Compiling: /Users/dhocker/Source/SMF-Extension-0.7.0/idl/Xsmf.idl
WARNING: value of key "/UCR/com/smf/ticker/getinfo/XSmf/" already exists.
merging registry "/Users/dhocker/Source/SMF-Extension-0.7.0/idl/Xsmf.urd" under key "UCR" in registry "/Users/dhocker/Source/SMF-Extension-0.7.0/SMF/Xsmf.rdb".
~/Source/SMF-Extension-0.7.0/SMF ~/Source/SMF-Extension-0.7.0
  adding: META-INF/ (stored 0%)
  adding: META-INF/manifest.xml (deflated 60%)
  adding: SMF.xcu (deflated 89%)
  adding: Xsmf.rdb (deflated 89%)
  adding: description.xml (deflated 46%)
  adding: morningstar.py (deflated 71%)
  adding: smf.py (deflated 68%)
  adding: yahoo.py (deflated 60%)
  adding: yahoo_hist.py (deflated 55%)

Add Extension to LibreOffice

Open LibreOffice Calc
Menu: Tools/Extension Manager
Click the Add button.
Navigate to the ~/Source/SMF-Extension directory.
Choose SMF.oxt
This will install the extension or replace the existing extension.

After building you can use the exit command to close the bash instance
that was created by the setsdkenv_unix script.

Running the Tests
-----------------

Open a terminal.
Run: /usr/local/share/libreoffice/setsdkenv_unix
Run: cd ~/Source/SMF-Extension/src #change directory to your source
Run: $UNO_PATH/python smftest.py -f yahoohist -t XOM -d 2015-07-31