# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2014-2020 Christopher Kerr <chris.kerr@mykolab.ch>
#
# SPDX-License-Identifier: GPL-3.0-or-later

import os.path

from setuptools import setup

with open(os.path.join(os.path.dirname(__file__), "README.md")) as f:
    readme = f.read()

setup(
    name="galvani",
    version="0.4.1",
    description="Open and process battery charger log data files",
    long_description=readme,
    long_description_content_type="text/markdown",
    url="https://github.com/echemdata/galvani",
    author="Chris Kerr",
    author_email="chris.kerr@mykolab.ch",
    license="GPLv3+",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Natural Language :: English",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Scientific/Engineering :: Chemistry",
    ],
    packages=["galvani"],
    entry_points={
        "console_scripts": [
            "res2sqlite = galvani.res2sqlite:main",
        ],
    },
    python_requires=">=3.6",
    install_requires=["numpy"],
    tests_require=["pytest"],
)
