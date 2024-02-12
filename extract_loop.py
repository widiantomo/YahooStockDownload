# -*- coding: utf-8 -*-
"""
Created on Sun Sep  9 07:18:54 2018

@author: user
"""
import numpy as np # np is an alias pointing to numpy, but at this point numpy is not linked to numpy.f2py
import numpy.f2py as myf2py # this com

from extract_yahoo_ import *
#dq = __import__(extract_yahoo_)
c = np.load('data.npy')

for x in c:
  download_quotes(x)