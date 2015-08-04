# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name='galvani',
    version='0.0.2',
    description='Open and process battery charger log data files',
    url='https://github.com/chatcannon/galvani',
    author='Chris Kerr',
    license='GPLv3+',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Natural Language :: English'],
    packages=['galvani'],
    scripts=['scripts/res2sqlite.py'],  # TODO make this use entry_points
    install_requires=['numpy']
)
