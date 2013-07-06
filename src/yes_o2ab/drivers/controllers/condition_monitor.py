"""
Controller to monitor instrument temperatures and environmental conditions
"""
###############################################################################
import time, datetime, traceback
import pylab
from automat.core.hwcontrol.controllers.controller import Controller, AbortInterrupt, NullController
try:
    from collections import OrderedDict
except ImportError:
    from yes_o2ab.support.odict import OrderedDict
###############################################################################
DEFAULT_CONFIGURATION = OrderedDict([
    ('retry_interval',10.0), #seconds
])

MAX_RETRY_ATTEMPTS = 10

###############################################################################
class Interface(Controller):
    def __init__(self,**kwargs):
        Controller.__init__(self, **kwargs)
        self.last_sample = None
        
    def initialize(self, **kwargs):
        self.thread_init(**kwargs)
        self.initialize_devices()
        
    def get_last_sample(self):
        return self.last_sample
        
    def acquire_sample(self):
        retry_interval = float(self.configuration['retry_interval']) #seconds
        retry_attempt = 0
        while retry_attempt < MAX_RETRY_ATTEMPTS: #this loop will cycle if grabbing any mutex fails
            try:
                sample = OrderedDict()
                devices = self.devices.copy() #do not accidently edit in place!
                camera = devices.pop('camera')
                sensor_SA_press = devices.pop('sensor_SA_press')
                sensor_SA_temp  = devices.pop('sensor_SA_temp')
                sensor_SA_humid = devices.pop('sensor_SA_humid')
                #read the camera with mutex to avoid inter-thread/process collisions
                with camera._mutex:
                    sample['CC_temp']  = camera.get_CC_temp()
                    sample['CH_temp']  = camera.get_CH_temp()
                    sample['CC_power'] = camera.get_CC_power()
                #read DAQ boards with mutex to avoid inter-thread/process collisions
                with sensor_SA_press.daq._mutex: 
                    sample['SA_press'] = sensor_SA_press.read()
                with sensor_SA_temp.daq._mutex: 
                    sample['SA_temp']  = sensor_SA_temp.read()
                with sensor_SA_humid.daq._mutex: 
                    sample['SA_humid'] = sensor_SA_humid.read()
                #remaining devices should be thermistors
                for key,therm in sorted(devices.items()):
                    if key.startswith('therm'): #check just in case 
                        with therm.daq._mutex:
                            sample[therm.name] = therm.read()
                #send sample event with information
                info = OrderedDict()
                info['timestamp'] = time.time()
                info['sample']    = sample 
                self._send_event("CONDITION_MONITOR_SAMPLE",info)
                #everything read successfuly now exit
                self.last_sample = sample
                return sample
            except RuntimeError: #caused when one of the mutex acquisition fails
                info = OrderedDict()
                info['timestamp'] = time.time()
                info['traceback'] = traceback.format_exc()
                info['retry_interval'] = retry_interval
                info['retry_attempt'] = retry_attempt
                self._send_event("CONDITION_MONITOR_MUTEX_ACQUISITION_FAILED",info)
                self.sleep(retry_interval)
                retry_attempt += 1 #enters loop again
        #retry attemps maxed out
        return None
        
    def main(self):
        try:
            interval = float(self.configuration['interval'])
            # START MONITORING LOOP  -----------------------------------
            info = OrderedDict()
            info['timestamp'] = time.time()
            info['interval']  = interval
            self._send_event("CONDITION_MONITOR_STARTED",info)
            #initialize the daq devices
            #daq.initialize()
            while True:
                t0 = time.time()
                self._thread_abort_breakout_point()
                samp = self.acquire_sample()
                self._thread_abort_breakout_point()
                # SLEEP UNTIL NEXT CYCLE  ----------------------------
                used_t = t0 - time.time()
                self.sleep(interval - used_t)
                #check if client requests stop
                if self._thread_check_stop_event():
                    # END NORMALLY -----------------------------------
                    info = OrderedDict()
                    info['timestamp'] = time.time()
                    self._send_event("CONDITION_MONITOR_STOPPED",info)
                    return
        except (AbortInterrupt, Exception), exc:
            # END ABNORMALLY -----------------------------------------
            info = OrderedDict()
            info['timestamp'] = time.time()
            info['reason']    = exc
            if not isinstance(exc, AbortInterrupt): 
                info['traceback'] = traceback.format_exc()
            self._send_event("CONDITION_MONITOR_ABORTED",info)
        finally: #Always clean up!
            self.reset()

#------------------------------------------------------------------------------
# INTERFACE CONFIGURATOR   
def get_interface(**kwargs):
    return Interface(**kwargs)
    
    
###############################################################################
# TEST CODE - Run the Controller, collect events, and plot
###############################################################################
# FIXME
if __name__ == "__main__":
    pass

