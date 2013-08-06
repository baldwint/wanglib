#!/usr/bin/env python

from setuptools import setup

reqs = ['numpy', 'pyserial', 'matplotlib']
# you may also want (separate pip install):
#    - PIL (for old SLM stuff)
#    - scipy (for old fitting helpers, don't use these though)
#    - gpib (if you use linux, own a NI GPIB card, and feel adventurous)

setup(name='wanglib',
      version='dev',
      description='Instrument control utilities for the Wang lab',
      author='Thomas Baldwin',
      author_email='tbaldwin@uoregon.edu',
      install_requires=reqs,
      #url='http://no.url.yet',
      packages=['wanglib',
                'wanglib.instruments',
                'wanglib.pylab_extensions'],
     )

