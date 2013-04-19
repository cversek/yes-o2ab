"""
Controller to switch the positio of the FLI filter_wheel
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
    ('position',0),
])

###############################################################################
class Interface(Controller):
    def __init__(self,**kwargs):
        self.position = None
        #kwargs.get(
        Controller.__init__(self, **kwargs)
        
    def initialize(self):
        filter_wheel = self.devices['filter_wheel']
        self.position = filter_wheel.get_position()
    
    def shutdown(self):
        pass
        
    def main(self):
        filter_wheel = self.devices['filter_wheel']
        pos          = self.configuration['position']
        filter_wheel.set_position(pos)
        self.position = pos
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

