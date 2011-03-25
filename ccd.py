import socket as s
import numpy as n
from time import sleep


class ccd_client(object):

    def __init__(self, host = "128.223.131.31", port = 3663, center_wl = 700):
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
    import pylab as p
    p.ion()
    p.hold(False)
    while True:
        clnt = ccd_client()
        clnt.center_wl = 600
        wl,ccd = clnt.get_spectrum()
        line, = p.plot(wl,ccd.sum(axis=0))
        p.draw()

