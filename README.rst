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

There are no versioned releases of `wanglib` - only a development
version. Install this with `pip`::

    $ pip install --user -e hg+https://bitbucket.org/tkb/wanglib#egg=wanglib

The `--user` flag is a good idea to prevent conflicts with other users
on the same machine. 

This creates an editable clone of the repository in your home directory at
`$HOME/src/wanglib`. To update to the latest version, change to this
directory and do::

    $ hg pull

You can make changes to wanglib by editing the files in this folder.
By making changes, you are creating a branch. If you wish to contribute
your changes back to me, create a repo for your branch on Bitbucket, and
open a pull request.

