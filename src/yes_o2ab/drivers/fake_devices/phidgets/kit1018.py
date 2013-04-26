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
        self.serial_number = serial_number
       
    def identify(self):
        return "(!!!DEBUGGING FAKE) Phidget InterfaceKit 8/8/8, Serial Number: %d" % self.serial_number
    
    def read_sensor(self, index):
        """ reads the raw value from the sensor at 'index' 
            returns integer in range [0,4095]
        """
        return 0.0
        
    def read_all_sensors(self):
        """ reads all the sensors raw values, indices 0-7
            returns list of 8 integers in range [0,4095]
        """
        values = []
        for i in range(8):
            values.append(self.read_sensor(i))
        return values   
         
    def read_digital_input(self,index):
        """ reads the digital input at 'index' 
            returns True if grounded, False if open (pulled-up to 5V)
        """
        return 0
        
    def write_digital_output(self,index,state):
        return 0
            
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
    serial_number = 148221
    iface = Interface(serial_number)
