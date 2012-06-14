#!/usr/bin/env python

from distutils.core import setup

setup(name='wanglib',
      version='dev',
      description='Instrument control utilities for the Wang lab',
      author='Thomas Baldwin',
      author_email='tbaldwin@uoregon.edu',
      #url='http://no.url.yet',
      packages=['wanglib',
                'wanglib.instruments',
                'wanglib.pylab_extensions'],
     )

