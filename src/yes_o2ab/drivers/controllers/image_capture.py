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
    #('bitdepth','16bit'),
    ('frametype','normal'),
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
        self.last_image = None

    def initialize(self, **kwargs):
        self.thread_init(**kwargs) #gets the threads working
        camera = self.devices['camera']
        try:
            with camera._mutex: #locks the resource
                self.initialize_devices()
                #send initialize start event
                info = OrderedDict()
                info['timestamp'] = time.time()
                info['camera_info'] = camera.get_info() #add a bunch of metadata
                self._send_event("IMAGE_CAPTURE_INITIALIZED", info)  
        except RuntimeError, exc: #can't get mutex locks (thread or process level)
            #send initialize end
            info = OrderedDict()
            info['timestamp'] = time.time()
            info['exception'] = exc
            self._send_event("IMAGE_CAPTURE_INITIALIZE_FAIL", info)
        
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
        camera  = self.devices['camera']
        frametype = self.configuration['frametype']
        hbin    = int(self.configuration['hbin'])
        vbin    = int(self.configuration['vbin'])
        exptime = int(self.configuration['exposure_time'])
        rbi_hbin = int(self.configuration['rbi_hbin'])
        rbi_vbin = int(self.configuration['rbi_vbin'])
        rbi_exptime = int(self.configuration['rbi_exposure_time'])
        rbi_nflushes = int(self.configuration['rbi_num_flushes'])
        info = OrderedDict()
        info['timestamp'] = time.time()
        info['frametype'] = frametype
        info['hbin'] = hbin
        info['vbin'] = vbin
        info['exposure_time'] = exptime
        info['rbi_hbin'] = rbi_hbin
        info['rbi_vbin'] = rbi_vbin
        info['rbi_exposure_time'] = rbi_exptime
        info['rbi_num_flushes'] = rbi_nflushes
        self._send_event("IMAGE_CAPTURE_STARTED", info)
        try:
            with camera._mutex: #locks the resource
                #camera.
                I = camera.take_photo(exptime,
                                      frametype = frametype,
                                     )
                self.last_image = I
                #send initialize start event
                info = OrderedDict()
                info['timestamp'] = time.time()
                info['camera_info'] = camera.get_info() #add a bunch of metadata
                self._send_event("IMAGE_CAPTURE_COMPLETED", info)  
        except RuntimeError, exc: #can't get mutex locks (thread or process level)
            #send initialize end
            info = OrderedDict()
            info['timestamp'] = time.time()
            info['exception'] = exc
            self._send_event("IMAGE_CAPTURE_FAILED", info)
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

