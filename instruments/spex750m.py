from time import sleep
from wanglib.util import Serial, InstrumentError


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

        self.bus = Serial(addr, timeout=10, baudrate=19200)

        try:
            self.init_hardware()    # try to initialize hardware.
        except InstrumentError as err:
            print "%s, rebooting once..." % err
            self.reboot()           # in case of trouble, reboot
            self.init_hardware()    # and try again.

        self.calibrate(calibration)

    def __repr__(self):
        return "Spex 750M"

    def boot_status_check(self):
        """Check the boot status of the controller.
        * : Just Autobauded
        B : Boot Acknowledged
        F : Just Flashed
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
        """Reboot the controller if it's not responding"""
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
            self.hi_iq()    # * -> B
            self.flash()    # B -> F
        status = self.boot_status_check()
        if status == "F":
            return True
        else:
            raise InstrumentError("750M hardware init failed.")

    def wait_for_ok(self):
        """sometimes the controller will wait a bit
        following a command before issuing a status byte.
        'o' means ok. This method waits for this byte
        indefinitely.
        """
        while self.bus.inWaiting() == 0: 
            # as long as the buffer is empty, hang out
            sleep(0.050)
        # read the status byte when it arrives
        resp = self.bus.read() 
        if resp != 'o':
            raise InstrumentError("750M operation failed: %s" % resp)

    def calibrate(self, wl_value):
        """Read the current wavelength from the window
        and pass it to this method (units of nm) to recalibrate
        the 750M.
        """
        self.bus.flush()
        cmd = "G0,%d\r" % (wl_value * 4000)
        self.bus.write(cmd)
        self.wait_for_ok()

    busyCodes = {"q": True,
                 "z": False }

    def is_busy(self):
        """Check if the motors are busy """
        resp = self.bus.ask("E")
        return self.busyCodes[resp[1]]

    def rel_move(self, distance_to_move):
        """Move the grating by the given
        number of nanometers."""
        self.bus.flush()
        cmd = "F0,%d\r" % (distance_to_move * 4000)
        self.bus.write(cmd)
        self.wait_for_ok()
        while self.is_busy():
            # wait for the motors to rest 
            sleep(0.050)

    def get_wavelength(self):
        """Query the current wavelength """
        self.bus.flush()
        self.bus.write("HO\r")
        resp = self.bus.read(9).rstrip()
        wl = int(resp.lstrip('o')) / 4000.0
        return wl

    def set_wavelength(self, wl):
        """Move to the wavelength value specified.
        contingent on proper calibration, of course.
        """
        distance_to_move = wl - self.get_wavelength()
        self.rel_move(distance_to_move)

    wavelength = property(get_wavelength, set_wavelength)
    wl = wavelength
        
