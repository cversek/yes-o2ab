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
this_dir, _ = os.path.split(os.path.realpath(__file__))

SENSOR_TO_VOLTAGE = 5.0/(4095)

################################################################################
#class for analog pressure sensor
class Interface(Device):
    def __init__(self, daq, daq_channel, name, temp_sensor, A=0.0,B=1.0,C=0.0):
        self.daq = daq
        self.daq_channel = daq_channel        
        self.name = name
        self.temp_sensor = temp_sensor
        self.A = A
        self.B = B
        self.C = C
        
    def initialize(self):
        pass

    def identify(self):
        daq_idn = self.daq.identify()
        idn = "PTH Board - Pressure Sensor %s, channel %d on %s" % (self.name, self.daq_channel, daq_idn)
        return idn

    def read(self):
        "reads the pressure in inches Hg"
        Vp = self.read_raw_voltage()
        Vt = self.temp_sensor.read_raw_voltage()
        P = self.A + self.B*(Vp + 0.4*(Vt - self.C))
        return P
        
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
    temp_sensor = kwargs.pop('temp_sensor')
    A = float(kwargs.pop('A',0.0))
    B = float(kwargs.pop('B',1.0))
    C = float(kwargs.pop('C',0.0))
    iface = Interface(daq=daq,
                      daq_channel=daq_channel,
                      name=name,
                      temp_sensor=temp_sensor,
                      A=A,
                      B=B,
                      C=C,
                      **kwargs
                     )
    return iface
################################################################################
# TEST CODE
################################################################################
if __name__ == "__main__":
    pass
