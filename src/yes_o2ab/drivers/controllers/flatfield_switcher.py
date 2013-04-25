"""
Controller to switch the flatfield 
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
    ("state",None),
    ("out_angle", 91), #degrees
])
WINDINGS_CHANNEL = 2
WINDINGS_STATE_ON  = 0
WINDINGS_STATE_OFF = 1

HOME_STATE = 'in'
###############################################################################
class Interface(Controller):
    def __init__(self,**kwargs):
        self.state = None
        Controller.__init__(self, **kwargs)
        
    def initialize(self, **kwargs):
        try:
            self.thread_init(**kwargs) #gets the threads working
            flip_motor = self.devices['flip_motor']
            #send initialize start event
            info = OrderedDict()
            info['timestamp'] = time.time()
            self._send_event("FLATFIELD_SWITCHER_INITIALIZE_STARTED", info)
            with flip_motor.motor_controller._mutex:
                self.initialize_devices()
            if self.state == None:
                self.goto_home()
            self.set_state('out')
            #send initialize completed event
            info = OrderedDict()
            info['timestamp'] = time.time()
            info['state']     = self.state
            self._send_event("FLATFIELD_SWITCHER_INITIALIZE_COMPLETED", info)
        except Exception as exc: #can't get mutex locks (thread or process level)
            #send initialize end
            info = OrderedDict()
            info['timestamp'] = time.time()
            info['exception'] = exc
            self._send_event("FLATFIELD_SWITCHER_INITIALIZE_FAILED", info)
        finally:
            #ensure windings are off
            self.set_windings('off')
        
    def set_windings(self, state = 'on'):
        "set current to windings, 'state' must be 'on' or 'off'"
        flip_motor = self.devices['flip_motor']
        with flip_motor.motor_controller._mutex:
            if state == 'on':
                flip_motor.motor_controller.write_digital_output(WINDINGS_CHANNEL,WINDINGS_STATE_ON)
            elif state == 'off':
                flip_motor.motor_controller.write_digital_output(WINDINGS_CHANNEL,WINDINGS_STATE_OFF)
            else:
                raise ValueError, "'state' must be 'on' or 'off'"
    
    def goto_home(self):
        try:
            #send start event
            info = OrderedDict()
            info['timestamp'] = time.time()
            info['state']     = self.state
            self._send_event("FLATFIELD_SWITCHER_SEEKING_HOME_STARTED", info)
            #get the device
            flip_motor = self.devices['flip_motor']
            #ensure windings are on
            self.set_windings('on')
            with flip_motor.motor_controller._mutex:
                flip_motor.configure_limit_sensors(sensor_mode=2) # 2 sensor mode
                flip_motor.seek_home('CCW')
                #in no definite state while moving
                self.state = None
                #wait until moving stops
                flip_motor.wait_on_move()
                #moving completed, take on band state
                self.state = HOME_STATE
            #send completed event
            info = OrderedDict()
            info['timestamp'] = time.time()
            info['state']     = self.state
            self._send_event("FLATFIELD_SWITCHER_SEEKING_HOME_COMPLETED", info)
        finally: 
            #ensure that windings are always in left off state, even during exception
            self.set_windings('off')
                    
    def set_state(self, state = 'in'):
        """switches betwen the flatfield between states 'in' and 'out' bands, 
           windings are always set 'off' upon completion (even during an error state)
        """
        try:
            if not state in ['in','out']:
                raise ValueError, "'state' must be 'in' or 'out'"
            #get the device
            flip_motor = self.devices['flip_motor']
            out_angle  = int(self.configuration['out_angle'])
            #send start event
            info = OrderedDict()
            info['from_state'] = self.state
            info['to_state'] = state
            self._send_event("FLATFIELD_SWITCHER_SET_STATE_STARTED", info)
            #ensure windings are on
            self.set_windings('on')
            with flip_motor.motor_controller._mutex:
                flip_motor.configure_limit_sensors(sensor_mode=2) # 2 sensor mode
                if state == 'in':   #system is driven CCW to Limit
                    flip_motor.seek_home('CCW')
                elif state == 'out': #system is driven to out position
                    flip_motor.goto_angle(out_angle)
                #in no definite state while moving
                self.state = None
                #wait until moving stops
                flip_motor.wait_on_move()
                #moving completed, take on band state
                self.state = state
            #send completed event
            info = OrderedDict()
            info['timestamp'] = time.time()
            info['state']     = self.state
            self._send_event("FLATFIELD_SWITCHER_SET_STATE_COMPLETED", info)
        finally: 
            #ensure that windings are always in left off state, even during exception
            self.set_windings('off') 
            
    def main(self):
        try:
            state = self.configuration['state']
            self.set_state(state)
        except Exception as exc:
            info = OrderedDict()
            info['timestamp'] = time.time()
            info['exception'] = exc
            self._send_event("FLATFIELD_SWITCHER_SET_STATE_FAILED", info)
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

