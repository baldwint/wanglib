#!/usr/bin/env python
"""
Utilities for computers using linux-gpib.

linux-gpib (http://linux-gpib.sourceforge.net/) is an open-source driver
for various GPIB cards. It includes two python modules:
    
    - the low-level `gpib` module
    - an object-oriented `Gpib` module.

The Gpib module defines a `Gpib` class representing individual
instruments. This module modifies that class to make it behave a little
more like PyVISA's `instrument` class, for better compatibility with the
rest of wanglib.

This will only work if your linux-gpib installation has been patched
with the following enhancement:

http://sourceforge.net/tracker/?func=detail&aid=3437534&group_id=42378&atid=432942

This should apply to any linux-gpib released since January 2012.

"""

import Gpib as Gpib_mod

class Gpib(Gpib_mod.Gpib):
    """
    Extension of the linux-gpib Gpib class to act more like a PyVISA
    instrument object.
    
    """

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
