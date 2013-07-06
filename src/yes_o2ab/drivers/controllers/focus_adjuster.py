"""
Controller to adjust the FLI focuser
"""
###############################################################################
import sys, time, copy, traceback
from automat.core.hwcontrol.controllers.controller import Controller, AbortInterrupt, NullController
OrderedDict = None
try:
    from collections import OrderedDict
except ImportError:
    from yes_o2ab.support.odict import OrderedDict
###############################################################################
DEFAULT_CONFIGURATION = OrderedDict([
    ('step_size', 1),
    ('step_direction', "+1"), #or -1
])

POLLING_DELAY = 0.1 #seconds
BABYSTEPSIZE  = 100
###############################################################################
class Interface(Controller):
    def __init__(self,**kwargs):
        self.position = None
        Controller.__init__(self, **kwargs)
        
    def initialize(self, **kwargs):
        self.thread_init(**kwargs) #gets the threads working
        focuser = self.devices['focuser']
        #send initialize start event
        info = OrderedDict()
        info['timestamp'] = time.time()
        self._send_event("FOCUS_ADJUSTER_INITIALIZE_START", info)
        try:
            with focuser._mutex:
                self.initialize_devices()
        except RuntimeError, exc: #can't get mutex locks (thread or process level)
            #send initialize end
            info = OrderedDict()
            info['timestamp'] = time.time()
            info['exception'] = exc
            self._send_event("FOCUS_ADJUSTER_INITIALIZE_FAILED", info)
        #success, send initialize end
        info = OrderedDict()
        info['timestamp'] = time.time()
        self._send_event("FOCUS_ADJUSTER_INITIALIZE_END", info)
        self.query_position()
    
    def shutdown(self):
        pass
        
    def query_position(self):
        focuser   = self.devices['focuser']
        with focuser._mutex:
            self.position = focuser.get_position()
        return self.position
        
    def main(self):
        try:
            focuser   = self.devices['focuser']
            step_size = int(self.configuration['step_size'])
            step_dir  = int(self.configuration['step_direction']) #"+1" or "-1" as string
            step = step_size*step_dir
            pos_start = self.query_position()
            #send initialize start event
            info = OrderedDict()
            info['timestamp'] = time.time()
            info['step']      = step
            info['start_position']  = pos_start
            self._send_event("FOCUS_ADJUSTER_STEP_STARTED", info)
        
            with focuser._mutex:   
                #focuser.step(step, blocking = False) #FIXME asynchron stepper mode doesn't work!
                #break a large step into small ones
                babysteps = step_size // BABYSTEPSIZE * [step_dir*BABYSTEPSIZE] + [step_dir*(step_size % BABYSTEPSIZE)]
                for babystep in babysteps:
                    pos = focuser.get_position()
                    steps_remaining = step - (pos - pos_start)
                    info = OrderedDict()
                    info['timestamp'] = time.time()
                    info['position']  = pos
                    info['steps_remaining'] = steps_remaining
                    self._send_event("FOCUS_ADJUSTER_STEP_POLL", info)
                    #take a babystep
                    focuser.step(babystep, blocking = True)
            #success
            pos_end = self.query_position()
            # END NORMALLY ---------------------------------------------
            info = OrderedDict()
            info['timestamp'] = time.time()
            info['step']      = step
            info['start_position']  = pos_start
            info['pos_end']   = pos_end
            self._send_event("FOCUS_ADJUSTER_STEP_COMPLETED", info)
        except (AbortInterrupt, Exception), exc:
            # END ABNORMALLY ---------------------------------------------
            info = OrderedDict()
            info['timestamp'] = time.time()
            info['exception'] = exc
            if not isinstance(exc, AbortInterrupt):
                info['traceback'] = traceback.format_exc()
            self._send_event("FOCUS_ADJUSTER_STEP_FAILED", info)
        finally:
            #finish up
            self.reset() #reset the controller to be used again
        
#------------------------------------------------------------------------------
# INTERFACE CONFIGURATOR     
def get_interface(**kwargs):
    interface_mode = kwargs.pop('interface_mode','threaded')
    if   interface_mode == 'threaded':
        return Interface(**kwargs)
    else:
        raise ValueError("interface_mode '%s' is not valid" % interface_mode)
            
###############################################################################
# TEST CODE - Run the Controller, collect events, and plot
###############################################################################
# FIXME
if __name__ == "__main__":
    pass

