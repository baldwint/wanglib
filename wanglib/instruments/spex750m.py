"""
This module contains utilities for controlling Jobin-Yvon
"SPEX" series monochromators over RS232 serial.

Classes defined:
 * :class:`spex750m` -- implements standard Jobin-Yvon serial commands for simple spectrometers like the 750M.
 * :class:`triax320` -- extends the :mod:`spex750m` class with the more sophisticated commands used by the triax.

Tutorial
++++++++

both :class:`spex750m` and :class:`triax320` behave roughly the same
way. In this tutorial we use the 750M for example. Instantiate like:

>>> beast = spex750m()

This opens a connection with the larger of the two spectrometers (the
SPEX 750M.)

Classes are configured to look for the spectrometer at the serial
port where they are normally plugged in. To specify a different serial
port, just pass it as an optional parameter when instantiating.
For example, the following should be equivalent:

>>> beast = spex750m(addr=1)
>>> beast = spex750m(addr="COM2")   # on windows
>>> beast = spex750m(addr="/dev/ttyS1")   # on linux

It's a good idea to check that the spectrometer has been
calibrated. This is unneccessary for the Triax, but on the 750M, we
should check it. Having instantiated it as ``beast``, run

>>> beast.wl
790.

This queries the current wavelength in nm, which ought to match
the value displayed in the window. If it doesn't, run

>>> beast.calibrate(800)

This will re-set the calibration to 800nm:

>>> beast.wl
800.

You can control the spectrometer using the methods documented below.
For example, this performs a wavelength scan:

>>> beast = spex750m('/dev/ttyUSB0')
>>> beast.calibrate(800)
>>> beast.set_wavelength(750)
>>> for i in range(200):
...    beast.rel_move(0.5)
...    while beast.is_busy():
...        sleep(0.1)
...    result = measure_something()
...    print beast.get_wavelength(), result

API documentation
+++++++++++++++++

"""

from time import sleep
from wanglib.util import Serial, InstrumentError

