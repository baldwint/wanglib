#!/usr/bin/env python

"""
Utilities for generating and displaying SLM phase masks.

Functions here support use of the Spatial Light Modulator
for use as a programmable grating, pulse shaper, etc.

"""

import numpy
import Image
import StringIO
import xmlrpclib
from wanglib.util import InstrumentError, calibration
from time import sleep

def sinewave(arg):
    """
    oscillates between 0 and 1
    argument given in 2pi units

    """
    return 0.5 * (1 - numpy.sin(2 * numpy.pi * arg))

def sawtooth(arg):
    """
    gives values between 0 and 1
    argument given in 2pi units

    """
    return numpy.remainder(arg,1.0)

def zebra(arg):
    """
    switches between 0 and 1
    argument given in 2pi units

    """
    return numpy.around(numpy.remainder(arg,1.0))

options = { 
    # a registry of grating function types
    "Sawtooth": sawtooth,
    "Sine Wave": sinewave,
    "Zebra": zebra
    }

class grating:
    """
    This class defines an object which acts as a
    function to produce a grating from an array of 
    pixel numbers (and optionally phase offsets).

    """
    def __init__(self, spacing, kind = "Sawtooth"):
        self.kind = kind
        self.spacing = spacing

    variableSpacing = False
    # matters only when spacing is given as array
    # True (False) means spacing will be varied 
    # parallel (perpendicular) to the grating axis
    # if spacing is a scalar, it is not varied

    variablePhase = False
    # matters only when phase is given as array
    # True (False) means phase will be varied 
    # parallel (perpendicular) to the grating axis
    # if phase is a scalar, it is not varied

    def __call__(self, coordinate, phase = 0.0):
        # phase is a(n array of) phase shifts
    
        # first find the unshifted argument
        if not self.variableSpacing:
            findarg = numpy.true_divide.outer
        else:
            findarg = numpy.true_divide
        arg = findarg(coordinate,self.spacing)

        # add in the shift
        if not self.variablePhase:
            addshift = numpy.add.outer
        else:
            addshift = numpy.add
        arg = addshift(arg,phase)
        
        # evaluate the function
        return options[self.kind](arg)

def scale(value, factor, baseline=0):
    """
    uniformly scale a value (or array)
    by a multiplicative factor (or array of factors)
    about a baseline value (or array of baselines)

    """
    return factor * (value - baseline) + baseline 

def maprange(value, targetrange):
    """
    map an array or value from [0,1] 
    to targetrange = [top,bottom]
    (usually [0,255])

    """
    top = targetrange[1]
    bottom = targetrange[0]
    return ((top - bottom) * value) + bottom

class pattern(object):
    """
    Boilerplate class for specialized gratings
    eg deflectors, pulse shapers, bessel beams

    Pass the intended pixel dimension of the pattern
    as a 2-tuple to the constructor.

    Children should override the array_ property,
    which gives the array representation of the object,
    as well as __init__ or whatever.

    Parameters for the pattern should be attributes.
    
    Standard attributes:
        image -- a PIL representation of the array, in grayscale.
        png -- the PNG file representation of the image.
        encodeimage -- a method that basically saves the PIL
                        image encoded as a file (default PNG)
                        in memory.

    Display-server compatibility:
        setproxy -- set the server proxy to display
                    these images at
        senddata -- send the current image data to the 
                    display server

    """
    def __init__(self, dim=(1890,1020), server=None):
        """
        Set core parameters of the pattern.

        Keyword arguments:
            dim -- a 2-tuple representing the pixel dimension
                    of the pattern. Default is (1890, 1020)
                    (about the largest that can be displayed on
                    a 1920x1080 monitor, with menu bars etc (on XFCE)
            server -- a string containing the address of the 
                    display server where the pattern will
                    be displayed. Default: None.

        """
        self.dim = dim
        self._grayrange = (0,255)
        self.setproxy(server)

    def update(self):
        """call this whenever an attribute is changed. """
        if self.proxy is not None:
            self.senddata()

    @property
    def grayrange(self):
        return self._grayrange
    @grayrange.setter
    def grayrange(self, val):
        self._grayrange = val
        self.update()

    def setproxy(self, server_address):
        """
        Construct XML-RPC server proxy from a string containing
        the server address.

        >>> eg = pattern()
        >>> eg.proxy
        None
        >>> pattern.setproxy("http://localhost:8000")
        >>> eg.proxy
        <ServerProxy for localhost:8000>
        
        """
        if server_address is not None:
            self.proxy = xmlrpclib.ServerProxy(str(server_address))
        else:
            self.proxy = None

    @property
    def array_(self):
        """
        Return the array representation of the pattern.

        In this boilerplate, return a random pattern.
        When inheriting, overwrite this with
        something intelligent.

        """
        return numpy.random.random(self.dim)

    @property
    def image(self):
        """
        A PIL representation of the pattern in grayscale mode

        """
        grarray = numpy.int8(maprange(self.array_, self.grayrange))
        return Image.fromarray(grarray, 'L')

    def encodeimage(self, form='PNG'):
        """
        return a file-like image of the specified format
        note: does not support "with ... as ..." syntax

        """
        buf = StringIO.StringIO()
        self.image.save(buf, format=form)
        buf.seek(0)
        return buf

    # now properties shortcut to formats
    png = property(encodeimage)

    def senddata(self, throw=True):
        """
        Send image data to the display server.

        If throw = False is given, will fail silently
        if there is no display server.

        """
        if self.proxy is not None:
            data = xmlrpclib.Binary(self.png.read())
            try:
                self.proxy.setImageData(data)
            except xmlrpclib.ProtocolError:
                print 'error talking to display server, retrying once'
                self.proxy.setImageData(data)
        elif throw:
            raise InstrumentError("No display server defined")

