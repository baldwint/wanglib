"""This file provides useful utilities for the wanglib package."""

from time import sleep, time, ctime
from numpy import array
from numpy import exp, sqrt, pi
import numpy
import logging

class InstrumentError(Exception):
    """Raise this when talking to instruments fails."""
    pass

try:
    import serial
except ImportError:
    # PySerial is not installed
    serial = None

def show_newlines(string):
    """
    replace CR+LF with the words "CR" and "LF".
    useful for debugging.

    """
    return string.replace('\r', '<CR>').replace('\n', '<LF>')

if serial:
    class Serial(serial.Serial):
        """
        Extension of PySerial_'s :class:`serial.Serial` class that
        implements a few extra features:

        .. _PySerial: http://pyserial.sourceforge.net/

            - an :meth:`ask` method
            - a :meth:`readall` method
            - auto-appended termination characters
            - in/out logging.
        
        To log whatever's written or read to a serial port,
        pass a filename into the ``log`` kwarg:

        >>> port = Serial('/dev/ttyS0', log='wtf.log')

        To automatically append a newline to each command, specify
        ``term_chars``:

        >>> port.term_chars = '/n'

        This can also be supplied as a keyword argument.

        """

        def __init__(self, *args, **kwargs):
            # make an event logger
            self.logger = logging.getLogger('wanglib.util.Serial')
            # take 'log' kwarg.
            self.logfile = kwargs.pop('log', False)
            if self.logfile:
                self.start_logging(self.logfile)
            # take default termination character
            # by default, append empty string
            self.term_chars = kwargs.pop('term_chars', '')
            # hand off to standard serial init function
            super(Serial, self).__init__(*args, **kwargs)

        def start_logging(self, fname):
            """ start logging read/write data to file. """
            # make log file handler
            lfh = logging.FileHandler(fname)
            self.logger.addHandler(lfh)
            # make log file formatter
            lff = logging.Formatter('%(asctime)s %(message)s')
            lfh.setFormatter(lff)
            # set level low to log everything
            self.logger.setLevel(1)
            self.logger.debug('opened serial port')

        def write(self, data):
            data += self.term_chars
            super(Serial, self).write(data)
            self.logger.debug('write: ' + show_newlines(data))

        def read(self, size=1):
            resp = super(Serial, self).read(size)
            self.logger.debug(' read: ' + show_newlines(resp))
            return resp
        
        def readall(self):
            """
            Automatically read all the bytes from the serial port.

            if :attr:`term_chars` is set, this will continue
            to read until the terminating bytes are received.

            """
            resp = self.read(self.inWaiting())
            if self.term_chars is not '':
                while resp[-len(self.term_chars):] != self.term_chars:
                    resp += self.read(self.inWaiting())
            return resp

        def ask(self, query, lag=0.05):
            """
            Write to the bus, then read response.

            This doesn't seem to work very well.

            """
            self.write(query)
            sleep(lag)
            return self.readall()


# ------------------------------------------------------
# up to this point, this file has dealt with customizing
# communication interfaces (GPIB / RS232). What follows
# are more random (though useful) utilities.
# 
# The two halves of this file serve rather disparate
# needs, and should probably be broken in two pieces.
# Before I actually do that I'd like to trim down 
# dependencies in the rest of the library - I think that
# will go a long way in reducing complexity.
# ------------------------------------------------------

from numpy import log10, floor

def num(string):
    """
    convert string to number. decide whether to convert to int or float.
    """
    if '.' not in string:
        return int(string)
    else:
        return float(string)

def sciround(number, sigfigs=1):
    """
    Round a number to a desired significant figure precision.

    >>> sciround(.000671438, 3)
    .000671

    """
    exponent = floor(log10(number))
    return round(number, -int(exponent) + (sigfigs - 1))

try:
    # importing scipy unnecessarily breaks Ctrl+C handling on windows, see:
    # http://stackoverflow.com/questions/15457786/ctrl-c-crashes-python-after-importing-scipy-stats
    # I am disabling this import because I never use `calibration` anymore,
    # but having it here prevents plotgen from working properly
    #from scipy.optimize import leastsq
    leastsq = None
