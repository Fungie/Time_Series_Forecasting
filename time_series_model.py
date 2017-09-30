#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Sep 30 08:59:50 2017

@author: aurenferguson
"""
# Loading libs
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Reading data in
target = pd.read_excel('/Users/aurenferguson/Documents/timeseries_challenge/data/EagleAlphaQuantAnalystTestData.xlsx')
data = pd.read_excel('/Users/aurenferguson/Documents/timeseries_challenge/data/EagleAlphaQuantAnalystTestData.xlsx',
                     sheetname = 1)
