#!/usr/bin/env python

from pylab import gca, draw
import numpy
from time import sleep

def cll(index = -1):
    """
    clear last line. removes the last line from the figure.

    To remove a different line, specify the index.

    """
    ax = gca()
    ax.lines.pop(index) # delete the line
    ax.relim()          # recalc limits
    ax.autoscale_view()
    draw()              # redraw

def bll(index = -1, lag = 0.3):
    """
    blink the last line, identifying it

    """

    line = gca().lines[index]
    lw, ms = line.get_lw(), line.get_ms() # preserve original state
    line.set_lw(lw * 2) # double the width of lines
    line.set_ms(ms * 2) # double the size of markers
    draw()
    sleep(lag) 
    line.set_lw(lw) # restore original linewithds
    line.set_ms(ms) # and marker sizes
    draw()


def sll(fname, index = -1, blink = True):
    """
    Save last line.

    Saves x,y data of the last line, in .npy format.
    Specify the file name.

    To save a different line, specify the index.

    """
    line = gca().lines[index]
    x,y = line.get_data()
    numpy.save(fname, (x,y))
    if blink:
        bll(index) # blink the line to indicate a successful save
