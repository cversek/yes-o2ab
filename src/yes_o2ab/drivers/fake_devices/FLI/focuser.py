###############################################################################
#Dependencies
#standard python
#Automat framework provided
from automat.core.hwcontrol.devices.instruments import Model
#other in-house packages
from FLI import USBFocuser
#3rd party hardware vendor, install from Internet
#package local
from device import FLIDevice
###############################################################################


###############################################################################
class Interface(FLIDevice):
    _driver_class = USBFocuser
    def __init__(self, serial_number):
        FLIDevice.__init__(self, serial_number=serial_number)

    def _init_device(self):
        self.goto_home()
    #--------------------------------------------------------------------------
    # Implementation of the Focuser Interface
    #--------------------------------------------------------------------------
    def get_position(self):
        "gets the current focuser position in steps"
        self._init_driver()
        return 0

    def goto_home(self):
        "resests the device to the home position, pos=0"
        self._init_driver()

    def step(self, steps, blocking = True):
        self.initialize()
        
    #--------------------------------------------------------------------------
      

#------------------------------------------------------------------------------
# INTERFACE CONFIGURATOR         
def get_interface(serial_number):
    return Interface(serial_number=serial_number)
    
###############################################################################
# TEST CODE
###############################################################################
if __name__ == "__main__":
    pass
