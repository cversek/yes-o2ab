"""
Controller to capture images from FLI camera
"""
###############################################################################
import time, copy
from automat.core.hwcontrol.controllers.controller import Controller, AbortInterrupt, NullController
OrderedDict = None
try:
    from collections import OrderedDict
except ImportError:
    from yes_o2ab.support.odict import OrderedDict
###############################################################################
DEFAULT_CONFIGURATION = OrderedDict([
    ('hbin',1),
    ('vbin',1),
    ('rbi_hbin',1),
    ('rbi_vbin',1),
    ('exposure_time',100),
    ('num_flushes',1),
    ('rbi_exposure_time',100),
    ('rbi_num_flushes',1),
])

###############################################################################
class Interface(Controller):
    def __init__(self,**kwargs):
        Controller.__init__(self, **kwargs)
        
    def initialize(self):
        camera = self.devices['camera']
        with camera._mutex: #locks the resource
            camera.initialize()
        
    def query_metadata(self):
        camera = self.devices['camera']
        with camera._mutex: #locks the resource
            self.metadata['CC_temp']  = camera.get_CC_temp()
            self.metadata['CH_temp']  = camera.get_CH_temp()
            self.metadata['CC_power'] = camera.get_CC_power()
        return self.metadata
        
    def shutdown(self):
        pass
        
    def main(self):
        self.reset() #reset the controller to be used again
        
       
def get_interface(**kwargs):
    interface_mode = kwargs.pop('interface_mode','threaded')
    if   interface_mode == 'threaded':
        return Interface(**kwargs)
            
###############################################################################
# TEST CODE - Run the Controller, collect events, and plot
###############################################################################
# FIXME
if __name__ == "__main__":
    pass

