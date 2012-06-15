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

The core contains these modules:
    
* :mod:`util` -- implements a custom serial interface
            provides templates for fitting, calibration, and scan automation.
* :mod:`prologix` -- drivers for prologix GPIB controllers (USB and Ethernet)
* :mod:`linux_gpib` -- provides compatibility with systems using linux_gpib
* :mod:`ccd` --  a client for the CCD on the spex750m
* :mod:`grating` -- generates phase gratings for the SLM

more functionality in two sub-packages:

* :mod:`instruments` -- libraries for individual instruments in the lab
* :mod:`pylab_extensions` -- misc. extensions to the pylab plotting interface

This is a code library - not a set of specific experimental routines.  
The script you write to control your experiment will call functions in
wanglib, but should only be a part of wanglib if it is modular, reusable, and
adds functionality not already here.

I welcome contributions and modifications. 

tkb

"""