except ImportError:
    leastsq = None

import csv

if leastsq is not None:
    class calibration(dict):
        """
        a class encapsulating a linear mapping based on measurements.

        Stores calibration pairs, calculates fits to determine cal
        parameters, and provides a function to do it.

        """
        def __init__(self, *args, **kw):
            from scipy.optimize import leastsq
            # initial guess of the cal
            self.param = [1,0]
            # form of the fit function
            self.func = lambda p, x: p[0] * x + p[1]
            dict.__init__(self, *args, **kw)

        def keys(self):
            return array(dict.keys(self))

        def values(self):
            return array(dict.values(self))

        def recal(self):
            """perform the fit routine and return parameters"""
            diff = lambda p, x, y: y - self.func(p, x)
            args = (self.keys(), self.values())
            
            result, win = leastsq(diff, self.param, args)
            if win:
                self.param = result
            else:
                print "fail!!"

        def plot(self):
            """ plot the calibration points and the fit"""
            from pylab import plot
            from numpy import linspace
            plot(self.keys(), self.values(), 'o')
            x = linspace(min(self.keys()), max(self.keys()), 100)
            plot(self.keys(), self.values(), 'o')
            plot(x, self.__call__(x), 'k--')


        def __call__(self, arg):
            """ calculate a conversion based on the current fit parameters """
            return self.func(self.param, arg)

        def save(self, filename):
            """ 
            save the current calibration data to csv file. pass filename as arg.

            >>> cal.save('18oct.csv')

            """
            fl = open(filename, 'w')
            wrt = csv.writer(fl)
            for x, y in self.iteritems():
                wrt.writerow([x, y])

        def load(self, filename):
            """
            load a csv calibration.

            >>> cal.load('18oct.csv')

            """
            rd = csv.reader(open(filename, 'r'))
            for x, y in rd:
                self[num(x)] = num(y)
            self.recal()

    def fit(x, y, func, guess):
        """
        fit data to a given functional form using least squares.

        inputs:
            x, y: data to fit, in arrays.
            func: a function of p and x, where p is a parameter vector
            guess: inital value of p to try.

        outputs:
            pfit: the best-fit parameter set.

        """
        diff = lambda p, x, y: y - func(p, x)
        pfit, win = leastsq(diff, guess, (x, y))
        if win:
            return pfit
        else:
            print "fail!"

def gaussian(p, x):
    """
    gaussian function.

    p is a 4-component parameter vector defining::

        0 -- a baseline offset
        1 -- the area between curve and baseline
        2 -- the location of the maximum
        3 -- the standard deviation

    """
    
    return p[0] + \
    exp(-((x - p[2])**2)/(2 * p[3]**2)) * \
    p[1]  /  (sqrt(2 * pi) * p[3])

def monitor(function, lag = 0.3, absolute = False):
    """
    Periodically yield output of a function, along with timestamp.
    Compatible with :func:`wanglib.pylab_extensions.live_plot.plotgen`.

    :param function: function to call
    :type function: function
    :param lag: interval between calls to ``function`` (default 0.3 seconds)
    :type lag: float
    :param absolute: if True, yielded x values are seconds since
                     epoch. otherwise, time since first yield.
    :type absolute: boolean
    :returns:   a generator object yielding t,y pairs.

    """
    start = 0 if absolute else time()
    while True:
        yield time() - start, function()
        sleep(lag)

