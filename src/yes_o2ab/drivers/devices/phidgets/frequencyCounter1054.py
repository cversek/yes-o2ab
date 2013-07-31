###############################################################################
#Dependencies
#standard python
import time
#Automat framework provided
from automat.core.hwcontrol.devices.instruments import Model
#3rd party hardware vendor, install from Internet
from Phidgets.PhidgetException import PhidgetException
from Phidgets.Devices.FrequencyCounter import FrequencyCounter

ATTACH_TIMEOUT = 10000 #milliseconds

###############################################################################
class Interface(Model):
    def __init__(self, serial_number):
        self._phidget = FrequencyCounter()
        self._phidget.openPhidget(serial=serial_number)
        self._phidget.waitForAttach(ATTACH_TIMEOUT)
        
    def identify(self):
        name = self._phidget.getDeviceName()
        serial_number = self._phidget.getSerialNum()
        return "%s, Serial Number: %d" % (name, serial_number)
        
    def set_enabled(self, index, state = True):
        self._phidget.setEnabled(index,state)
        
    def get_frequency(self, index):
        """ reads the raw value from the sensor at 'index' 
            returns integer in range [0,4095]
        """
        return self._phidget.getFrequency(index)
    
    def shutdown(self):
        self._phidget.closePhidget()
    
    def __del__(self):
        self.shutdown()

#------------------------------------------------------------------------------
# INTERFACE CONFIGURATOR         
def get_interface(serial_number):
    serial_number = int(serial_number)
    return Interface(serial_number)
    
###############################################################################
# TEST CODE
###############################################################################
if __name__ == "__main__":
    serial_number = 143033
    iface = Interface(serial_number)
