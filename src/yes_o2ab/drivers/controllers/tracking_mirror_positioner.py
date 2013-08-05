"""
Controller to track elevation and azimuth of the sun and to steer the collimator
on the O2ab spectrometer
"""
###############################################################################
import time, copy, warnings
from automat.core.hwcontrol.controllers.controller import Controller, AbortInterrupt, NullController

try:
    from collections import OrderedDict
except ImportError:
    from yes_o2ab.support.odict import OrderedDict
###############################################################################
CONTROL_POINT_INTERVAL_DEFAULT = 60
###############################################################################
class Interface(Controller):
    def __init__(self,**kwargs):
        self.az_pos = None
        self.el_pos = None
        self.az_target = None
        self.el_target = None
        self.is_initialized = False
        Controller.__init__(self, **kwargs)
        
    def initialize(self):
        """Initialize motors and seek the home position.
        """
        try:
            #get dependent devices and controllers
            el_motor = self.devices['el_motor']
            az_motor = self.devices['az_motor']
            #send initialize event
            info = OrderedDict()
            info['timestamp'] = time.time()
            self._send_event("TRACKING_MIRROR_POSITIONER_INITIALIZE_STARTED", info)
            #initialize motor devices
            self.initialize_devices()
            el_motor.configure_limit_sensors(sensor_mode=2) # 2 sensor mode
            az_motor.configure_limit_sensors(sensor_mode=2) # 2 sensor mode
            self.is_initialized = True
            self.seek_home()
            #ensure windings are off FIXME do we need this?
            #self.set_windings('on')
            #end initialize normally
            info = OrderedDict()
            info['timestamp'] = time.time()
            self._send_event("TRACKING_MIRROR_POSITIONER_INITIALIZE_COMPLETED", info)
        except RuntimeError, exc: #can't get mutex locks (thread or process level)
            #send initialize end
            info = OrderedDict()
            info['timestamp'] = time.time()
            info['exception'] = exc
            self._send_event("TRACKING_MIRROR_POSITIONER_INITIALIZE_FAILED", info)
        finally:
            pass
            #ensure windings are off
            #self.set_windings('off')
            
    def seek_home(self):
        assert self.is_initialized
        az_motor = self.devices['az_motor']
        el_motor = self.devices['el_motor']
        #get configuration
        az_home_pos = float(self.configuration['az_home_pos'])
        el_home_pos = float(self.configuration['el_home_pos'])
        #send start event
        info = OrderedDict()
        info['timestamp'] = time.time()
        self._send_event("TRACKING_MIRROR_POSITIONER_SEEK_HOME_STARTED", info)
        #ensure windings are off FIXME do we need this?
        #self.set_windings('on')
        #must do elevation first, so snorkel doesn't swing azimuth at wide angle
        #these actions should be blocking
        with el_motor.motor_controller._mutex:
            el_motor.seek_home("CW") 
            el_motor.set_home()       #sets motor's ref. pos to zero
        with az_motor.motor_controller._mutex:
            az_motor.seek_home("CCW")
            az_motor.set_home()       #sets motor's ref. pos to zero
        self.el_pos = el_home_pos     #convert to sky coordinates
        self.az_pos = az_home_pos     #convert to sky coordinates
        #end event
        self.is_initialized = True
        info = OrderedDict()
        info['timestamp'] = time.time()
        info['az_pos'] = self.az_pos
        info['el_pos'] = self.el_pos
        self._send_event("TRACKING_MIRROR_POSITIONER_SEEK_HOME_COMPLETED", info)
        
    def _goto_az_angle(self, angle, blocking = True, **kwargs):
        assert self.is_initialized
        az_motor = self.devices['az_motor']
        az_home_pos = float(self.configuration['az_home_pos'])
        motor_angle = angle - az_home_pos
        az_motor.goto_angle(motor_angle, **kwargs)
        #query the motor for the position
        new_motor_angle = az_motor.get_position()
        self.az_pos = new_motor_angle + az_home_pos
        return self.az_pos
        
    def _goto_el_angle(self, angle, **kwargs):
        assert self.is_initialized
        el_motor = self.devices['el_motor']
        el_home_pos = float(self.configuration['el_home_pos'])
        motor_angle = angle - el_home_pos
        el_motor.goto_angle(motor_angle, **kwargs)
        #query the motor for the position
        new_motor_angle = el_motor.get_position()
        self.el_pos = new_motor_angle + el_home_pos
        return self.el_pos
        
