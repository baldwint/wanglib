"""miscellaneous experimental routines """

from time import sleep

def scan_gen(wls, spec, lockin, avgs=1, wait_factor=1.75):
    """
    Generator for a scanned spectrum.

    Arguments:
        wls -- list or numpy array containing
                the spectral values to scan over.
        spec -- a spectrometer instance. 
        lockin -- a lockin instance. 

    Keyword Arguments:
        avgs -- the number of data points to average on 
                each spectral value.
        wait_factor --  how many multiples of the lockin's
                        time constant to wait after each move

    """
#    if lockin is None:
#        lockin = egg5110()
#    if spec is None:
#        spec = triax()

    timeconst, unit = lockin.timeconst
    if unit == "ms":
        timeconst /= 1000.
    elif unit == "s":
        pass
    else:
        raise Exception( "Unknown time unit: %s" % unit)
    for i in range(len(wls)):
        spec.wl = wls[i]
        tally = 0.
        for j in range(avgs):
            sleep(timeconst * wait_factor)
            tally += lockin.r[0] # discard unit
        yield tally / avgs


