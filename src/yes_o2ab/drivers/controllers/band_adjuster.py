"""
Controller to adjust the FLI focuser
"""
###############################################################################
import time, copy, traceback
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

DEFAULT_CONTROLLERS = OrderedDict([
    ('band_switcher', NullController())
])

POLLING_DELAY = 0.1 #seconds
BABYSTEPSIZE  = 10
###############################################################################
class Interface(Controller):
    def __init__(self,**kwargs):
        self.position = None
        Controller.__init__(self, **kwargs)
        
    def initialize(self, **kwargs):
        self.thread_init(**kwargs) #gets the threads working
        picomotor_driver = self.devices['picomotor_driver']
        picomotorA       = self.devices['picomotorA']
        picomotorB       = self.devices['picomotorB']
        band_switcher    = self.controllers['band_switcher']
        #send initialize start event
        info = OrderedDict()
        info['timestamp'] = time.time()
        info['band']      = band_switcher.band
        self._send_event("BAND_ADJUSTER_INITIALIZE_START", info)
        try:
            with picomotor_driver._mutex:
                self.initialize_devices()
        except RuntimeError, exc: #can't get mutex locks (thread or process level)
            #send initialize end
            info = OrderedDict()
            info['timestamp'] = time.time()
            info['exception'] = exc
            self._send_event("BAND_ADJUSTER_INITIALIZE_FAILED", info)
        #success, send initialize end
        info = OrderedDict()
        info['timestamp'] = time.time()
        self._send_event("BAND_ADJUSTER_INITIALIZE_END", info)
    
    def shutdown(self):
        pass
        
    def query_position(self):
        try:
            picomotor_driver = self.devices['picomotor_driver']
            picomotorA       = self.devices['picomotorA']
            picomotorB       = self.devices['picomotorB']
            band_switcher    = self.controllers['band_switcher']
            #determine which band we are in to find the correct picomotor channel
            band = band_switcher.band
            target_motor = None 
            channel = None
            if band == 'O2A':
                target_motor = picomotorA
                channel = 'A'
            elif band == 'H2O':
                target_motor = picomotorB
                channel = 'B'
            elif band is None:
                self.position = None
            else:
                raise RuntimeError("band state is %s" % band)
            #run only if band is defined
            if not band is None:
                with picomotor_driver._mutex:
                    self.position = target_motor.get_position()
            #success
            info = OrderedDict()
            info['timestamp'] = time.time()
            info['band']      = band
            info['picomotor_driver_channel'] = channel
            info['position']  = self.position
            self._send_event("BAND_ADJUSTER_QUERY_POSITION", info)
            return self.position
        except Exception as exc: #can't get mutex locks (thread or process level)
            info = OrderedDict()
            info['timestamp'] = time.time()
            info['exception'] = exc
            self._send_event("BAND_ADJUSTER_QUERY_POSITION_FAILED", info)
        
        
    def main(self):
        try:
            picomotor_driver = self.devices['picomotor_driver']
            picomotorA       = self.devices['picomotorA']
            picomotorB       = self.devices['picomotorB']
            band_switcher    = self.controllers['band_switcher']
            step_size = int(self.configuration['step_size'])
            step_dir  = int(self.configuration['step_direction']) #"+1" or "-1" as string
            step = step_size*step_dir
            pos_start = self.query_position()
            #determine which band we are in to find the correct picomotor channel
            band = band_switcher.band
            target_motor = None 
            channel = None
            if band == 'O2A':
                target_motor = picomotorA
                channel = 'A'
            elif band == 'H2O':
                target_motor = picomotorB
                channel = 'B'
            else:
                self.position = None
                info = OrderedDict()
                info['timestamp'] = time.time()
                info['exception'] = RuntimeError("band state is %s" % band)
                self._send_event("BAND_ADJUSTER_STEP_FAILED", info)
                return
            #send start event
            info = OrderedDict()
            info['timestamp'] = time.time()
            info['band']      = band
            info['picomotor_driver_channel'] = channel
            info['step']      = step
            info['start_position']  = pos_start
            self._send_event("BAND_ADJUSTER_STEP_STARTED", info)
            with picomotor_driver._mutex:   
                #break a large step into small ones
                babysteps = step_size // BABYSTEPSIZE * [step_dir*BABYSTEPSIZE] + [step_dir*(step_size % BABYSTEPSIZE)]
                for babystep in babysteps:
                    pos = target_motor.get_position()
                    steps_remaining = step - (pos - pos_start)
                    info = OrderedDict()
                    info['timestamp'] = time.time()
                    info['position']  = pos
                    info['steps_remaining'] = steps_remaining
                    self._send_event("BAND_ADJUSTER_STEP_POLL", info)
                    #take a babystep
                    target_motor.move_relative(babystep, blocking = True)
            # END NORMALLY -------------------------------------------
            pos_end = self.query_position()
            info = OrderedDict()
            info['timestamp'] = time.time()
            info['band']      = band
            info['picomotor_driver_channel'] = channel
            info['step']      = step
            info['start_position']  = pos_start
            info['pos_end']   = pos_end
            self._send_event("BAND_ADJUSTER_STEP_END", info)
            return pos_end
        except (AbortInterrupt, Exception), exc:
            # END ABNORMALLY ---------------------------------------------
            info = OrderedDict()
            info['timestamp'] = time.time()
            info['exception'] = exc
            if not isinstance(exc, AbortInterrupt):
                info['traceback'] = traceback.format_exc()
            self._send_event("BAND_ADJUSTER_STEP_FAILED",info)
        finally:
            # FINISH UP --------------------------------------------------
            self.reset()
      
        
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

