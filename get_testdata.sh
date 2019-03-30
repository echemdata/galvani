#!/bin/sh

## Test data are posted on FigShare, listed in this article
# http://figshare.com/articles/galvani_test_data/1228760

mkdir -p tests/testdata
cd tests/testdata

/usr/bin/wget --continue -i - <<END_FILELIST
https://files.figshare.com/1778905/arbin1.res
https://files.figshare.com/1778937/bio_logic2.mpt
https://files.figshare.com/1778938/bio_logic5.mpt
https://files.figshare.com/1778939/bio_logic1.mpr
https://files.figshare.com/1778940/bio_logic6.mpr
https://files.figshare.com/1778941/bio_logic4.mpt
https://files.figshare.com/1778942/bio_logic5.mpr
https://files.figshare.com/1778943/bio_logic2.mpr
https://files.figshare.com/1778944/bio_logic6.mpt
https://files.figshare.com/1778945/bio_logic1.mpt
https://files.figshare.com/1778946/bio_logic3.mpr
https://files.figshare.com/1780444/bio_logic4.mpr
https://files.figshare.com/1780529/121_CA_455nm_6V_30min_C01.mpr
https://files.figshare.com/1780530/121_CA_455nm_6V_30min_C01.mpt
https://files.figshare.com/1780526/CV_C01.mpr
https://files.figshare.com/1780527/CV_C01.mpt
END_FILELIST