class deflector(pattern):
    """
    A grating, which can be rotated to deflect in a desired direction.
    
    pass as keyword argument when instantiating: 
        dim --  the dimension of the pattern 

    Parameters are attributes:
        kind -- the type of grating: 'Sawtooth' etc. all types
                are listed in grating.options .
        spacing -- grating spacing
        deg -- orientation of the grating, in degrees.
        th -- orientation of the grating, in radians.
        phase -- phase of the grating

    """
    def __init__(self, *args, **kwargs):
        super(deflector,self).__init__(*args, **kwargs)

        # grating parameters:
        self.kind = 'Sawtooth'
        self.spacing = 30
        self.deg = 0
        self.phase = 0.0

        # brightness controls:
        self.scalefactor = 1.0
        self.baseline = 0.0

    @property
    def th(self):
        """ orientation of the grating, in radians """
        return numpy.radians(self.deg)
    @th.setter
    def th(self,th):
        self.deg = numpy.degrees(th)

    @property
    def grid(self):
        x, y = numpy.arange(self.dim[1]), numpy.arange(self.dim[0])
        xax, yax = numpy.meshgrid(x, y)
        return xax*numpy.sin(self.th) + yax*numpy.cos(self.th)

    @property
    def array_(self):
        # make a grating instance:
        func = grating(self.spacing, self.kind)
        # using said instance, generate a pattern:
        array_ = func(self.grid,self.phase)
        # scale the output (amplitude-modulate)
        array_ = scale(array_,self.scalefactor,self.baseline)
        return array_

class pulseshaper(pattern):
    """
    Vertically-deflecting grating with
    horizontally-varied phase and amplitude profiles

    Adjust the pixel dimension of the pulse shaper
    by providing a 2-tuple to the constructor like:

    >>> ps = pulseshaper(dim = (1920, 1080))

    This returns an object representing your shaper.

    By default, this class will try to find a display server
    on the local host, port 8000. If using a different computer
    or port, specify in the constructor, like:

    >>> ps = pulseshaper(server = 'http://128.223.131.68:8000')

    Reference Attributes:
        x -- horizontal axis (pixel units)
        y -- vertical axis (pixel units)

    Parameter Attributes:
        phase -- array representing phase of grating (2pi units)
        amp -- array representing amplitude modulation
        deflect_up -- boolean. True deflects up, False deflects down
        grating -- a grating object, has its own attributes.

    """
    def __init__(self, *args, **kwargs):

        if 'server' not in kwargs.keys():
            # configure a server by default
            kwargs['server'] = 'http://localhost:8000'

        super(pulseshaper,self).__init__(*args, **kwargs)

        # grating function to use, default spacing 100 pixels
        self.grating = grating(100)

        # defaults: no amplitude or phase mod
        self._phase = self.x * 0.0
        self._amp = self.phase + 1.0

        # deflect down by default
        self.deflect_up = False

        # calibration dictionary to hold pixel -> wl mapping.
        # keys are pixel numbers, values are measured wavelengths
        self.cal = calibration()

        # always call this
        self.update()

    # x and y axes of the pulse shaper, pixel units.
    @property
    def x(self): return numpy.arange(self.dim[0])
    @property
    def y(self): return numpy.arange(self.dim[1])

    # x axis, wavelength units.
    @property
    def wl(self): return self.cal(self.x)

    # these are a bunch of settable attributes
    @property
    def phase(self):
        return self._phase
    @phase.setter
    def phase(self, val):
        self._phase = val
        self.update()
    @property
    def amp(self):
        return self._amp
    @amp.setter
    def amp(self, val):
        self._amp = val
        self.update()

    @property
    def array_(self):
        gd = -1 if self.deflect_up else 1
        # the following works due to some crazy fucked up shit I wrote
        # in 2010 defining the "grating" class above
        # i must have been smoking crack
        return self.grating(gd * self.y, self.phase) * self.amp

    def blink(self, interval = 1.0):
        """ blink the grating on and off (for alignment)"""
        orig = self.amp
        while True:
            try:
                self.amp = 0
                sleep(interval / 2.)
                self.amp = orig
                sleep(interval / 2.)
            except KeyboardInterrupt:
                self.amp = orig
                break

from pylab import imshow
def show(*args, **kwargs):
    """
    imshow alternative that makes slm-specific tweaks.

    That is, it makes gray colormaps the default
    and turns off the axis labels.

    """
    if 'cmap' not in kwargs:
        kwargs['cmap'] = 'gray'
    ax = imshow(*args, **kwargs)
    ax.axes.xaxis.set_visible(False)
    ax.axes.yaxis.set_visible(False)
    return ax


if __name__ == "__main__":
    eg = pulseshaper()
