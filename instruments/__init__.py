#
# This file is a placeholder which makes Python
# recognize this folder as an importable package.
#
# tkb

from spex750m import spex750m
from lockins import egg5110

# Some instruments depend on PyVISA, which in turn
# relies on the NI VISA stack. This is unavailable
# on some systems, so only make these instruments
# available on those platforms.
try:
    import visa
except ImportError:
    pass
else:
    # these instruments depend on PyVisa.
    from triax import triax
    from signal_generators import ag8648
