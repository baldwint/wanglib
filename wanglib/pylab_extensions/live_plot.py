#!/usr/bin/env python

"""
This module facilitates plotting of data while it is being gathered.

To use this, you will need to implement your data gathering
using Python generators_. A generator is like a Python function
that, rather than returning data all at once (with the
``return`` statement), returns it point by point (with the
``yield`` statement).

.. _generators: http://wiki.python.org/moin/Generators

Suppose we have a ``spex`` spectrometer object, and a
``lockin`` object that we are using to detect the signal at
the output slit of the spectrometer. Here is an example of a
generator we might use to scan a spectrum, while yielding
values along the way:

>>> def scan_wls(wls):
...     for wl in wls:
...         spex.set_wl(wl)
...         sleep(0.1)
...         val = lockin.get_x()
...         yield wl, val

.. note :: This pattern is so common that a shorthand is provided for it in :func:`wanglib.util.scanner`.

Then, if we wanted to scan from 800nm to 810nm, we would do

>>> scan = scan_wls(numpy.arange(800, 810, 0.1))
>>> for x,y in scan:
...     print x,y

This will print the data to STDOUT, but we could also:

 - save it to a python list using `list comprehensions`_
 - save it as a numpy object using :func:`numpy.fromiter`
 - plot it progressively using :func:`wanglib.pylab_extensions.live_plot.plotgen`

.. _`list comprehensions`: http://docs.python.org/tutorial/datastructures.html#list-comprehensions

"""

from pylab import plot, gca, draw

def plotgen(gen, ax=None, **kwargs):
    """
    Take X,Y data from a generator, and plot it at the same time.

    :param gen: a generator object yielding X,Y pairs.
    :param ax: an axes object (optional).
    :returns: an array of the measured Y values.

    Any extra keyword arguments are passed to the plot function.

    For example, we could plot progressively from our
    ``scan_wls`` example above:

    >>> wls = arange(800, 810, 0.1))
    >>> plotgen(scan_wls(wls))
    # ... measures data, plotting as it goes along ...

    After `scan_wls` yields its last value, it will return the
    complete array of measured Y values. So you can use it
    like this:

    >>> ref = plotgen(scan_wls(wls))   # measure reference spectrum and plot it
    >>> trn = plotgen(scan_wls(wls))   # measure transmission spectrum and plot it
    >>> plot(wls, log(ref/trn), 'k--') # plot absorption spectrum

    """
    if ax is None:
        ax = gca()

    # maintain x and y lists (we'll append to these as we go)
    x = []
    y = []

    # make a (initially blank) line.
    line, = ax.plot(x, y, **kwargs)

    for pt in gen: # for new y value generated

        x.append(pt[0])
        y.append(pt[1])

        line.set_data(x, y)      # update plot with new data
        line._invalid = True     # this clears the cache or something
        ax.relim()               # recalculate the limits
        ax.autoscale_view()      # autoscale the bounds to include it all
        ax.figure.canvas.draw()  # force a redraw
    return line.get_ydata()

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
            rl = sin(2 * pi * pt) + 6
            rl += 0.1* randn()
            yield pt, rl

    ion()

    x = arange(0,4,0.1)
    y = plotgen(silly_gen(x))

 
