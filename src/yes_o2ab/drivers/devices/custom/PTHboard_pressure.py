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

##load and interpolate the data curve
#VOLTAGE_PRESSURE_FILENAME = os.path.sep.join((this_dir,".csv"))
#_volt_press_data = loadtxt(VOLTAGE_PRESSURE_FILENAME, delimiter=',')
#_P = _volt_press_data[:,0]
#_V = _volt_press_data[:,1]
#_volt_press_interp = interpolate.splrep(_P,_T,k=3)

#def volt_to_press(V):
#    return interpolate.splev(V,_volt_press_interp) 

################################################################################
#class for analog pressure sensor
class Interface(Device):
    def __init__(self, daq, daq_channel, name, V0=0):
        self.daq = daq
        self.daq_channel = daq_channel        
        self.name = name
        self.V0   = V0
        
    def initialize(self):
        pass

    def identify(self):
        daq_idn = self.daq.identify()
        idn = "PTH Board - Pressure Sensor %s, channel %d on %s" % (self.name, self.daq_channel, daq_idn)
        return idn

    def read(self):
        "reads the pressure in millibar"
        V = self.read_raw_voltage()
        V = V + self.V0 #apply voltage correction
        raise NotImplementedError
        P = volt_to_temp(V)
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
    daq = kwargs.get('daq')
    daq_channel = int(kwargs.get('daq_channel'))
    name = kwargs.get('name')
    V0   = float(kwargs.get('V0',0.0))
    iface = Interface(daq=daq,
                      daq_channel=daq_channel,
                      name=name,
                      V0 = V0
                     )
    return iface
################################################################################
# TEST CODE
################################################################################
if __name__ == "__main__":
    V = linspace(4.0,1.0,100)
    P = volt_to_temp(V)
    for v,t in zip(V,P):
        print "%0.3f\t%0.3f" % (v,t)
