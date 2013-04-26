"""
Controller to capture images from FLI camera

--------------------------------------------------------------------------------
Configuration:

frametype - 'normal'     - open shutter exposure
            'dark'       - exposure with shutter closed
            'bias'       - zero second exposure (exptime ignnored)
            'flatfield'  - white screen in front of camera
            'opaque'     - filter wheel locking light input
            
exposure_time     - length of exposure in milliseconds (default 100)

rbi_num_flushes   - number of Residual Bulk Image (flood then flush) frames

rbi_exposure_time - length of the RBI exposure in milliseconds (default 10)
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
    ('frametype','normal'),
    ('num_captures',1),
    ('repeat_delay', 0),
    #('bitdepth','16bit'),    
    #('hbin',1),
    #('vbin',1),
    #('rbi_hbin',1),
    #('rbi_vbin',1),
    ('exposure_time',500),
    #('num_flushes',1),
    ('rbi_num_flushes',0),
    ('rbi_exposure_time',500),
    
])

SLEEP_TIME = 0.100 #seconds
###############################################################################
class Interface(Controller):
    def __init__(self,**kwargs):
        Controller.__init__(self, **kwargs)
        self.last_image = None
        self.saved_filter_position = None
        self.opaque_state = False

    def initialize(self, **kwargs):
        try:
            self.thread_init(**kwargs) #gets the threads working
            camera = self.devices['camera']
            camera_info = None
            with camera._mutex: #locks the resource
                self.initialize_devices()
                camera_info = camera.get_info() #add a bunch of metadata
             #send initialize start event
            info = OrderedDict()
            info['timestamp'] = time.time()
            info['camera_info'] = camera_info
            self._send_event("IMAGE_CAPTURE_INITIALIZE_STARTED", info)
            #initialize component controllers
            flatfield_switcher = self.controllers['flatfield_switcher']
            flatfield_switcher.initialize(**kwargs)
            filter_switcher = self.controllers['filter_switcher']
            filter_switcher.initialize(**kwargs)
            #send initialize completed event
            info = OrderedDict()
            info['timestamp'] = time.time()
            info['camera_info'] = camera_info
            self._send_event("IMAGE_CAPTURE_INITIALIZE_COMPLETED", info)
            return True
        except Exception as exc: #can't get mutex locks (thread or process level)
            #send initialize end
            info = OrderedDict()
            info['timestamp'] = time.time()
            info['exception'] = exc
            self._send_event("IMAGE_CAPTURE_INITIALIZE_FAILED", info)
            return False
            
    def shutdown(self):
        pass
            
             
    def main(self):
        try:
            frametype    = self.configuration['frametype']
            num_captures = self.configuration['num_captures']
            if not num_captures is None:
                num_captures = int(num_captures)
            repeat_delay = float(self.configuration['repeat_delay'])
            # START LOOP -------------------------------------------------
            i = 0
            while True:
                if  self._thread_check_stop_event() or (not num_captures is None and i >= num_captures):
                        # END NORMALLY -----------------------------------
                        info = OrderedDict()
                        info['timestamp'] = time.time()
                        self._send_event("IMAGE_CAPTURE_LOOP_STOPPED",info)
                        return
                # CAPTURE ------------------------------------------------
                self.do_exposure(frametype)
                # SLEEP for a bit ----------------------------------------
                self.sleep(repeat_delay)
                i += 1
                # REPEAT
        except (AbortInterrupt, Exception), exc:
            # END ABNORMALLY ---------------------------------------------
            info = OrderedDict()
            info['timestamp'] = time.time()
            info['exception'] = exc
            if not isinstance(exc, AbortInterrupt):
                info['traceback'] = traceback.format_exc()
            self._send_event("IMAGE_CAPTURE_LOOP_ABORTED",info)
        finally:
            # FINSIH UP --------------------------------------------------
            self.reset()
            
    def configure_optics(self, frametype):
        #first configure the frametype
        if   frametype == 'normal':
            self.set_flatfield('out')
            self.set_opaque_filter(False)
            self.configuration['camera_frametype'] = 'normal'
        elif frametype == 'dark':
            self.set_opaque_filter(False)
            self.configuration['camera_frametype'] = 'dark'
        elif frametype == 'bias':
            #bias is a zero time readout
            self.set_opaque_filter(False)
            self.configuration['camera_frametype'] = 'dark'
        elif frametype == 'flatfield':
            #require the flipper to be moved up
            self.set_flatfield('in')
            self.set_opaque_filter(False)
            self.configuration['camera_frametype'] = 'normal'
        elif frametype == 'opaque':
            self.set_flatfield('out')
            self.set_opaque_filter(True)
            self.configuration['camera_frametype'] = 'normal'
        else:
            raise ValueError("frametype '%s' is not valid" % frametype)
        
        
    def set_flatfield(self, state):
        flatfield_switcher = self.controllers['flatfield_switcher']
        #only switch if necessary
        if flatfield_switcher.state != state:
            #chain events
            flatfield_switcher.thread_init(event_queue = self.event_queue)
            flatfield_switcher.configuration['state'] = state
            flatfield_switcher.run() #this should block
            
    def set_opaque_filter(self, state = True):
        filter_switcher = self.controllers['filter_switcher']
        if state == True:
            if self.opaque_state == False:
                self.saved_filter_position = filter_switcher.query_position()
                filter_switcher.set_filter_by_name('Opaque')
            self.opaque_state = True
        elif state == False:
            if self.opaque_state == True:
                old_pos = self.saved_filter_position
                filter_switcher.set_filter_by_position(old_pos)
            self.opaque_state = False
        
    def do_exposure(self, frametype = 'normal'):
        camera    = self.devices['camera']
        #hbin    = int(self.configuration['hbin'])
        #vbin    = int(self.configuration['vbin'])
        exptime = int(self.configuration['exposure_time'])
        if frametype == 'bias':
            exptime = 0 #bias is a zero time exposure
        #rbi_hbin = int(self.configuration['rbi_hbin'])
        #rbi_vbin = int(self.configuration['rbi_vbin'])
        rbi_exptime = int(self.configuration['rbi_exposure_time'])
        rbi_nflushes = int(self.configuration['rbi_num_flushes'])
        #configure the optics for the frametype
        self.configure_optics(frametype) #sets camera_frametype
        camera_frametype = self.configuration['camera_frametype']
        info = OrderedDict()
        info['timestamp'] = time.time()
        info['frametype'] = frametype
        info['camera_frametype'] = camera_frametype
        #info['hbin'] = hbin
        #info['vbin'] = vbin
        info['exposure_time'] = exptime
        #info['rbi_hbin'] = rbi_hbin
        #info['rbi_vbin'] = rbi_vbin
        info['rbi_exposure_time'] = rbi_exptime
        info['rbi_num_flushes']   = rbi_nflushes
        self._send_event("IMAGE_CAPTURE_EXPOSURE_STARTED", info)
        
        with camera._mutex: #locks the resource
            #do RBI flushes
            for i in range(rbi_nflushes):
                info = OrderedDict()
                info['timestamp'] = time.time()
                info['index']     = i
                info['exposure_time'] = rbi_exptime
                self._send_event("IMAGE_CAPTURE_EXPOSURE_RBI_FLUSH", info)
                #floods the CCD
                camera.start_exposure(rbi_exptime, frametype = 'rbi_flush')
                while camera.get_exposure_timeleft() > 0:
                    self._thread_abort_breakout_point()
                    self.sleep(SLEEP_TIME)
                camera.fetch_image()
                #finish flush in dark (no shutter) mode
                camera.start_exposure(0, frametype = 'dark')
                while camera.get_exposure_timeleft() > 0:
                    self._thread_abort_breakout_point()
                    self.sleep(SLEEP_TIME)
                camera.fetch_image()
            #now acquire the image
            camera.start_exposure(exptime, frametype = camera_frametype)
            while camera.get_exposure_timeleft() > 0:
                self._thread_abort_breakout_point()
                self.sleep(SLEEP_TIME)
            I = camera.fetch_image()
            self.last_image = I
            #completed
            info = OrderedDict()
            info['timestamp'] = time.time()
            info['frametype'] = frametype
            info['camera_frametype'] = camera_frametype
            #info['hbin'] = hbin
            #info['vbin'] = vbin
            info['exposure_time'] = exptime
            #info['rbi_hbin'] = rbi_hbin
            #info['rbi_vbin'] = rbi_vbin
            info['rbi_exposure_time'] = rbi_exptime
            info['rbi_num_flushes']   = rbi_nflushes
            info['image_array'] = I
            self._send_event("IMAGE_CAPTURE_EXPOSURE_COMPLETED", info)
            return self.last_image

    def query_metadata(self):
        camera = self.devices['camera']
        with camera._mutex: #locks the resource            
            self.metadata['CC_temp']  = camera.get_CC_temp()
            self.metadata['CH_temp']  = camera.get_CH_temp()
            self.metadata['CC_power'] = camera.get_CC_power()
        return self.metadata
   
#------------------------------------------------------------------------------
# INTERFACE CONFIGURATOR
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

