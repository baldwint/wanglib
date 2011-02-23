#
# This file is a placeholder which makes Python
# recognize this folder as an importable package.
#
# tkb

from spex750m import spex750m

# Some instruments depend on PyVISA, which in turn
# relies on the NI VISA stack. This is unavailable
# on some systems, so only make these instruments
# available on those platforms.
try:
    import visa
except ImportError:
    print "No VISA bindings found. GPIB unavailable."
else:
    from triax import triax
    from egg5110 import egg5110
    from agilent_signal_generators import ag8648