class spex750m(object):
    """
    A class implementing standard Jobin-Yvon serial commands
    for simple spectrometers like the SPEX 750M.

    By default, this class is configured to look for the 750M
    plugged into ``/dev/ttyUSB0`` (the first port on the USB-serial
    adapter, when run under linux).

    """

    def __init__(self, addr=None):
        """
        Connect to the spectrometer and initialize its hardware.

        :param addr: the serial interface where the
                     spectrometer is found.
                     Default: ``/dev/ttyUSB0``

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

    # 750M specific data
    _steps_per_nm = 4000
    _default_location = '/dev/ttyUSB0'

    def __str__(self):
        return 'Spex 750M'

    def boot_status_check(self):
        """Check the boot status of the controller.

        - \* : Just Autobauded
        - B : Boot Acknowledged
        - F : Just Flashed
        """
        self.bus.readall()
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

    def _hi_iq(self):
        """Send the HI IQ character to the controller.
        (Duplicates functionality of F7-247.vi.)
        Returns True if it's ok to flash the controller
        afterward.
        """
        self.bus.readall()
        resp = self.bus.ask("\xF7")
        if resp[0] == "=":
            return True
        else:
            raise InstrumentError("750M HI IQ command failed")

    def _flash(self):
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
            self._hi_iq()    # * -> B
            self._flash()    # B -> F
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
        self.bus.readall()
        cmd = "G0,%d\r" % (wl_value * self._steps_per_nm)
        self.bus.write(cmd)
        self.wait_for_ok()

    _busyCodes = {"q": True,
                 "z": False }

    def is_busy(self):
        """Check if the motors are busy. """
        self.bus.write("E")
        self.wait_for_ok()
        resp = self.bus.readall()
        return self._busyCodes[resp]

    def rel_move(self, distance_to_move):
        """Move the grating by the given
        number of nanometers."""
        self.bus.readall()
        cmd = "F0,%d\r" % (distance_to_move * self._steps_per_nm)
        self.bus.write(cmd)
        self.wait_for_ok()
        while self.is_busy():
            # wait for the motors to rest
            sleep(0.050)

    def get_wavelength(self):
        """Query the current wavelength """
        self.bus.readall()
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
        if wl < 0 or wl > 1500:
            raise InstrumentError("Out of Range")
        distance_to_move = wl - self.get_wavelength()
        self.rel_move(distance_to_move)

    wavelength = property(get_wavelength, set_wavelength)

    # abbreviate 'wavelength' to 'wl'
    get_wl = get_wavelength
    set_wl = set_wavelength
    wl = wavelength


# the triax series monochromators add some features
# define a new class which inherits from spex750m

class triax320(spex750m):
    """
    A class implementing Jobin-Yvon serial commands
    for more advanced spectrometers like the TRIAX 320.

    Instantiate as you would a spex750m. If you don't
    specify a serial port, this class will assume the
    spectrometer is attached to ``/dev/ttyUSB1``, the second
    port on the USB-serial converter.

    Unlike the 750M, the Triax
        - has motorized entrance and exit slits
        - zeroes its grating on power-up.

    To perform a motor init on the triax, call :meth:`motor_init`.


    """

    # different default location.
    # hopefully the __init__ function will pick this up.
    _default_location = '/dev/ttyUSB1'

    def __str__(self):
        return 'Triax 320'

    # the Triax series isn't designed for the steps-per-nm
    # system (although these commands work).
    # instead, it works in actual wavelength values.
    # the following functions shadow the ones defined
    # above, to prefer the extended 'Z' functions.

    def calibrate(self, wl):
        """Set wavelength of Triax without moving motor """
        self.bus.readall()
        self.bus.write("Z60,1,"+str(wl)+"\r")
        self.wait_for_ok()

    def get_wavelength(self):
        """Query the current wavelength """
        self.bus.readall()
        self.bus.write("Z62,1\r")
        self.wait_for_ok(expected_bytes=8)
        resp = self.bus.readall()
        return float(resp)

    def set_wavelength(self, wl):
        """Move to a new wavelength """
        self.bus.readall()
        self.bus.write("Z61,1,"+str(wl)+"\r")
        self.wait_for_ok()
        while self.is_busy():
            # wait for the motors to rest
            sleep(0.050)

    wavelength = property(get_wavelength, set_wavelength)

    # abbreviate 'wavelength' to 'wl'
    get_wl = get_wavelength
    set_wl = set_wavelength
    wl = wavelength

    # general utilities for motorized slits.

    def _move_slit_relative(self, slit_number, amount):
        """
        Move a slit motor relatively.

        For example, the following moves slit 0
        by 5 steps:

        >>> spec._move_slit_relative(0,5)

        """
        self.bus.readall()
        self.bus.write("k0,%d,%d\r" % (slit_number, amount))
        self.wait_for_ok()
        while self.is_busy():
            # wait for the motors to rest
            sleep(0.050)

    def _get_slit_position(self, slit_number):
        """
        Read the current absolute position of a slit.

        For example, read the absolute position of slit 0:

        >>> spec._get_slit_position(0)
        5

        """
        self.bus.readall()
        self.bus.write("j0,%d\r" % slit_number)
        self.wait_for_ok()
        resp = self.bus.readall()
        return float(resp)

    def _set_slit_position(self, slit_number, position):
        """
        Move a slit motor to a given absolute position.

        Zeroes things out ahead of time for backslash correction.

        """
        start_position = self._get_slit_position(slit_number)
        self._move_slit_relative(slit_number, 0 - start_position)
        self._move_slit_relative(slit_number, position)

    # parameters specific to the triax 320.
    # entrance slit: 0
    # exit slit: 2

    entr_slit = property(
        lambda self: self._get_slit_position(0),
        lambda self, val: self._set_slit_position(0, val)
    )
    """
    The entrance slit setting.

    >>> beast.entr_slit
    20.
    >>> beast.entr_slit = 30
    >>> beast.entr_slit
    30.

    """

    exit_slit = property(
        lambda self: self._get_slit_position(2),
        lambda self, val: self._set_slit_position(2, val)
    )
    """
    The exit slit setting.

    >>> beast.exit_slit
    20.
    >>> beast.exit_slit = 30
    >>> beast.exit_slit
    30.

    """

    @property
    def slits(self):
        """
        Return the entrance and exit slit settings together.

        >>> beast.slits
        (30., 30.)

        Indicates that both slits are at 30. They can also be set
        together:

        >>> beast.slits = (20,30)
        >>> beast.slits
        (20., 30.)

        sets the entrance slit to 20. There is a shortcut for setting
        the slits to equal values:

        >>> beast.slits = 20
        >>> beast.slits
        (20., 20.)

        """
        return (self.entr_slit, self.exit_slit)

    @slits.setter
    def slits(self, newvals):
        if hasattr(newvals, '__iter__'):
            # if a list or a tuple is given,
            # adjust entrance and exit slits correspondingly
            self.entr_slit, self.exit_slit = newvals
        else:
            # if the given value is just one number,
            # set both slits to that value
            self.entr_slit, self.exit_slit = (newvals, newvals)

    # does the triax 320 autocalibrate?
    # whatever, here's the code for that.

    def motor_init(self):
        """
        Move all motors to their power-up (autocal) positions.

        This zeroes the wavelength grating and
        both entrance and exit slits.
        Don't forget to reopen the slits after calling this.

        """
        self.bus.write("A")
        self.wait_for_ok()
        # at this point we could call "i0,0,0\r"
        # and "i0,2,0" to zero the slits
        # (yan does that with labview)
        # but I think this is implied by "A"

