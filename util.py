"""This file provides useful utilities for the wanglib package."""

from time import sleep
from numpy import array

class InstrumentError(Exception):
    """Raise this when talking to instruments fails."""
    pass

try:
    import visa as visa_mod
except ImportError:
    visa_avail = False
else:
    visa_avail = True

try:
    import Gpib as Gpib_mod
except ImportError:
    gpib_avail = False
else:
    gpib_avail = True

try:
    import serial
except ImportError:
    ser_avail = False
else:
    ser_avail = True


if gpib_avail:
    class Gpib(Gpib_mod.Gpib):
        """ Extension of the linux-gpib Gpib module. """

        def read(self, *args, **kwargs):
            """ Read from Gpib device, stripping trailing space. """
            result = super(Gpib, self).read(*args, **kwargs)
            return result.rstrip()

        def ask(self, query):
            """
            Write then read.

            Shadows the usual Gpib.ask() method,
            which does something weird.

            """
            self.write(query)
            return self.read()

        
elif visa_avail:
    def Gpib(board, addr, timeout=None):
        inst = visa_mod.instrument("GPIB%d::%d" % (board, addr))
        if timeout is not None:
            inst.timeout = timeout
        return inst
else:
    #raise InstrumentError("no GPIB interface found")
    pass



if ser_avail:
    class Serial(serial.Serial):
        """ Extension of the standard serial class.  """
        
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


def scan_gen(wls, spec, lockin, avgs=1):
    """
    Generator for a scanned spectrum.

    Arguments:
        wls -- list or numpy array containing
                the spectral values to scan over.
        spec -- a spectrometer instance. 
        lockin -- a lockin instance. 

    Keyword Arguments:
        avgs -- the number of data points to average on 
                each spectral value.

    """
#    if lockin is None:
#        lockin = egg5110()
#    if spec is None:
#        spec = triax()

    timeconst, unit = lockin.timeconst
    if unit == "ms":
        timeconst /= 1000.
    elif unit == "s":
        pass
    else:
        raise Exception( "Unknown time unit: %s" % unit)
    for i in range(len(wls)):
        spec.wl = wls[i]
        tally = 0.
        for j in range(avgs):
            sleep(timeconst * 1.2)
            tally += lockin.r[0] # discard unit
        yield tally / avgs

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

