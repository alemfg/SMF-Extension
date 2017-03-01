Notes on Building SMF-Extension
-------------------------------

macOS
-----

Consider creating a Python3 virtualenv for working with the extension.
I created one named lo-smf. You can test your code outside of the
world of LO.

NOTE: Depending on your macOS version you may need to fully disable SIP.

Install the LibreOffice SDK. As of LibreOffice 5.2.4, the SDK is merely a directory
in the ditribution .dmg file. Copy the SDK directory to a preferred location
such as your home directory. For purposes of example, consider the SDK copied to
~/LibreOffice5.2_SDK.

Run the environment/configuration script.
	cd ~/LibreOffice5.2_SDK
	./setsdkenv_unix
	
The first time this script is run it will ask a number of questions. The default
answers chould be adquate. When the script finishes you will be in a new bash shell.

Change to your SMF directory and run the build.
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
Remove the existing SMF extension (if it exists).
Click the Add button.
Navigate to the ~/Source/SMF-Extension directory.
Choose SMF.oxt
This will install the extension or replace the existing extension.

After building you can use the exit command to close the bash instance
that was created by the setsdkenv_unix script.

Running the Tests
-----------------

macOS
-----

Open a terminal.
Run: ~/LibreOffice5.2_SDK/setsdkenv_unix
Run: cd ~/Source/SMF-Extension/src #change directory to your source
Run: /Applications/LibreOffice.app/Contents/Resources/python smftest.py -f yahoohist -t XOM -d 2017-02-27

Windows
-------

TBD
