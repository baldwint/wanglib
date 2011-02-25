# This is a library to talk to the EG&G Model 5110 lock-in
# which runs on address 12 of the GPIB network
#
# tkb

from wanglib.util import InstrumentError, Gpib

class egg5110(object):
    """ An EG&G model 5110 lock-in.

    Typically controlled over GPIB, address 12. If you're connecting
    differently, bass the bus object to the constructor.

    """
    def __init__(self,bus=None):

        if bus is not None:
            self.bus = bus
        else:
            self.bus = Gpib(0, 12)


        # verify lockin identity
        self.bus.write("ID")
        if self.bus.read() != '5110':    
            raise InstrumentError('5110 lockin not found')

    # sensitivity functions
    
    sensitivities = {0: (100,'nV'), \
                     1: (200,'nV'), \
                     2: (500,'nV'), \
                     3: (1,'uV'), \
                     4: (2,'uV'), \
                     5: (5,'uV'), \
                     6: (10,'uV'), \
                     7: (20,'uV'), \
                     8: (50,'uV'), \
                     9: (100,'uV'), \
                     10: (200,'uV'), \
                     11: (500,'uV'), \
                     12: (1,'mV'), \
                     13: (2,'mV'), \
                     14: (5,'mV'), \
                     15: (10,'mV'), \
                     16: (20,'mV'), \
                     17: (50,'mV'), \
                     18: (100,'mV'), \
                     19: (200,'mV'), \
                     20: (500,'mV'), \
                     21: (1,'V')}
    
    def getSensitivity(self):
        val = self.bus.ask("SEN")
        return self.sensitivities[int(val)]
    def setSensitivity(self,code):
        self.bus.write("SEN %d" % code)
    sensitivity = property(getSensitivity,setSensitivity)

    # time constant functions

    timeconsts = {0: (0,'MIN'), \
                  1: (1,'ms'), \
                  2: (3,'ms'), \
                  3: (10,'ms'), \
                  4: (30,'ms'), \
                  5: (100,'ms'), \
                  6: (300,'ms'), \
                  7: (1,'s'), \
                  8: (3,'s'), \
                  9: (10,'s'), \
                  10: (30,'s'), \
                  11: (100,'s'), \
                  12: (300,'s')}

    def getTimeconst(self):
        val = self.bus.ask("TC")
        return self.timeconsts[int(val)]
    def setTimeconst(self,code):
        self.bus.write("TC %d" % code)
    timeconst = property(getTimeconst,setTimeconst)

    # measurement functions

    def measure(self,command):
        # the 5110 lockin returns measurements
        # as ten-thousandths of full-scale
        sens,unit = self.sensitivity
        multiplier = float(sens) / 10000
        response = self.bus.ask(command)
        return int(response) * multiplier, unit

    def getX(self): return self.measure('X')
    x = property(getX)
    def getY(self): return self.measure('Y')
    y = property(getY)
    def getMagnitude(self): return self.measure('MAG')
    r = property(getMagnitude)

    def getPhase(self):
        # phase measurements come in millidegrees
        # so convert them to degrees
        multiplier = float(1) / 1000
        response = self.bus.ask('PHA')
        return int(response) * mulitplier, 'degrees'
    phase = property(getPhase)

    # adc function

    def getADC(self,n):
        # read one of the four ADC ports
        if n not in range(1,4):
            raise InstrumentError("Indicate ADC between 1 and 4")
        response = self.bus.ask("ADC %d" % n)
        return 0.001 * response, 'V'

    @property
    def lights(self):
        response = self.bus.ask("LTS")
        return bool(int(response))

    @lights.setter
    def lights(self, arg):
        cmd = "LTS %d" % bool(arg)
        self.bus.write(cmd)


    

    
if __name__ == "__main__":
    import sys,csv
    address = sys.argv[1]
    egg = egg5110("GPIB::%d" % int(address))
    for step in range(0,100):
        print "%.2f %s" % egg.x
        
