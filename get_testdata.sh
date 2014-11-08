#!/bin/sh

## Test data are posted on FigShare, listed in this article
# http://figshare.com/articles/galvani_test_data/1228760

mkdir -p tests/testdata
cd tests/testdata

/usr/bin/wget -i - <<END_FILELIST
http://files.figshare.com/1778905/arbin1.res
http://files.figshare.com/1778937/bio_logic2.mpt
http://files.figshare.com/1778938/bio_logic5.mpt
http://files.figshare.com/1778939/bio_logic1.mpr
http://files.figshare.com/1778940/bio_logic6.mpr
http://files.figshare.com/1778941/bio_logic4.mpt
http://files.figshare.com/1778942/bio_logic5.mpr
http://files.figshare.com/1778943/bio_logic2.mpr
http://files.figshare.com/1778944/bio_logic6.mpt
http://files.figshare.com/1778945/bio_logic1.mpt
http://files.figshare.com/1778946/bio_logic3.mpr
http://files.figshare.com/1780444/bio_logic4.mpr
http://files.figshare.com/1780529/121_CA_455nm_6V_30min_C01.mpr
http://files.figshare.com/1780530/121_CA_455nm_6V_30min_C01.mpt
http://files.figshare.com/1780526/CV_C01.mpr
http://files.figshare.com/1780527/CV_C01.mpt
END_FILELIST
