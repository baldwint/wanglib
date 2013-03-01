#!/usr/bin/env python

"""
Client routines for use with the CCD-2000 camera
(generally attached to the Spex 750M spectrometer).
These utilities talk to the CCD server LabView program 
running on the old computer over TCP/IP.

To configure the CCD server, refer to README file
on the desktop of the CCD controller computer.

Command-line invocation
+++++++++++++++++++++++

For a simple live display from the CCD, invoke
this module as a script::

    $ python -m wanglib.ccd 800

where 800 is the center wavelength of the grating
(as read from the window). You may need to specify
the IP address of the CCD server:: 

    $ python -m wanglib.ccd --ip 128.223.23.240 800

Client library
++++++++++++++

To integrate the CCD client into your own script,
use :class:`labview_client`.

"""

import socket as s
import numpy as n
from time import sleep

class labview_client(object):
    """
    TCP client for Tim's labview ccd server.

    Instantiate like so:

    >>> ccd = labview_client(700)

    where 700 is the current wavelength of the spectrometer
    in nanometers (read from the window).

    This info is needed because the labview program calculates
    wavelength values (from dispersion calibration info) on the
    server-side. Tye Hetherington wrote that sub-routine.

    This client implements no control whatsoever of the 
    SPEX 750m spectrometer to which the CCD is attached.
    For proper wavelength and dispersion info, you'll need to
    keep the client informed.

    Whenever you move the spectrometer, set ``center_wl``
    attribute to match:

    >>> ccd.center_wl = 750

    To get a spectrum, use :meth:`get_spectrum`.

    """
    def __init__(self, center_wl, host = None, port = 3663):
        if host is None:
            host = "128.223.23.240"
        self.sock = s.socket(s.AF_INET,s.SOCK_STREAM)
        self.sock.connect((host,port))
        self.center_wl = center_wl

    def get_spectrum(self):
        """
        Takes a shot on the CCD.

        Returns a 2-tuple ``(wl, ccd)``.

        ``wl``: a 1-D array of the horizontal (wavelength) axis.
        ``ccd``: a 2-D array of CCD counts.

        To collapse ``ccd`` into a 1D array matching ``wl``,
        sum over axis 0:

        >>> wl,ccd = clnt.get_spectrum()
        >>> line, = pylab.plot(wl,ccd.sum(axis=0))

        """

        self.sock.send('Q')
        self.sock.send(str(100 * self.center_wl))

#        sleep(1)

        datalen = int(self.sock.recv(7))
        data = ''

        while datalen > 0:
            # read data in chunks
            dt = self.sock.recv(datalen)
            data += dt
            datalen -= len(dt)

        data = data.split("\n")[:-1]
        for i in range(len(data)):
            data[i] = data[i].split("\t")

        data = n.array(data,dtype=float)

        wl = data[0]
        ccd = data[1:]

        return wl,ccd

        #self.sock.close()

if __name__ == "__main__":
    # for command line invocation, take the center wavelength
    # as first argument and put on a live display.
    import pylab as p
    from optparse import OptionParser

    from wanglib.util import gaussian
    class fake_ccd(object):
        """ dummy class for testing the gui """
        def __init__(self, center_wl):
            self.center_wl = center_wl

        def get_spectrum(self):
            x = p.arange(-10, 10, .1) + self.center_wl
            param = [0, 100, self.center_wl, 4]
            spice = n.random.randn(len(x))
            y = gaussian(param, x) + spice
            ccd = n.vstack((y,y))
            return x,ccd

    # parse command line options
    parser = OptionParser()
    parser.add_option('--ip', dest='ip', default=None,
                      help='IP address of CCD server')
    opts, args = parser.parse_args()

    # read center wl from command line
    center_wl = float(args[0])

    # connect to server
    clnt = labview_client(center_wl, host=opts.ip)
    #clnt = fake_ccd(center_wl)

    # make a plot
    p.ion()
    p.hold(False)
    wl,ccd = clnt.get_spectrum()
    line, = p.plot(wl,ccd.sum(axis=0))
    while True:
        # update it continuously
        wl,ccd = clnt.get_spectrum()
        line.set_ydata(ccd.sum(axis=0))
        p.draw()

