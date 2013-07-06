"""
Controller to switch the O2ab spectrometer between A (oxygen A) and B (water )
and to finely adjust the diffraction grating position
"""
###############################################################################
import sys, time, copy
from automat.core.hwcontrol.controllers.controller import Controller, AbortInterrupt, NullController
OrderedDict = None
try:
    from collections import OrderedDict
except ImportError:
    from yes_o2ab.support.odict import OrderedDict
###############################################################################
DEFAULT_CONFIGURATION = OrderedDict([
    ("band",None),
])
WINDINGS_CHANNEL = 1
WINDINGS_STATE_ON = 0
WINDINGS_STATE_OFF = 1
###############################################################################
class Interface(Controller):
    def __init__(self,**kwargs):
        self.band = None
        #kwargs.get(
        Controller.__init__(self, **kwargs)
        
    def initialize(self, **kwargs):
        try:
            self.thread_init(**kwargs) #gets the threads working
            band_motor = self.devices['band_motor']
            #send initialize event
            info = OrderedDict()
            info['timestamp'] = time.time()
            self._send_event("BAND_SWITCHER_INITIALIZE", info)
            with band_motor.motor_controller._mutex:
                self.initialize_devices()
            #ensure windings are off
            self.set_windings('off')
        except RuntimeError, exc: #can't get mutex locks (thread or process level)
            #send initialize end
            info = OrderedDict()
            info['timestamp'] = time.time()
            info['exception'] = exc
            self._send_event("BAND_SWITCHER_INITIALIZE_FAILED", info)
        
    def set_windings(self, state = 'on'):
        "set current to windings, 'state' must be 'on' or 'off'"
        band_motor = self.devices['band_motor']
        with band_motor.motor_controller._mutex:
            if state == 'on':
                band_motor.motor_controller.write_digital_output(WINDINGS_CHANNEL,WINDINGS_STATE_ON)
            elif state == 'off':
                band_motor.motor_controller.write_digital_output(WINDINGS_CHANNEL,WINDINGS_STATE_OFF)
            else:
                raise ValueError, "'state' must be 'on' or 'off'"
        
    def query_band(self):
        return self.band
        
    def select_band(self, band):
        """switches betwen the 'H2O' and 'O2A' bands, windings are
           always set 'off' upon completion (even during an error state)
        """
        try:
            if not band in ['O2A','H2O']:
                raise ValueError, "'band' must be 'H2O' or 'O2A'"
            #get the device
            band_motor = self.devices['band_motor']
            #ensure windings are on
            self.set_windings('on')
            with band_motor.motor_controller._mutex:
                band_motor.configure_limit_sensors(sensor_mode=2) # 2 sensor mode
                if band == 'O2A':   #system is driven CCW to Limit
                    band_motor.seek_home('CCW')
                elif band == 'H2O':     #system is driven CW to Limit
                    band_motor.seek_home('CW')
                #in no band while moving
                self.band = None
                #wait until moving stops
                band_motor.wait_on_move()
                #moving completed, take on band state
                self.band = band
        finally: 
            #ensure that windings are always in left off state, even during exception
            self.set_windings('off')
           
    
#    def fine_adjust(self, steps, adjust_speed = None):
#        """uses the bands picomotor driver to finely adjust the diffraction grating"""
#        if adjust_speed is None:
#            adjust_speed = self.configuration['default_adjust_speed']
#        if self.band is None:
#            self.select_band('H2O')
#        picomotor = None
#        if self.band == 'H2O':
#            picomotor = self.devices['picomotorA']
#        elif self.band == 'O2A':
#            picomotor = self.devices['picomotorB']
#        picomotor.initialize()
#        picomotor.move_relative(steps, speed = adjust_speed)
#        picomotor.wait()
            
            
    def main(self):
        try:
            band = self.configuration['band']
            #send start event
            info = OrderedDict()
            info['timestamp'] = time.time()
            info['from_band'] = self.band
            info['to_band']   = band
            self._send_event("BAND_SWITCHER_SELECT_BAND_STARTED", info)
            self.select_band(band)
            #send completed event
            info = OrderedDict()
            info['timestamp'] = time.time()
            info['band']      = self.band
            self._send_event("BAND_SWITCHER_SELECT_BAND_COMPLETED", info)
        except Exception as exc:
            info = OrderedDict()
            info['timestamp'] = time.time()
            info['exception'] = exc
            self._send_event("BAND_SWITCHER_SELECT_BAND_FAILED", info)
        finally:
            #IMPORTANT!
            self.reset() #reset the controller to be used again
       
class InteractiveInterface: 
    def __init__(self,**kwargs):
        self.band = None
        self.controller = Interface(**kwargs)
        
    def set_windings(self, state = 'on'):
        "set current to windings, 'state' must be 'on' or 'off'"
        self.controller.set_windings(state)
    
    def select_band(self, band):
        """switches betwen the 'H2O' and 'O2A' bands"""
        self.controller.select_band(band)
        self.band = self.controller.band  
    
    def fine_adjust(self, steps, adjust_speed = None):
        """uses the bands picomotor driver to finely adjust the diffraction grating"""
        self.controller.fine_adjust(steps = steps,
                                    adjust_speed = adjust_speed,
                                   )
        self.band = self.controller.band
        
#------------------------------------------------------------------------------
# INTERFACE CONFIGURATOR
def get_interface(**kwargs):
    interface_mode = kwargs.pop('interface_mode','threaded')
    if   interface_mode == 'threaded':
        return Interface(**kwargs)
    elif interface_mode == 'interactive':
        return InteractiveInterface(**kwargs)
    else:
        raise ValueError("interface_mode '%s' is not valid" % interface_mode)
            
    
    
###############################################################################
# TEST CODE - Run the Controller, collect events, and plot
###############################################################################
# FIXME
if __name__ == "__main__":
    pass

