galvani
=======

<!---
SPDX-FileCopyrightText: 2013-2020 Christopher Kerr, Peter Attia
-->

Read proprietary file formats from electrochemical test stations

## Bio-Logic .mpr files ##

Use the `MPRfile` class from BioLogic.py (exported in the main package)

````
from galvani import BioLogic
import pandas as pd

mpr_file = BioLogic.MPRfile('test.mpr')
df = pd.DataFrame(mpr_file.data)
````

## Arbin .res files ##

Use the res2sqlite.py script to convert the .res file to a sqlite3 database
with the same schema.
