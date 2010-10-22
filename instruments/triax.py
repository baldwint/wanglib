# a library to talk to the Triax spectrometer
# which runs on address 1 of the GPIB network
#
# tkb

import visa
import time


class triax(object):
    def __init__(self,addr='GPIB::1'):
        self.bus = visa.instrument(addr)
        # extension: verify that the instrument
        # is at the given address

    busyCodes = {"q": True,
                 "z": False }

    def is_busy(self):
        """ ask the Triax if its motors are busy """
        response = self.bus.ask("E")
        return self.busyCodes[response[1:]]

    busy = property(is_busy)

    def check_if_busy(self):
        if self.busy:
            raise Exception('Triax motors are busy')

    def get_wavelength(self):
        """query the current wavelength"""
        response = self.bus.ask("Z62,1")
        return float(response[1:])

    def set_wavelength(self,wavelength):
        """move to a new wavelength"""
        self.check_if_busy()
        command = "Z61,1,"+str(wavelength)
        response = self.bus.ask(command)
        # even though this is a write-only command,
        # triax still returns 'o' for okay

    wavelength = property(get_wavelength,set_wavelength)


if __name__ == "__main__":
    from sys import argv
    spec = triax()
    spec.wavelength = argv[1]

    while spec.wavelength <= 815:    
        spec.wavelength = spec.wavelength + 1
        while spec.busy:
            print spec.wavelength
            time.sleep(0.1)
        print "made it to %.4f" % spec.wavelength    
    print "all done!"
    print spec.wavelength
