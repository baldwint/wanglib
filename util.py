"""This file provides useful utilities for the wanglib package."""

import serial
from time import sleep

class Serial(serial.Serial):
    """Extension of the standard serial class
    to provide some convenient functions"""
    
    def readall(self):
        return self.read(self.inWaiting())

    def ask(self, query, lag=0.1):
        self.write(query)
        sleep(lag)
        return self.readall()
