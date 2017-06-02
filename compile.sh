#!/bin/bash

#Import tools for compiling extension binaries
export PATH=$PATH:/usr/lib/ure/bin/
#export PATH=$PATH:/Applications/Contents/Frameworks
# My LO SDK tools were not here.
#export PATH=$PATH:/usr/lib/libreoffice/sdk/bin/
# They were here...
#export PATH=$PATH:/usr/local/share/libreoffice/bin
export PATH=$PATH:/Users/dhocker/LibreOffice5.2_SDK/bin
# This addition was required to make the script work with
# SDK 5.2
export DYLD_LIBRARY_PATH=$OO_SDK_URE_LIB_DIR

#Setup directories 
mkdir "${PWD}"/SMF/
mkdir "${PWD}"/SMF/META-INF/

#Compile the binaries
idlc "${PWD}"/idl/Xsmf.idl
regmerge -v "${PWD}"/SMF/Xsmf.rdb UCR "${PWD}"/idl/Xsmf.urd
rm "${PWD}"/idl/Xsmf.urd

#Copy extension files and generate metadata
cp -f "${PWD}"/src/smf.py "${PWD}"/SMF/
cp -f "${PWD}"/src/morningstar.py "${PWD}"/SMF/
cp -f "${PWD}"/src/yahoo.py "${PWD}"/SMF/
cp -f "${PWD}"/src/yahoo_hist.py "${PWD}"/SMF/
cp -f "${PWD}"/src/html_hist_quote.py "${PWD}"/SMF/
python "${PWD}"/src/generate_metainfo.py

#Package into oxt file
pushd "${PWD}"/SMF/
zip -r "${PWD}"/SMF.zip ./*
popd
mv "${PWD}"/SMF/SMF.zip "${PWD}"/SMF.oxt
