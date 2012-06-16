#
# This file is a placeholder which makes Python
# recognize this folder as an importable package.
#
# tkb

"""
Experimental control utilities for the Wang lab.

When writing a script to control your experiment (or working
interactively using the interpreter), use :mod:`wanglib` to make
instrument control and data gathering easy.

This is a code library - not a set of miscellaneous experimental routines.  
Functions included in :mod:`wanglib` should be generally useful somehow,
rather than being specific to any given experimental setup.

The core contains these modules:
    
* :mod:`wanglib.util` -- miscellaneous utilities
    - implements a custom serial interface
    - provides templates for fitting, calibration, and scan automation.
* :mod:`wanglib.prologix` -- drivers for prologix GPIB controllers (USB and Ethernet)
* :mod:`wanglib.linux_gpib` -- provides compatibility with systems using linux_gpib
* :mod:`wanglib.ccd` --  a client for the CCD on the spex750m
* :mod:`wanglib.grating` -- generates phase gratings for the SLM

more functionality in two sub-packages:

* :mod:`wanglib.instruments` -- libraries for individual instruments in the lab
* :mod:`wanglib.pylab_extensions` -- misc. extensions to the pylab plotting interface

"""
