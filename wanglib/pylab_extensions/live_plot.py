#!/usr/bin/env python

"""
This module facilitates plotting of data while it is being gathered.

"""

from pylab import plot, gca, draw
from collections import deque
import itertools

def plotgen(gen, ax=None, maxlen=None, **kwargs):
    """
    Take X,Y data from a generator, and plot it at the same time.

    :param gen: a generator object yielding X,Y pairs.
    :param ax: an axes object (optional).
    :param maxlen: maximum number of points to retain (optional).
    :returns: an array of the measured X and Y values.

    Any extra keyword arguments are passed to the plot function.

    ``gen`` can yield any even number of values, and these are
    interpreted as a set of X,Y pairs. That is, if the provided
    generator yields 4 values each time, plotgen will plot two lines -
    with the first line updated from the [0:2] slice and the second
    line updated from the [2:4] slice.

    ``ax`` is the axes object into which the line(s) are plotted. By
    default, the current axes. ``ax`` can also be a tuple of axes
    objects, as long as the tuple is the same length as the number of
    lines being plotted. Each line is then plotted into the
    corresponding axes.

    ``maxlen``, when provided, limits the buffer size. When the
    plotted lines each grow to this number of points, the oldest data
    points will start being trimmed off the line's trailing end.

    """
    import matplotlib
    if 'inline' in matplotlib.get_backend():
        from IPython import display

    if ax is None:
        ax = gca()

    # obtain first value
    points = next(gen)

    try:
        len(ax) # if a tuple of axes was provided, do nothing
    except TypeError:
        # if not, plot all lines to the same axes
        ax = (ax,) * (len(points) / 2)

    assert len(ax) == len(points) / 2

    # maintain x_n and y_n lists (we'll append to these as we go)
    deques = [deque([point], maxlen) for point in points]

    # make some (initially length-1) lines.
    lines = []
    for axis, x, y in zip(ax, deques[::2], deques[1::2]):
        line, = axis.plot(x, y, **kwargs)
        lines.append(line)
    assert len(lines) == len(deques) / 2

    for points in gen: # for new x_n,y_n tuple generated

        # append to the deques
        for pt,deq in zip(points, deques):
            deq.append(pt)

        # update the lines
        for line,xdata,ydata in zip(lines, deques[::2], deques[1::2]):
            line.set_data(xdata, ydata)  # update plot with new data
            line._invalid = True         # this clears the cache?

        # rescale the axes
        for axis in ax:
            axis.relim()           # recalculate the limits
            axis.autoscale_view()  # autoscale the bounds to include it all

        # redraw the figure
        if 'inline' in matplotlib.get_backend():
            display.clear_output(wait=True)
            display.display(ax[0].figure)
        else:
            ax[0].figure.canvas.draw()  # force a redraw

    result = [line.get_data() for line in lines]
    return list(itertools.chain(*result))

if __name__ == '__main__':

    # example usage of the plotgen function.
    # run this file as a script to test.

    from time import sleep
    from pylab import *

    def silly_gen(x):
        """
        a silly generator function producing 'data'
        (really just a sine wave plus noise)

        """
        for pt in x:
            sleep(0.1)
            rl = sin(2 * pi * pt) + 6 + 0.1* randn()
            r2 = cos(2 * pi * pt) + 6 + 0.1* randn()
            yield pt, rl, pt, r2

    ion()

    a1 = subplot(211)
    a2 = subplot(212)

    x = arange(0,4,0.1)
    y = plotgen(silly_gen(x), ax=(a1,a2))