def scanner(xvals, set, get, lag = 0.3):
    """
    Generic scan generator - useful for spectra, delay scans, whatever.
    Compatible with :func:`wanglib.pylab_extensions.live_plot.plotgen`.

    :param xvals: values of x over which to scan.
    :type xvals: iterable
    :param set: Function to call on each step that advances the independent
                variable to the next value of ``xvals``. This function should
                take that value as an argument.
    :type set: function
    :param get: Function to call on each step that performs the measurement.
                The return value of this function should be the measurement
                result.
    :type get: function
    :param lag: seconds to sleep between setting and measuring
    :type lag: float
    :returns:   a generator object yielding x,y pairs.

    Example: while scanning triax wavelength, measure lockin x

    >>> from triax.instruments.lockins import egg5110
    >>> from triax.instruments.spex750m import triax320
    >>> from wanglib.pylab_extensions import plotgen
    >>> tr = triax320()
    >>> li = egg5110(instrument(plx,12))
    >>> wls = arange(770, 774, .1)
    >>> gen = scanner(wls, set=tr.set_wl, get=li.get_x)
    >>> result = plotgen(gen)

    Sometimes we will want to set/measure an attribute of an object on each
    step, instead of calling a method. In this case, we can provide an
    (object, attribute_name) tuple in lieu of a function for ``set`` or ``get``.
    For example, in place of the ``gen`` used above, we could do:

    >>> gen = scanner(wls, set=(tr,'wl'), get=(li,'x'))

    Avoid this if you can, though.
    
    """
    for X in xvals:
        if hasattr(set,'__call__'):
            set(X)
        else:
            set[0].__setattr__(set[1], X)
        sleep(lag)
        if hasattr(get,'__call__'):
            Y = get()
        else:
            Y = get[0].__getattribute__(get[1])
        yield X,Y

def averager(func, n, lag=0.1):
    """
    Given a function ``func``, returns an implementation of that
    function that just repeats it ``n`` times, and returns an average
    of the result.

    :param func: function returning a measurement
    :type func: function
    :param n: number of times to call ``func``.
    :type n: int
    :param lag: seconds to sleep between measurements.
    :type lag: float
    :returns:   the average of the ``n`` measurements.

    This is useful when scanning. For example, if scanning a spectrum
    with the lockin like so:

    >>> gen = scanner(wls, set=tr.set_wl, get=li.get_x)

    We can implement a version that averages three lockin measurements
    with a 0.3s delay like so:

    >>> acq = averager(li.get_x, 3, lag=0.3)
    >>> gen = scanner(wls, set=tr.set_wl, get=acq)

    """
    def f(*args, **kwargs):
        ls = []
        ls.append(func(*args, **kwargs))
        for i in range(n - 1):
            sleep(0.1)
            ls.append(func(*args, **kwargs))
        ar = array(ls)
        return ar.mean(axis=0)
    return f

def save(fname, array):
    """
    Save a Numpy array to file.

    :param fname: Filename, as a string
    :param array: Numpy array to save.

    Unlike :meth:`numpy.save`, this function will raise ValueError if
    overwriting an existing file.

    """
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
        numpy.save(fname, array)
    else:
        # if the open statement succeeded, the filename is taken.
        raise ValueError('file exists. choose a different name')

class saver(object):
    """
    Sequential file saver.

    after initializing :class:`saver` with the base filename, use the
    :meth:`save` method to save arrays to sequentially-numbered files.

    >>> s = saver('foo')
    >>> s.save(arange(5)) # saves to 'foo000.npy'
    >>> s.save(arange(2)) # saves to 'foo001.npy'

    """

    def __init__(self, name, verbose=False):
        self.name = name
        self.n = 0
        self.verbose = verbose

    def save(self, array):
        """
        Save an array to the next file in the sequence.

        """
        fname = "%s%03d.npy" % (self.name, self.n)
        save(fname, array)
        self.n +=1
        if self.verbose:
            print "saved as", fname

from contextlib import contextmanager

@contextmanager
def notraceback():
    """
    Context manager to swallow keyboard interrupt.

    Execute any infinitely-looping process in this context, like:

    >>> from time import sleep
    >>> with notraceback():
    ...     while True:
    ...         sleep(0.1)

    If you are planning to interrupt it anyway then you are
    not interested in the traceback and this prevents your
    output from being cluttered.
    """
    try:
        yield
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    from pylab import *
    cal = calibration()
    x = arange(40, 100, 5)
    y = .2 * x + 5
    y += randn(len(y))
    param = [.2,5]
    for i in range(len(x)):
            cal[x[i]] = y[i]
    cal.plot()

