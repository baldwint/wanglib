#
# This file is a placeholder which makes Python
# recognize this folder as an importable package.
#
# tkb

"""
Class-based interfaces to various scientific instruments.

These interfaces are designed to complement the low-level instrument
talking already provided by PySerial_ (for RS232) and PyVISA_
(for GPIB). Each instrument object defined here wraps a
:class:`serial.Serial` or :class:`visa.instrument` instance and uses
its ``write``/``read``/``ask`` methods to accomplish common commands
and readings specific to that instrument.

.. _PySerial: http://pyserial.sourceforge.net/
.. _PyVISA: http://pyvisa.sourceforge.net/

Example usage
+++++++++++++

Here's an example. We want to talk to an Agilent model 8648 RF signal
generator using GPIB. We have PyVISA installed, and that makes GPIB
talking a snap:

>>> from visa import instrument
>>> agilent = instrument("GPIB::18")
>>> agilent.ask("FREQ:CW?")
'200000000'

Three lines of code isn't bad, but it's cumbersome to write raw
commands to the instrument all the time. Plus, the returned value is a
string, not a number, and we'll have to convert it.

Fortunately, wanglib defines a class that handles all these commands
for us.

>>> from wanglib.instruments.signal_generators import ag8648
>>> rf = ag8648(agilent)
>>> rf.freq
200.

What happened here? Well, the ag8648 class we imported from wanglib
has 'wrapped' the agilent object we made before, and returned an
object representing our signal generator. This object has a variable
attached to it (an 'attribute') representing the frequency. Whenever
we access this attribute, the object performs the GPIB query behind
the scenes and converts the instrument response to a number in MHz.

We can also change the attribute:

>>> rf.freq = 110
>>> rf.freq
110.

Again, all queries and commands are being handled behind the scenes.
This makes your scripts much more readable, and is a especially useful
for interactive use. If all of your instruments are supported by
wanglib, you can feasibly run your whole experiment from a live python
interpreter.

For a list of all you can do with this rf object, do

>>> dir(rf)

And, as always in Python, use the help() function for information on
any object, attribute, or method.

>>> help(rf)
>>> help(rf.freq)
>>> help(rf.blink)

If the ag8648 class doesn't have an attribute or method for a given
instrument function, you can still send raw GPIB queries by accessing
the original PyVISA object as a sub-object of the ag8648 instance.

>>> rf.bus.ask("FREQ:CW?")
'110000000'

In this example, we wrapped a PyVISA instrument, but that's not required.
The low-level instrument we started with can be anything that has similar
read(), write(), and ask() methods:

    :PyVISA:        visa.instrument
    :linux-gpib:    wanglib.linux_gpib.Gpib
    :prologix:      wanglib.prologix.instrument

It's also easy to add functionality to the class. The help() function
tells you where to find the source file for any object on your
computer.

"""

from spex750m import spex750m, triax320
from lockins import egg5110, srs830
from signal_generators import ag8648

