"""
This module contains utilities for controlling Jobin-Yvon
"SPEX" series monochromators over RS232 serial.

Classes defined:
    spex750m -- implements standard Jobin-Yvon serial commands
                for simple spectrometers like the 750M.
    triax --    extends the spex750m class with the more
                sophisticated commands used by the triax.

"""

from time import sleep
from wanglib.util import Serial, InstrumentError

class spex750m(object):
    """
    A class implementing standard Jobin-Yvon serial commands
    for simple spectrometers like the SPEX 750M.
    
    Instantiate like:

    >>> beast = spex750m()

    To specify the serial port where the spex is plugged in,
    just pass it as an optional parameter when instantiating.
    For example, the following should be equivalent:

    >>> beast = spex750m(addr=1)
    >>> beast = spex750m(addr="COM2")   # on windows
    >>> beast = spex750m(addr="/dev/ttyS1")   # on linux

    By default, this class is configured to look for the 750M 
    plugged into /dev/ttyUSB0 (the first port on the USB-serial
    adapter, when run under linux). 

    To calibrate the spectrometer in the same step, pass
    the current wavelength of the spectrometer as read from
    the window, like so (either of these works):

    >>> beast = spex750m(calibration = 800)
    >>> beast = spex750m(800)

    where 800 is measured in nm. You can also calibrate later, like

    >>> beast = spex750m()
    >>> # ... do things ...
    >>> beast.calibrate(800)

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
    
    def __init__(self, calibration=None, addr=None):
        """
        Initialize (and optionally calibrate) the spectrometer.

        Keyword arguments:
            addr -- the serial interface where the 
                    spectrometer is found. 
                    Default: /dev/ttyUSB0
            calibration -- the current wavelength value
                            of the spectrometer.

        """

        if addr is None:
            addr = self._default_location 
        self.bus = Serial(addr, timeout=10, baudrate=19200)

        try:
            self.init_hardware()    # try to initialize hardware.
        except InstrumentError as err:
            print "%s, rebooting once..." % err
            self.reboot()           # in case of trouble, reboot
            self.init_hardware()    # and try again.

        if calibration is not None:
            self.calibrate(calibration)

    # 750M specific data
    _steps_per_nm = 4000
    _default_location = '/dev/ttyUSB0'

    def boot_status_check(self):
        """Check the boot status of the controller.
        * : Just Autobauded
        B : Boot Acknowledged
        F : Just Flashed
        """
        self.bus.flush()
        resp = self.bus.ask(' ')    # send autobaud character
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

    def wait_for_ok(self, expected_bytes=1):
        """
        Wait indefinitely for the 'o' status byte.

        This function waits until a certain number of bytes
        (usually just one) are present on the bus. When
        that data arrives, the first bye is read
        and checked to make sure it's the "okay" status.

        """
        while self.bus.inWaiting() < expected_bytes: 
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
        cmd = "G0,%d\r" % (wl_value * self._steps_per_nm)
        self.bus.write(cmd)
        self.wait_for_ok()

    busyCodes = {"q": True,
                 "z": False }

    def is_busy(self):
        """Check if the motors are busy. """
        self.bus.write("E")
        self.wait_for_ok()
        resp = self.bus.readall()
        return self.busyCodes[resp]

    def rel_move(self, distance_to_move):
        """Move the grating by the given
        number of nanometers."""
        self.bus.flush()
        cmd = "F0,%d\r" % (distance_to_move * self._steps_per_nm)
        self.bus.write(cmd)
        self.wait_for_ok()
        while self.is_busy():
            # wait for the motors to rest 
            sleep(0.050)

    def get_wavelength(self):
        """Query the current wavelength """
        self.bus.flush()
        self.bus.write("HO\r")
        self.wait_for_ok()
        resp = self.bus.readall()
        # convert to wavelength units
        wl = int(resp) / float(self._steps_per_nm) 
        return wl

    def set_wavelength(self, wl):
        """Move to the wavelength value specified.
        contingent on proper calibration, of course.
        """
        distance_to_move = wl - self.get_wavelength()
        self.rel_move(distance_to_move)

    wavelength = property(get_wavelength, set_wavelength)
    wl = wavelength

# the triax series monochromators add some features
# define a new class which inherits from spex750m

class triax320(spex750m):

    # different default location.
    # hopefully the __init__ function will pick this up.
    _default_location = '/dev/ttyUSB1'
    
    # the Triax series isn't designed for the steps-per-nm
    # system (although these commands work).
    # instead, it works in actual wavelength values.
    # the following functions shadow the ones defined
    # above, to prefer the extended 'Z' functions.

    def get_wavelength(self):
        """Query the current wavelength """
        self.bus.flush()
        self.bus.write("Z62,1\r")
        self.wait_for_ok(expected_bytes=8)
        resp = self.bus.readall()
        return float(resp)

    def set_wavelength(self, wl):
        """Move to a new wavelength """
        self.bus.flush()
        self.bus.write("Z61,1,"+str(wl)+"\r")
        self.wait_for_ok()
        while self.is_busy():
            # wait for the motors to rest 
            sleep(0.050)

    wavelength = property(get_wavelength, set_wavelength)
    wl = wavelength

    # general utilities for motorized slits.

    def move_slit_relative(self, slit_number, amount):
        """
        Move a slit motor relatively.

        For example, the following moves slit 0
        by 5 steps:

        >>> spec.move_slit_relative(0,5)

        """
        self.bus.flush()
        self.bus.write("k0,%d,%d\r" % (slit_number, amount))
        self.wait_for_ok()
        while self.is_busy():
            # wait for the motors to rest 
            sleep(0.050)

    def get_slit_position(self, slit_number):
        """
        Read the current absolute position of a slit.

        For example, read the absolute position of slit 0:
        
        >>> spec.get_slit_position(0)
        5

        """
        self.bus.flush()
        self.bus.write("j0,%d\r" % slit_number)
        self.wait_for_ok()
        resp = self.bus.readall()
        return float(resp)

    def set_slit_position(self, slit_number, position):
        """
        Move a slit motor to a given absolute position.

        Zeroes things out ahead of time for backslash correction.

        """
        start_position = self.get_slit_position(slit_number)
        self.move_slit_relative(slit_number, 0 - start_position)
        self.move_slit_relative(slit_number, position)

    # parameters specific to the triax 320.
    # entrance slit: 0
    # exit slit: 2

    entr_slit = property(
        lambda self: self.get_slit_position(0),
        lambda self, val: self.set_slit_position(0, val)
    )
    exit_slit = property(
        lambda self: self.get_slit_position(2),
        lambda self, val: self.set_slit_position(2, val)
    )

    # does the triax 320 autocalibrate?
    # whatever, here's the code for that.

    def motor_init(self):
        """
        Move all motors to their power-up (autocal) positions.

        """
        self.bus.write("A")
        self.wait_for_ok()
        # at this point we could call "i0,0,0\r"
        # and "i0,2,0" to zero the slits
        # (yan does that with labview)
        # but I think this is implied by "A"







        
