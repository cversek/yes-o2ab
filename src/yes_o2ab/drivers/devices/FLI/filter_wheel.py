###############################################################################
#Dependencies
#standard python
#Automat framework provided
from automat.core.hwcontrol.devices.instruments import Model
#other in-house packages
from FLI import USBFilterWheel
#3rd party hardware vendor, install from Internet
#package local
from device import FLIDevice
###############################################################################


###############################################################################
class Interface(FLIDevice):
    _driver_class = USBFilterWheel
    def __init__(self, serial_number):
        FLIDevice.__init__(self, serial_number=serial_number)
    def _init_device(self):
        self.set_position(0)
    #--------------------------------------------------------------------------
    # Implementation of the Filter Wheel Interface
    #--------------------------------------------------------------------------
    def set_position(self, pos):
        "Sets the postion of the filter wheel"
        self._init_driver()     
        self._driver.set_filter_pos(pos)

    def get_position(self):
        "Gets the postion of the filter wheel"
        self._init_driver()        
        return self._driver.get_filter_pos()

    def get_filter_count(self):
        "Gets the total number of positions"
        self._init_driver()        
        return self._driver.get_filter_count()
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
