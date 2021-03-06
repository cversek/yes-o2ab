###############################################################################
#Dependencies
#standard python
#Automat framework provided
from automat.core.hwcontrol.devices.instruments import Model
#other in-house packages
from FLI.device import USBDevice
#3rd party hardware vendor, install from Internet
###############################################################################


###############################################################################
class FLIDevice(Model):
    _driver_class = USBDevice
    def __init__(self, serial_number):
        self.serial_number = serial_number
        self._driver      = None
        self._initialized = False
                
    def _init_driver(self):
        ## FIXME FAKE cannot do this
        #        if self._driver is None:
        #            driver = self._driver_class.locate_device(self.serial_number)
        #            if driver is None:
        #                raise IOError, "could not locate device: %s" % self.serial_number
        #            else:
        #                self._driver = driver
        pass

    def _init_device(self):
        pass   
    #--------------------------------------------------------------------------
    # Implementation of the Instrument Interface
    def initialize(self):
        """ """
        if not self._initialized:
            self._init_driver()
            self._init_device()
            self._initialized = True 
                
    def identify(self):
        self._init_driver()
        ## FIXME FAKE cannot do this
        #        idn = "%s, SN#: %s, path: %s" % (self._driver.model, 
        #                                         self.serial_number, 
        #                                         self._driver.dev_name)
        idn = "FAKE FLIDevice"
        return idn
        
    def test(self):
        try:
            self._init_driver()
            idn = self.identify()
        except Exception, exc:
            return (False, exc)
        return (True, idn)
        
    def shutdown(self):
        pass
        
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
