###############################################################################
#Dependencies
#standard python
import time
#Automat framework provided
from automat.core.hwcontrol.devices.instruments import Model
#3rd party hardware vendor, install from Internet
from Phidgets.PhidgetException import PhidgetException
from Phidgets.Devices.InterfaceKit import InterfaceKit

ATTACH_TIMEOUT = 10000 #milliseconds

###############################################################################
class Interface(Model):
    def __init__(self, serial_number):
        self._phidget = InterfaceKit()
        self._serial_number = serial_number
        self._is_initialized = False
    
    def initialize(self):
        if not self._is_initialized:
            self._phidget.openPhidget(serial = self._serial_number)
            self._phidget.waitForAttach(ATTACH_TIMEOUT)
            self._phidget.setRatiometric(False) #note the default is True!
            self._is_initialized = True
            
    def identify(self):
        if not self._is_initialized:
            self.initialize()
        name = self._phidget.getDeviceName()
        serial_number = self._phidget.getSerialNum()
        return "%s, Serial Number: %d" % (name, serial_number)
    
    def read_sensor(self, index):
        """ reads the raw value from the sensor at 'index' 
            returns integer in range [0,4095]
        """
        if not self._is_initialized:
            self.initialize()
        return self._phidget.getSensorRawValue(index)
    
    def read_all_sensors(self):
        """ reads all the sensors raw values, indices 0-7
            returns list of 8 integers in range [0,4095]
        """
        if not self._is_initialized:
            self.initialize()
        values = []
        for i in range(8):
            values.append(self.read_sensor(i))
        return values    
    
    def read_digital_input(self,index):
        """ reads the digital input at 'index' 
            returns True if grounded, False if open (pulled-up to 5V)
        """
        if not self._is_initialized:
            self.initialize()
        return self._phidget.getInputState(index)
    
    def write_digital_output(self,index,state):
        if not self._is_initialized:
            self.initialize()
        return self._phidget.setOutputState(index,state)
    
    def shutdown(self):
        if not self._is_initialized:
            self.initialize()
        self._phidget.closePhidget()
        self._is_initialized = False
    
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
    serial_number = 148221
    iface = Interface(serial_number)
