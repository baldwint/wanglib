wanglib: Experimental control utilities for the Wang Lab
========================================================

`wanglib` is a module of experimental-control tools for use in the Wang
Lab. Contact its maintainer, Thomas Baldwin, if you have questions about
this library.

Documentation
-------------

Documentation is hosted at http://wanglib.readthedocs.org.

Dependencies
------------

Wanglib is designed to run on a typical scientific Python stack: Python
2.7 with Numpy_, Scipy_, and Matplotlib_. Interactive use is best
done through IPython_.

.. _Numpy: http://numpy.scipy.org/
.. _Scipy: http://scipy.org/
.. _Matplotlib: http://matplotlib.sourceforge.net/
.. _IPython: http://ipython.org/

For talking to RS-232 instruments, PySerial_ is required. For GPIB
instruments, you will need either PyVISA_ or linux-gpib_ (unless you're
using a prologix GPIB controller - wanglib provides its own driver for
these).

.. _PySerial: http://pyserial.sourceforge.net/
.. _PyVISA: http://pyvisa.sourceforge.net/ 
.. _linux-gpib: http://linux-gpib.sourceforge.net/ 

To install wanglib and keep it up to date, it is best to have the
Mercurial_ DVCS and the pip_ installer.

.. _Mercurial: http://mercurial.selenic.com/
.. _pip: http://www.pip-installer.org/


Installation
------------

There are no versioned releases of `wanglib` - only a development
version that changes all the time. Install this with `pip`::

    $ pip install --user -e hg+https://bitbucket.org/tkb/wanglib#egg=wanglib

The `--user` flag is a good idea to prevent version conflicts with other
users on the same machine. 

This creates an editable clone of the repository in your home directory at
`$HOME/src/wanglib`. To update to the latest version, change to this
directory and do::

    $ hg pull
    $ hg update

You can make changes to wanglib by editing the files in this folder.
By making changes, you are creating a branch. If you wish to contribute
your changes back to me, create a repo for your branch on Bitbucket, and
open a pull request.

Package Contents
----------------

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


