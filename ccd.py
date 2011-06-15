#!/usr/bin/env python

"""
Client routines for use with the CCD-2000 camera.
(generally attached to the Spex 750M spectrometer).

To configure the CCD server, refer to README file
on the desktop of the CCD controller computer.

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
    (read from the window).

    This info is needed because the labview program calculates
    wavelength values (from dispersion calibration info) on the
    server-side. Tye Hetherington wrote that sub-routine.

    This client implements no control whatsoever of the 
    SPEX 750m spectrometer to which the CCD is attached.
    For proper wavelength and dispersion info, you'll need to
    keep the client informed.

    Whenever you move the spectrometer, set center_wl
    attribute to match:

    >>> ccd.center_wl = 750

    To get a spectrum, use the get_spectrum method.

    """
    def __init__(self, center_wl, host = "128.223.131.31", port = 3663):
        self.sock = s.socket(s.AF_INET,s.SOCK_STREAM)
        self.sock.connect((host,port))
        self.center_wl = center_wl

    def get_spectrum(self):

        self.sock.send('Q')
        self.sock.send(str(100 * self.center_wl))

        sleep(1)

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
    from sys import argv
    p.ion()
    p.hold(False)
    while True:
        clnt = labview_client(argv[1])
        wl,ccd = clnt.get_spectrum()
        line, = p.plot(wl,ccd.sum(axis=0))
        p.draw()

