#!/usr/bin/env python

from pylab import gca, draw
import numpy

def cll(index = -1):
    """
    clear last line. removes the last line from the figure.

    To remove a different line, specify the index.

    """
    gca().lines.pop(index)
    draw()

def sll(fname, index = -1):
    """
    Save last line.

    Saves x,y data of the last line, in .npy format.
    Specify the file name.

    To save a different line, specify the index.

    """
    line = gca().lines[index]
    x,y = line.get_data()
    numpy.save(fname, (x,y))
