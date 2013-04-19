"""
Controller to monitor instrument temperatures and environmental conditions
"""
###############################################################################
import time, datetime
import pylab
from automat.core.hwcontrol.controllers.controller import Controller, AbortInterrupt, NullController
try:
    from collections import OrderedDict
except ImportError:
    from yes_o2ab.support.odict import OrderedDict
###############################################################################


###############################################################################
class Interface(Controller):
    def __init__(self,**kwargs):
        Controller.__init__(self, **kwargs)
        
    def acquire_sample(self):
        temps = OrderedDict()
        for key,therm in sorted(self.devices.items()):
            temps[therm.name] = therm.read()
        return temps
            
    def main(self):
        interval = float(self.configuration['interval'])
        try:
            # START MONITORING LOOP  -----------------------------------
            info = OrderedDict()
            info['timestamp'] = time.time()
            info['interval']  = interval
            self._send_event("TEMPERATURE_MONITOR_STARTED",info)
            #initialize the daq devices
            #daq.initialize()
            while True:
                t0 = time.time()
                self._thread_abort_breakout_point()
                temps = self.acquire_sample()
                #send information
                info = OrderedDict()
                info['timestamp'] = t0
                info['temperatures'] = temps
                self._send_event("TEMPERATURE_SAMPLE",info)
                self._thread_abort_breakout_point()
                # SLEEP UNTIL NEXT CYCLE  ----------------------------
                used_t = t0 - time.time()
                self.sleep(interval - used_t)
                #check if client requests stop
                if self._thread_check_stop_event():
                    # END NORMALLY -----------------------------------
                    info = OrderedDict()
                    info['timestamp'] = time.time()
                    self._send_event("TEMPERATURE_MONITOR_STOPPED",info)
                    return
        except (AbortInterrupt, Exception), exc:
            # END ABNORMALLY -----------------------------------------
            import traceback
            info = OrderedDict()
            info['timestamp'] = time.time()
            info['reason']    = exc
            if not isinstance(exc, AbortInterrupt): 
                info['traceback'] = traceback.format_exc()
            self._send_event("TEMPERATURE_MONITOR_ABORTED",info)
        finally: #Always clean up!
            pass
            #daq.shutdown()  
       
            
def get_interface(interface_mode = 'threaded', **kwargs):
    if   interface_mode == 'threaded':
        return Interface(**kwargs)
    elif interface_mode == 'interactive':
        from temperature_monitor_interactive import get_interface as get_interface2
        return get_interface2(interface_mode = 'interactive', **kwargs)
            
    
    
###############################################################################
# TEST CODE - Run the Controller, collect events, and plot
###############################################################################
# FIXME
if __name__ == "__main__":
    pass

