#!/usr/bin/env python

"""
This module implements plotting of data while it is being gathered.

"""

from pylab import *

def plotgen(x, data_gen, *args, **kwargs):
    """
    take X/Y data from a generator, and plot it at the same time.

    arguments:
        x           -- the x-axis data.
        data_gen    -- a generator to produce y data.
                       should take x as the argument and yield
                       y values as they are available.

    any extra arguments beyond these are passed to the
    generator you provide.

    """

    # instantiate the provided generator.
    # pass extra args/kwargs to it.
    gen = data_gen(x, *args, **kwargs)

    # make a line. Initially, just zeros.
    # this also casts y to the float type.
    line, = plot(x, x * 0.)
    y = line.get_ydata()
    draw()

    i = 0
    for pt in gen: # for new y value generated
        y[i] = pt  # update our y array
        i+=1

        line.set_ydata(y)       # update plot with new data
        line._invalid = True    # this clears the cache or something
        gca().relim()           # recalculate the limits
        gca().autoscale_view()  # autoscale the bounds to include it all 
        draw()                  # force a redraw
    return line.get_ydata()

if __name__ == '__main__':

    from time import sleep
 
    def silly_gen(x):
        for pt in x:
            sleep(0.1)
            rl = sin(2 * pi * pt)
            rl += 0.1* randn()
            yield rl

    ion()

    x = arange(0,4,0.1)
    y = plotgen(x, silly_gen)

 
