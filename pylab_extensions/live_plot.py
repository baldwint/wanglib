#!/usr/bin/env python

"""
This module implements plotting of data while it is being gathered.

"""

from pylab import *

def plotgen(data_gen, *args, **kwargs):
    """
    take X/Y data from a generator, and plot it at the same time.

    arguments:
        data_gen    -- a generator to produce x and y data.
                       should yield x and y values as they are available.

    any extra arguments beyond these are passed to the
    generator you provide.

    """

    # instantiate the provided generator.
    # pass extra args/kwargs to it.
    gen = data_gen(*args, **kwargs)

    # maintain x and y lists (we'll append to these as we go)
    x = []
    y = []
    # make a (initially blank) line.
    line, = plot(x, y) 

    i = 0
    for pt in gen: # for new y value generated
        
        x.append(pt[0])
        y.append(pt[1])
        i+=1

        line.set_data(x, y)     # update plot with new data
        line._invalid = True    # this clears the cache or something
        gca().relim()           # recalculate the limits
        gca().autoscale_view()  # autoscale the bounds to include it all 
        draw()                  # force a redraw
    return line.get_ydata()

if __name__ == '__main__':

    # example usage of the plotgen function.
    # run this file as a script to test.

    from time import sleep
 
    def silly_gen(x):
        """
        a silly generator function producing 'data'
        (really just a sine wave plus noise)

        """
        for pt in x:
            sleep(0.1)
            rl = sin(2 * pi * pt) + 6
            rl += 0.1* randn()
            yield pt, rl

    ion()

    x = arange(0,4,0.1)
    y = plotgen(silly_gen, x)

 
