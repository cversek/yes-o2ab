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
        self.serial_number = serial_number
        
    def identify(self):
        return "(!!!DEBUGGING FAKE) Phidget Frequency Counter 1054, Serial Number: %d" % self.serial_number
        
    def set_enabled(self, index, state = True):
        self._phidget.setEnabled(index,state)
        
    def get_frequency(self, index):
        return 0.0
    
    def shutdown(self):
        pass
    
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
