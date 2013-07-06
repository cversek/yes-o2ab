###############################################################################
#Dependencies
#standard python
import os
#3rd part provided
from scipy import interpolate
from numpy import loadtxt, linspace
#Automat framework provided
from automat.core.hwcontrol.devices.device import Device
################################################################################

SENSOR_TO_VOLTAGE = 5.0/(4095)


################################################################################
#class for thermistor object
class Interface(Device):
    def __init__(self, daq, daq_channel, name, A=0.0, B=1.0):
        self.daq = daq
        self.daq_channel = daq_channel
        self.name = name
        self.A = A
        self.B = B
        
    def initialize(self):
        pass

    def identify(self):
        daq_idn = self.daq.identify()
        idn = "PTH Board - Pressure Sensor %s, channel %d on %s" % (self.name, self.daq_channel, daq_idn)
        return idn

    def read(self):
        "reads the humidity in %RH"
        V = self.read_raw_voltage()
        RH = (V/5.0 - self.A)/self.B
        return RH
        
    def read_raw_voltage(self):
        "reads the uncorrected voltage"
        val = self.daq.read_sensor(self.daq_channel)
        V = SENSOR_TO_VOLTAGE*val
        return V
        
    def shutdown(self):
        pass 
#-------------------------------------------------------------------------------
# INTERFACE CONFIGURATOR         
def get_interface(**kwargs):
    daq = kwargs.pop('daq')
    daq_channel = int(kwargs.pop('daq_channel'))
    name = kwargs.pop('name')
    A = float(kwargs.pop('A',0.0))
    B = float(kwargs.pop('B',1.0))
    iface = Interface(daq=daq,
                      daq_channel=daq_channel,
                      name=name,
                      A=A,
                      B=B,
                      **kwargs
                     )
    return iface
################################################################################
# TEST CODE
################################################################################
if __name__ == "__main__":
    V = linspace(4.0,1.0,100)
    T = volt_to_temp(V)
    for v,t in zip(V,T):
        print "%0.3f\t%0.3f" % (v,t)
