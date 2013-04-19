"""
Controller to switch the O2ab spectrometer between A (oxygen A) and B (water )
and to finely adjust the diffraction grating position
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
    ("band",None),
])

###############################################################################
class Interface(Controller):
    def __init__(self,**kwargs):
        self.band = None
        #kwargs.get(
        Controller.__init__(self, **kwargs)
        
    def initialize(self):
        band_motor = self.devices['band_motor']
        band_motor.motor_controller.initialize()
        #ensure windings are off
        self.set_windings('off')
    
    def set_windings(self, state = 'on'):
        "set current to windings, 'state' must be 'on' or 'off'"
        band_motor = self.devices['band_motor']
        if state == 'on':
            band_motor.motor_controller.write_digital_output(1,0)
        elif state == 'off':
            band_motor.motor_controller.write_digital_output(1,1)
        else:
            raise ValueError, "'state' must be 'on' or 'off'"
        
        
    def select_band(self, band):
        """switches betwen the 'H2O' and 'O2A' bands, windings are
           always set 'off' upon completion (even during an error state)
        """
        if not band in ['O2A','H2O']:
            raise ValueError, "'band' must be 'H2O' or 'O2A'"
        #configure the devices
        band_motor = self.devices['band_motor']
        try:
            #send start event
            info = OrderedDict()
            info['timestamp'] = time.time()
            info['from_band'] = self.band
            info['to_band']   = band
            self._send_event("BAND_SWITCHER_SELECT_BAND_STARTED", info)
            band_motor.initialize()
            #ensure windings are on
            self.set_windings('on')
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
            #send completed event
            info = OrderedDict()
            info['timestamp'] = time.time()
            info['band']      = self.band
            self._send_event("BAND_SWITCHER_SELECT_BAND_COMPLETED", info)        
        finally: 
            #ensure that windings are always in left off state, even during exception
            self.set_windings('off')
           
    
    def fine_adjust(self, steps, adjust_speed = None):
        """uses the bands picomotor driver to finely adjust the diffraction grating"""
        if adjust_speed is None:
            adjust_speed = self.configuration['default_adjust_speed']
        if self.band is None:
            self.select_band('H2O')
        picomotor = None
        if self.band == 'H2O':
            picomotor = self.devices['picomotorA']
        elif self.band == 'O2A':
            picomotor = self.devices['picomotorB']
        picomotor.initialize()
        picomotor.move_relative(steps, speed = adjust_speed)
        picomotor.wait()
            
            
    def main(self):
        band = self.configuration['band']
        if band is None:
            return
        else:
            self.select_band(band)
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
            
def get_interface(**kwargs):
    interface_mode = kwargs.pop('interface_mode','threaded')
    if   interface_mode == 'threaded':
        return Interface(**kwargs)
    elif interface_mode == 'interactive':
        return InteractiveInterface(**kwargs)
            
    
    
###############################################################################
# TEST CODE - Run the Controller, collect events, and plot
###############################################################################
# FIXME
if __name__ == "__main__":
    pass

