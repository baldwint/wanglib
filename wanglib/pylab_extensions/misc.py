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

    if not fname.endswith('.npy'):
        # append file extension.
        fname = fname + '.npy'
        # usually the numpy function does this, but
        # to guard against overwrites, we should do it ourselves.

    try:
        # test to see if the file exists
        open(fname, 'r')
    except IOError:
        # if an error was raised, the filename is available
        numpy.save(fname, (x,y))
        if blink:
            bll(index) # blink the line to indicate a successful save
    else:
        # if the open statement succeeded, the filename is taken.
        raise ValueError('file exists. choose a different name')


# some line-editing functions

def relim(line):
    """ redraw the line's figure to include the line. """
    line.get_axes().relim()
    line.get_axes().autoscale_view()
    line.get_figure().canvas.draw()

def apply_mask(line, mask):
    """ mask x and y (to remove bad points, etc). """
    x,y = line.get_data()
    y[numpy.invert(mask)] = None
    line.set_ydata(y)
    relim(line)

def apply_offset(line, offset):
    """ move the line up or down """
    newdata = line.get_ydata() + offset
    line.set_ydata(newdata)
    relim(line)

def apply_reference(line, ref):
    """ apply reference data (for absorption spectra) """
    absorption = numpy.log(ref/line.get_ydata())
    line.set_ydata(absorption)
    relim(line)


