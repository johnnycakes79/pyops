#!/usr/bin/env python
"""
ePYs is a python library for the manipulation, processing and plotting
of the input and output files of ESA Experiment Planning Software (EPS).

.. WARNING::
   This is a very beta-project. It's not on PyPI and can't be installed
   via PIP.
"""

__author__ = 'Jonathan McAuliffe'
__email__ = 'watch.n.learn@gmail.com'
__version__ = '0.3.1'
__url__ = 'https://github.com/johnnycakes79/epys'

from epys.read import read

from epys.utils import plotly_prep, merge_dataframes