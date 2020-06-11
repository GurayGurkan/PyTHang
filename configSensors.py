# -*- coding: utf-8 -*-
"""
Created on Fri Jan 19 11:19:41 2018

@author: g.gurkan
"""
import numpy as np


class devTorso(object):
    def __init__(self):
        self.gain = np.diag([1/270.5, 1/272.5, 1/253.0])
        self.offset = np.matrix([[12.5],[4.5],[19.0]])
        
class devHead(object):
    def __init__(self):
        self.gain = np.diag([1/275., 1/274., 1/257.5])
        self.offset = np.matrix([[5.],[6.],[-27.5]])
        
class devDual(object):
    def __init__(self):
        self.gain = np.diag([1/270.5, 1/272.5, 1/253.0,1/275., 1/274., 1/257.5])
        self.offset = np.matrix([[12.5],[4.5],[19.0],[5.],[6.],[-27.5]])