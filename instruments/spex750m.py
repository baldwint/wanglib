from time import sleep
from wanglib.util import *


class spex750m(object):
    """A class encapsulating communication with the SPEX 750M
    spectrometer. Instantiate by passing the current wavelength
    of the spectrometer as read from the window, like so:

    spex750m(800)

    where 800 is measured in nm. This assumes the instrument is
    plugged into the first serial port. To use a different serial port,
    just pass it as the optional second parameter. For example, the
    following should be equivalent:

    spex750m(800,addr=1)
    spex750m(800,addr="COM2")

    Control the 750M using the provided methods. This example performs
    a wavelength scan:

    beast = spex750m(800)
    beast.set_wavelength(750)
    for i in range(200):
        beast.rel_move(0.5)
        while beast.is_busy():
            sleep(0.1)
        result = measure_something()
        print beast.get_wavelength(), result


    """

    
    def __init__(self, calibration, addr=0):

        self.bus_timeout = 10
        self.bus = Serial(addr, timeout=self.bus_timeout, baudrate=19200)

        try:
            self.init_hardware()    # try to initialize hardware.
        except InstrumentError:
            self.reboot()           # in case of trouble, reboot
            self.init_hardware()    # and try again.

        self.calibrate(calibration)

    def __repr__(self):
        return "Spex 750M"

    def boot_status_check(self):
        """Check the boot status of the controller.
        * : Just Autobauded
        F : Just Flashed
        B : Boot Acknowledged
        """
        self.bus.flush()
        resp = self.bus.ask(' ')
        if len(resp) == 0:
            raise InstrumentError("750M did not give a boot status")
        elif resp[0] in ("*", "F", "B"):
            return resp[0]
        else:
            raise InstrumentError("Unknown 750M boot status: %s" % resp)

    def reboot(self):
        """Reboot the controller if it's not responding
        """
        return self.bus.ask("\xDE")

    def hi_iq(self):
        """Send the HI IQ character to the controller.
        (Duplicates functionality of F7-247.vi.)
        Returns True if it's ok to flash the controller
        afterward.
        """
        self.bus.flush()
        resp = self.bus.ask("\xF7")
        if resp[0] == "=":
            return True
        else:
            raise InstrumentError("750M HI IQ command failed")

    def flash(self):
        """Flash the controller by sending the O2000<null>
        string to it.
        """
        return self.bus.ask("O2000\x00")

    def init_hardware(self):
        """Initialize 750M hardware. I don't know why this
        works, I just copied Yan's LabView routine.
        """
        status = self.boot_status_check()
        if status == "*":
            self.hi_iq()
            self.flash()
        status = self.boot_status_check()
        if status == "F":
            return True
        else:
            raise InstrumentError("750M hardware init failed.")

    def calibrate(self, wl_value):
        """Read the current wavelength from the window
        and pass it to this method (units of nm) to recalibrate
        the 750M.
        """
        cmd = "G0,%d\r" % (wl_value * 4000)
        self.bus.write(cmd)
        self.wavelength = wl_value # update internal wl tally

    busyCodes = {"q": True,
                 "z": False }

    def is_busy(self):
        """Check if the motors are busy """
        resp = self.bus.ask("E")
        return self.busyCodes[resp[1]]

    def rel_move(self, distance_to_move):
        """Move the grating by the given
        number of nanometers."""
        cmd = "F0,%d\r" % (distance_to_move * 4000)
        self.bus.write(cmd)
        resp = self.bus.read() # read one byte
        if resp != 'o':
            raise InstrumentError("750M move failed: %s" % resp)
        else:   # update internal wl tally
            self.wavelength += distance_to_move

    def get_wavelength(self):
        """Query the current wavelength """
        resp = self.bus.ask("HO\r").rstrip()
        wl = int(resp.lstrip('o')) / 4000.0
        self.wavelength = wl # update internal wl tally
        return wl

    def set_wavelength(self, wl):
        """Move to the wavelength value specified.
        contingent on proper calibration, of course.
        """
        distance_to_move = wl - self.get_wavelength()
        self.rel_move(distance_to_move)
        
