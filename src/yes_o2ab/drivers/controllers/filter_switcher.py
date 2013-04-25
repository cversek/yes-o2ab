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
        Controller.__init__(self, **kwargs)
        
    def initialize(self, **kwargs):
        try:
            self.thread_init(**kwargs) #gets the threads working
            filter_wheel = self.devices['filter_wheel']
            #send initialize event
            info = OrderedDict()
            info['timestamp'] = time.time()
            self._send_event("FILTER_SWITCHER_INITIALIZE", info)
            with filter_wheel._mutex:
                self.initialize_devices()
            self.query_position()
        except Exception as exc: #can't get mutex locks (thread or process level)
            #send initialize end
            info = OrderedDict()
            info['timestamp'] = time.time()
            info['exception'] = exc
            self._send_event("FILTER_SWITCHER_INITIALIZE_FAILED", info)
            
    def query_position(self):
        filter_wheel = self.devices['filter_wheel']
        with filter_wheel._mutex:
            self.position = filter_wheel.get_position()
        return self.position
        
    def set_filter_by_name(self, name):
        filter_wheel = self.devices['filter_wheel']
        wheel_A = filter_wheel.kwargs['wheel_A']
        wheel_B = filter_wheel.kwargs['wheel_B']
        backmap_A = dict([(val,int(slot.strip('slot'))) for slot,val in wheel_A.items()])
        backmap_B = dict([(val,int(slot.strip('slot'))) for slot,val in wheel_B.items()])
        open_A = backmap_A.get('Open',0)
        open_B = backmap_B.get('Open',0)
        A = backmap_A.get(name,open_A)
        B = backmap_B.get(name,open_B)
        pos = 5*B + A
        self.set_filter_by_position(position=pos)
            
    def set_filter_by_position(self, position):
        #send start event
        info = OrderedDict()
        info['timestamp'] = time.time()
        info['from_position'] = self.position
        info['to_position']   = position
        self._send_event("FILTER_SWITCHER_STARTED", info)
        filter_wheel = self.devices['filter_wheel']
        with filter_wheel._mutex:
            self.position = None
            filter_wheel.set_position(position) #should block
            self.position = position
        #send completed event
        info = OrderedDict()
        info['timestamp'] = time.time()
        info['position']  = self.position
        self._send_event("FILTER_SWITCHER_COMPLETED", info)    

    def shutdown(self):
        pass
        
    def main(self):
        try:
            position = self.configuration['position']
            self.set_filter_by_position(position)
        except Exception as exc:
            info = OrderedDict()
            info['timestamp'] = time.time()
            info['exception'] = exc
            self._send_event("FILTER_SWITCHER_FAILED", info)
        finally:
            #IMPORTANT!
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

