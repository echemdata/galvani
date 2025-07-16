galvani
=======

<!---
SPDX-FileCopyrightText: 2013-2020 Christopher Kerr, Peter Attia

SPDX-License-Identifier: GPL-3.0-or-later
-->

> [!NOTE]  
> This repository is an approximate mirror of https://codeberg.org/echemdata/galvani (originally developed at https://github.com/echemdata/galvani), though the syncing is not automatic. 
> Versions deployed to PyPI package from this repository as the [`datalab-org-galvani-mirror`](https://pypi.org/project/datalab-org-galvani) may not match those of the `galvani` package itself. Documentation may still contain out of date references to the original repository.
> It is unlikely new features will be developed in this mirror, changes will only involve build system, deployment and testing improvements, so please direct your development attention to the codeberg repo linked above.

Read proprietary file formats from electrochemical test stations.

# Usage

## Bio-Logic .mpr files

Use the `MPRfile` class from BioLogic.py (exported in the main package)

```python
from galvani import BioLogic
import pandas as pd

mpr_file = BioLogic.MPRfile('test.mpr')
df = pd.DataFrame(mpr_file.data)
```

## Arbin .res files

Use the `./galvani/res2sqlite.py` script to convert the .res file to a sqlite3 database with the same schema, which can then be interrogated with external tools or directly in Python.
For example, to extract the data into a pandas DataFrame (will need to be installed separately):

```python
import sqlite3
import pandas as pd
from galvani.res2sqlite import convert_arbin_to_sqlite
convert_arbin_to_sqlite("input.res", "output.sqlite")
with sqlite3.connect("output.sqlite") as db:
    df = pd.read_sql(sql="select * from Channel_Normal_Table", con=db)
```

This functionality requires [MDBTools](https://github.com/mdbtools/mdbtools) to be installed on the local system.

# Installation

The latest galvani releases can be installed from [PyPI](https://pypi.org/project/galvani-mirror/) via

```shell
pip install datalab-org-galvani
```

The latest development version can be installed with `pip` directly from GitHub (see note about git-lfs below):

```shell
GIT_LFS_SKIP_SMUDGE=1 pip install git+https://github.com/datalab-org/galvani-mirror
```

## Development installation and contributing 

> [!WARNING]
> 
> This project uses Git Large File Storage (LFS) to store its test files,
> however the LFS quota provided by GitHub is frequently exceeded. 
> This means that anyone cloning the repository with LFS installed will get
> failures unless they set the `GIT_LFS_SKIP_SMUDGE=1` environment variable when
> cloning. 
> The full test data from the last release can always be obtained by
> downloading the GitHub release archives (tar or zip), at
> https://github.com/datalab-org/galvani-mirror/releases/latest
>
> If you wish to add test files, please ensure they are as small as possible,
> and take care that your tests work locally without the need for the LFS files.
> Ideally, you could commit them to your fork when making a PR, and then they
> can be converted to LFS files as part of the review.

If you wish to contribute to galvani, please clone the repository and install the testing dependencies:

```shell
git clone git@github.com:datalab-org/galvani-mirror
cd galvani
pip install -e .\[tests\]
```

Code can be contributed back via [GitHub pull requests](https://github.com/datalab-org/galvani-mirror/pulls) and new features or bugs can be discussed in the [issue tracker](https://github.com/datalab-org/galvani-mirror/issues).
It may also be useful to check the original [issue tracker for galvani](https://github.com/echemdata/galvani).