#    def set_windings(self, state = 'on'):
#        "set current to windings, 'state' must be 'on' or 'off'"
#        az_motor = self.devices['az_motor']
#        el_motor = self.devices['el_motor']
#        with az_motor.motor_controller._mutex:
#            if state == 'on':
#                az_motor.motor_controller.write_digital_output(WINDINGS_CHANNEL,WINDINGS_STATE_ON)
#            elif state == 'off':
#                az_motor.motor_controller.write_digital_output(WINDINGS_CHANNEL,WINDINGS_STATE_OFF)
#            else:
#                raise ValueError, "'state' must be 'on' or 'off'"
#   
    def goto(self, az_target = None, el_target = None, blocking = False, **kwargs):
        self.az_target = az_target
        self.el_target = el_target
        self.thread_init(**kwargs) #gets the threads working
        if blocking:
            self.run()
        else:
            self.start()
        
    def main(self):
        ##get dependent devices and controllers
        el_motor = self.devices['el_motor']
        az_motor = self.devices['az_motor']
        #get configuration
        el_home_pos = float(self.configuration['el_home_pos'])
        az_home_pos = float(self.configuration['az_home_pos'])
        update_query_delay = float(self.configuration['update_query_delay'])
        #goto_speed             = float(self.configuration.get('goto_speed', GOTO_SPEED_DEFAULT))
        #get current target parameters
        el_target = self.el_target
        az_target = self.az_target
        try:
            # INITIALIZE -------------------------------------------------------
            if not self.is_initialized:
                self.initialize()
            # START TRACKING LOOP  -----------------------------------          
            info = OrderedDict()
            info['timestamp'] = time.time()
            info['el_target'] = el_target
            info['az_target'] = az_target
            self._send_event("TRACKING_MIRROR_POSITIONER_STARTED",info)
            self._thread_abort_breakout_point()
            #move the motors simultaneously
            el_motor_angle = el_target - el_home_pos
            az_motor_angle = az_target - az_home_pos
            el_motor.goto_angle(el_motor_angle, blocking = False)
            az_motor.goto_angle(az_motor_angle, blocking = False)
            while el_motor.is_moving() or az_motor.is_moving():
                self._thread_abort_breakout_point()
                self.sleep(update_query_delay)
                self._thread_abort_breakout_point()
                #query the motors for their positions
                el_new_motor_angle = el_motor.get_position()
                self.el_pos = el_new_motor_angle + el_home_pos
                self._thread_abort_breakout_point()
                az_new_motor_angle = az_motor.get_position()
                self.az_pos = az_new_motor_angle + az_home_pos
                info = OrderedDict()
                info['timestamp'] = time.time()
                info['el_pos']    = self.el_pos
                info['az_pos']    = self.az_pos
                self._send_event("TRACKING_MIRROR_POSITIONER_UPDATE",info)
            # END NORMALLY -----------------------------------
            info = OrderedDict()
            info['timestamp'] = time.time()
            self._send_event("TRACKING_MIRROR_POSITIONER_STOPPED",info)
            return
        except (AbortInterrupt, Exception), exc:
            # END ABNORMALLY -----------------------------------------
            self.az_pos = None
            self.el_pos = None
            import traceback
            info = OrderedDict()
            info['timestamp'] = time.time()
            info['reason']    = exc
            if not isinstance(exc, AbortInterrupt): 
                info['traceback'] = traceback.format_exc()
            self._send_event("TRACKING_MIRROR_POSITIONER_ABORTED",info)
        finally: #Always clean up!
            #halts any moving motors
            el_motor.shutdown()
            az_motor.shutdown()
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

