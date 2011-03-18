#!/usr/bin/env python

"""
Utilities for generating and displaying SLM phase masks.

Functions here support use of the Spatial Light Modulator
for use as a programmable grating, pulse shaper, etc.

"""

from numpy import *
import Image
import StringIO

def sinewave(arg):
    """
    oscillates between 0 and 1
    argument given in 2pi units

    """
    return 0.5 * (1 - sin(2 * pi * arg))

def sawtooth(arg):
    """
    gives values between 0 and 1
    argument given in 2pi units

    """
    return remainder(arg,1.0)

def zebra(arg):
    """
    switches between 0 and 1
    argument given in 2pi units

    """
    return around(remainder(arg,1.0))

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
            findarg = true_divide.outer
        else:
            findarg = true_divide
        arg = findarg(coordinate,self.spacing)

        # add in the shift
        if not self.variablePhase:
            addshift = add.outer
        else:
            addshift = add
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
    
    Provided by the boilerplate:
        image -- a PIL representation of the array, in grayscale.
        png -- the PNG file representation of the image.
        encodeimage -- a method that basically saves the PIL
                        image encoded as a file (default PNG)
                        in memory. This was used for the XML-RPC
                        thing once upon a time.

    """
    def __init__(self, dim=(1024,768)):
        """
        Set core parameters of the pattern,
        like the dimension, etc.

        """
        self.dim = dim
        self.grayrange = (0,255)

    @property
    def array_(self):
        """
        Return the array representation of the pattern.

        In this boilerplate, return a random pattern.
        When inheriting, overwrite this with
        something intelligent.

        """
        return random.random(self.dim)

    @property
    def image(self):
        """
        A PIL representation of the pattern in grayscale mode

        """
        grarray = int8(maprange(self.array_, self.grayrange))
        return Image.fromarray(grarray, 'L')

    @property
    def rgb(self):
        """
        A PIL representation of the pattern in RGB mode

        Useful for imshow() when you don't want it using colormaps.
        seems buggy? just use image, and then cmap='gray'.

        """
        img = self.image
        img.mode = 'RGB'
        return img

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
    def __init__(self,
                dim = (1000,1900),
                ):
        super(deflector,self).__init__(dim)

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
        return radians(self.deg)
    @th.setter
    def th(self,th):
        self.deg = degrees(th)

    @property
    def grid(self):
        x, y = arange(self.dim[1]), arange(self.dim[0])
        xax, yax = meshgrid(x, y)
        return xax*sin(self.th) + yax*cos(self.th)

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

    """
    def __init__(self, dim = (1024, 768)):
        super(pulseshaper,self).__init__(dim)

        # grating function to use, default spacing 100 pixels
        self.grating = grating(100)

        # defaults: no amplitude or phase mod
        self.phase = self.x * 0.0
        self.amp = self.phase + 1.0

    # x and y axes of the pulse shaper, pixel units.
    @property
    def x(self): return arange(self.dim[0])
    @property
    def y(self): return arange(self.dim[1])

    @property
    def array_(self):
        # this works due to some crazy fucked up shit I wrote
        # in 2010 defining the "grating" class above
        # i must have been smoking crack
        return self.grating(self.y, self.phase) * self.amp

from pylab import imshow
def show(*args, **kwargs):
    """
    imshow alternative that makes slm-specific tweaks.

    """
    if 'cmap' not in kwargs:
        kwargs['cmap'] = 'gray'
    ax = imshow(*args, **kwargs)
    ax.axes.xaxis.set_visible(False)
    ax.axes.yaxis.set_visible(False)
    return ax


if __name__ == "__main__":
    eg = pulseshaper()
