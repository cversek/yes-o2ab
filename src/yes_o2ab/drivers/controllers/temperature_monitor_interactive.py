"""
Controller to monitor temperature from the USB DAQ
"""
###############################################################################
import time, datetime
import pylab
from automat.core.hwcontrol.controllers.controller import Controller, AbortInterrupt, NullController
###############################################################################


###############################################################################
class InteractiveInterface:
    def __init__(self,**kwargs):
        Controller.__init__(self, **kwargs)
        
    def acquire_sample(self):
        daq = self.devices['daq']
        vals = [time.time()]
        vals.extend(daq.read_all_sensors())
        return vals
            
    def main(self, delay = None, max_samples = None):
        daq = self.devices['daq']
        now = datetime.datetime.now()
        filename = now.strftime("%Y_%m_%d_%H_%M_temps.csv")
        if delay is None:
            delay = float(self.configuration['default_delay'])
        try:
            data = []
            while True:
                if not (max_samples is None) and (len(data) >= max_samples):
                    break
                vals = self.acquire_sample()
                data.append(vals)
                print "\t".join(map(str,vals))
                time.sleep(delay)
        except KeyboardInterrupt:
            pass
            
        data = pylab.array(data)
        pylab.savetxt(filename,data,delimiter=",")    
       
            
def get_interface(interface_mode = 'interactive', **kwargs):
    if   interface_mode == 'interactive':
        return InteractiveInterface(**kwargs)
    else:
        raise ValueError, "there is no '%s' interace for this controller, only 'interactive'" % interface_mode
            
    
    
###############################################################################
# TEST CODE - Run the Controller, collect events, and plot
###############################################################################
# FIXME
if __name__ == "__main__":
    pass

