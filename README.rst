wanglib: Experimental control utilities for the Wang Lab
========================================================

`wanglib` is a module of experimental-control tools for use in the Wang
Lab. Contact its maintainer, Thomas Baldwin, if you have questions about
this library.

Documentation
-------------

Documentation is hosted at http://wanglib.readthedocs.org.

Installation
------------

First, clone this repository:

    $ hg clone https://bitbucket.org/tkb/wanglib

To install, run the setup script:

    $ cd wanglib
    $ python setup.py install

If you go this route, you may want to use the `--home` or `--user`
install options to prevent version conflicts with other users of the
machine.

Alternatively, you could just symlink the `wanglib` directory you made
into a place on your `sys.path`, like the `site_packages` directory.
This is a better option if you want to help development of wanglib.



