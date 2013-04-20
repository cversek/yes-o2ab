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
        info = OrderedDict()
        devices = self.devices.copy() #do not accidently edit in place!
        camera = devices.pop('camera')
        sensor_SA_press = devices.pop('sensor_SA_press')
        sensor_SA_temp  = devices.pop('sensor_SA_temp')
        sensor_SA_humid = devices.pop('sensor_SA_humid')
        #read the camera with mutex to avoid inter-thread/process collisions
        with camera._mutex:
            info['CC_temp']  = camera.get_CC_temp()
            info['CH_temp']  = camera.get_CH_temp()
            info['CC_power'] = camera.get_CC_power()
        #read DAQ boards with mutex to avoid inter-thread/process collisions
        with sensor_SA_press.daq._mutex: 
            info['SA_press_raw_voltage'] = sensor_SA_press.read_raw_voltage()
        with sensor_SA_temp.daq._mutex: 
            info['SA_temp_raw_voltage']  = sensor_SA_temp.read_raw_voltage()
        with sensor_SA_humid.daq._mutex: 
            info['SA_humid_raw_voltage'] = sensor_SA_humid.read_raw_voltage()
        #remaining devices should be thermistors
        for key,therm in sorted(devices.items()):
            if key.startswith('therm'): #check just in case 
                with therm.daq._mutex:
                    info[therm.name] = therm.read()
        return info
            
    def main(self):
        interval = float(self.configuration['interval'])
        try:
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
                #send information
                info = OrderedDict()
                info['timestamp'] = t0
                info.update(samp) #merge in sample dictionary
                self._send_event("CONDITION_SAMPLE",info)
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
            import traceback
            info = OrderedDict()
            info['timestamp'] = time.time()
            info['reason']    = exc
            if not isinstance(exc, AbortInterrupt): 
                info['traceback'] = traceback.format_exc()
            self._send_event("CONDITION_MONITOR_ABORTED",info)
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

