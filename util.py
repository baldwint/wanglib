"""This file provides useful utilities for the wanglib package."""

from time import sleep, time, ctime
from numpy import array

class InstrumentError(Exception):
    """Raise this when talking to instruments fails."""
    pass

try:
    import serial
except ImportError:
    ser_avail = False
else:
    ser_avail = True

def show_newlines(string):
    """
    replace CR+LF with the words "CR" and "LF".
    useful for debugging.

    """
    return string.replace('\r', '<CR>').replace('\n', '<LF>')

if ser_avail:
    class Serial(serial.Serial):
        """
        Extension of the standard serial class.
        
        to log whatever's written or read, pass a filename into
        the 'log' kwarg.


        """

        def __init__(self, *args, **kwargs):
            # take 'log' kwarg.
            self.logfile = kwargs.pop('log', False)
            if self.logfile:
                self.start_logging(self.logfile)
            # hand off to standard serial init function
            super(Serial, self).__init__(*args, **kwargs)

        def start_logging(self, fname):
            """
            start logging in/out data.

            """
            self.lf = open(fname, 'a')
            self.start = time()
            self.lf.write('\n\nstart logging at %s\n\n' % ctime(self.start))
            self.lf.write('time (s) ' + 'event  ' + 'data' +'\n')
            self.lf.write('-'*8 + ' ' + '-'*5 + '  ' + '-'*4 + '\n\n')

        def log_something(self, event, data):
            if self.logfile:
                self.lf.write('% 8.2f ' % self.clock())
                self.lf.write('%5s: ' % str(event)[:5])
                self.lf.write('%s\n' % show_newlines(data))

        def clock(self):
            return time() - self.start

        def write(self, data):
            super(Serial, self).write(data)
            self.log_something('write', data)

        def read(self, size=1):
            resp = super(Serial, self).read(size)
            self.log_something('read', resp)
            return resp
        
        def readall(self):
            """Automatically read all the bytes from the serial port."""
            return self.read(self.inWaiting())

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

def num(string):
    """
    convert string to number. decide whether to convert to int or float.
    """
    if '.' not in string:
        return int(string)
    else:
        return float(string)


from scipy.optimize import leastsq
import csv

class calibration(dict):
    """
    a class encapsulating a linear mapping based on measurements.

    Stores calibration pairs, calculates fits to determine cal
    parameters, and provides a function to do it.

    """
    def __init__(self, *args, **kw):
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

# density plot was previously defined here
from wanglib.pylab_extensions import density_plot

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

