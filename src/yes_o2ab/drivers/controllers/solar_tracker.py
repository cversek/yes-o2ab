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
        self.is_initialized = False
        Controller.__init__(self, **kwargs)
        
    def initialize(self):
        if self.is_initialized:
            return
        try:
            #get dependent devices and controllers
            solar_ephemeris = self.devices['solar_ephemeris']
            el_motor = self.devices['el_motor']
            az_motor = self.devices['az_motor']
            #send initialize event
            info = OrderedDict()
            info['timestamp'] = time.time()
            self._send_event("SOLAR_TRACKER_INITIALIZE_STARTED", info)
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
            self._send_event("SOLAR_TRACKER_INITIALIZE_COMPLETED", info)
        except RuntimeError, exc: #can't get mutex locks (thread or process level)
            #send initialize end
            info = OrderedDict()
            info['timestamp'] = time.time()
            info['exception'] = exc
            self._send_event("SOLAR_TRACKER_INITIALIZE_FAILED", info)
        finally:
            pass
            #ensure windings are off
            #self.set_windings('off')
            
    def seek_home(self):
        assert self.is_initialized
        #send start event
        info = OrderedDict()
        info['timestamp'] = time.time()
        self._send_event("SOLAR_TRACKER_SEEK_HOME_STARTED", info)
        #ensure windings are off FIXME do we need this?
        #self.set_windings('on')
        self._seek_el_home()  #must do first, so snorkel doesn't swing azimuth at wide angle
        self._seek_az_home()
        #end event
        self.is_initialized = True
        info = OrderedDict()
        info['timestamp'] = time.time()
        info['az_pos'] = self.az_pos
        info['el_pos'] = self.el_pos
        self._send_event("SOLAR_TRACKER_SEEK_HOME_COMPLETED", info)
        
    def goto_zenith(self):
        assert self.is_initialized
        #send start event
        info = OrderedDict()
        info['timestamp'] = time.time()
        self._send_event("SOLAR_TRACKER_GOTO_ZENITH_STARTED", info)
        #ensure windings are off FIXME do we need this?
        #self.set_windings('on')
        #start tracking time
        t0 = time.time()
        self.goto_el_angle(90) #straight up
        t1 = time.time()
        used_t = t1-t0
        #end event
        self.is_initialized = True
        info = OrderedDict()
        info['timestamp'] = time.time()
        info['az_pos']    = self.az_pos
        info['el_pos']    = self.el_pos
        info['used_time'] = used_t
        self._send_event("SOLAR_TRACKER_GOTO_ZENITH_COMPLETED", info)
        return used_t
        
    def goto_sun(self, seconds_ahead = 0):
        """goto to where the sun is predicted to be 'seconds_ahead' from now"""
        assert self.is_initialized
        #get the position of the sun from the ephemeris
        solar_ephemeris = self.devices['solar_ephemeris']
        #self.set_windings('on')
        #start tracking time
        t0 = time.time()
        #get current sun location
        jd_now, el_now, az_now = solar_ephemeris.update()
        #predict where sun will be at next control point
        jd_future, el_future, az_future = solar_ephemeris.predict(seconds_ahead, jd_now)
        #send start event
        info = OrderedDict()
        info['timestamp'] = t0
        info['seconds_ahead'] = seconds_ahead
        info['jd_now']    = jd_now
        info['az_now']    = az_now
        info['el_now']    = el_now
        info['jd_future'] = jd_future
        info['az_future'] = az_future
        info['el_future'] = el_future
        self._send_event("SOLAR_TRACKER_GOTO_SUN_STARTED", info)
        #ensure windings are off FIXME do we need this?
        self._goto_az_angle(az_future)
        self._goto_el_angle(el_future)
        t1 = time.time()
        used_t = t1-t0
        #send end event
        info = OrderedDict()
        info['timestamp'] = t1
        info['az_pos']    = self.az_pos
        info['el_pos']    = self.el_pos
        info['used_time'] = used_t
        self._send_event("SOLAR_TRACKER_GOTO_SUN_COMPLETED", info)
        return used_t
        
    def _seek_az_home(self):
        assert self.is_initialized
        az_motor = self.devices['az_motor']
        az_home_pos = float(self.configuration['az_home_pos'])
        with az_motor.motor_controller._mutex:
            az_motor.seek_home("CCW")
            az_motor.set_home()       #sets motor's ref. pos to zero
        self.az_pos = az_home_pos     #convert to sky coordinates
            
    def _seek_el_home(self):
        assert self.is_initialized
        el_motor = self.devices['el_motor']
        el_home_pos = float(self.configuration['el_home_pos'])
        with el_motor.motor_controller._mutex:
            el_motor.seek_home("CW") 
            el_motor.set_home()       #sets motor's ref. pos to zero
        self.el_pos = el_home_pos     #convert to sky coordinates
        
    def _goto_az_angle(self, angle, **kwargs):
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
    def start_tracking(self, blocking = False, **kwargs):
        if blocking:
            self.run()
        else:
            self.thread_init(**kwargs) #gets the threads working
            self.start()
        
    def main(self):
        ##get dependent devices and controllers
        solar_ephemeris = self.devices['solar_ephemeris']
        el_motor = self.devices['el_motor']
        az_motor = self.devices['az_motor']
        #get configuration
        control_point_interval = float(self.configuration.get('control_point_interval', CONTROL_POINT_INTERVAL_DEFAULT))
        #goto_speed             = float(self.configuration.get('goto_speed', GOTO_SPEED_DEFAULT))
        try:
            # INITIALIZE -------------------------------------------------------
            self.initialize()
            self.goto_sun()
            # START TRACKING LOOP  -----------------------------------          
            info = OrderedDict()
            info['timestamp'] = time.time()
            #info['control_point_interval'] = control_point_interval
            #info['goto_speed'] = goto_speed
            self._send_event("SOLAR_TRACKER_STARTED",info)
            while True:
                self._thread_abort_breakout_point()
                #goto where the sun will be at the control point
                used_t = self.goto_sun(seconds_ahead = control_point_interval)
                self._thread_abort_breakout_point()
                # SLEEP UNTIL NEXT CYCLE  ----------------------------
                sleep_time = control_point_interval - used_t
                info = OrderedDict()
                info['timestamp']  = time.time()
                info['sleep_time'] = sleep_time
                self._send_event("SOLAR_TRACKER_SLEEPING",info)
                if sleep_time > 0.0:
                    self.sleep(sleep_time)
                #check if client requests stop
                if self._thread_check_stop_event():
                    # END NORMALLY -----------------------------------
                    info = OrderedDict()
                    info['timestamp'] = time.time()
                    self._send_event("SOLAR_TRACKER_STOPPED",info)
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
            self._send_event("SOLAR_TRACKER_ABORTED",info)
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

