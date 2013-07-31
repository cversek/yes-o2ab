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

###############################################################################
class Interface(Controller):
    def __init__(self,**kwargs):
        self.az_pos = None
        self.el_pos = None
        Controller.__init__(self, **kwargs)
        
    def initialize(self, **kwargs):
        try:
            self.thread_init(**kwargs) #gets the threads working
            #get dependent devices and controllers
            solar_ephemeris = self.devices['solar_ephemeris']
            el_motor = self.devices['el_motor']
            az_motor = self.devices['az_motor']
            #send initialize event
            info = OrderedDict()
            info['timestamp'] = time.time()
            self._send_event("SOLAR_TRACKER_INITIALIZE", info)
            #initialize motor devices
            el_motor.initialize()
            el_motor.configure_limit_sensors(sensor_mode=2) # 2 sensor mode
            az_motor.initialize()
            az_motor.configure_limit_sensors(sensor_mode=2) # 2 sensor mode
            self.seek_home()
            #ensure windings are off FIXME do we need this?
            #self.set_windings('on')
            
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
        self.seek_el_home()  #must do first!!!
        self.seek_az_home()
        
        
    def goto_zenith(self):
        #start tracking time
        t0 = time.time()
        self.goto_el_angle(90) #straight up
        t1 = time.time()
        used_t = t1-t0
        return used_t
        
    def goto_sun(self, seconds_ahead = 0):
        """goto to where the sun is predicted to be 'seconds_ahead' from now"""
        #get the position of the sun from the ephemeris
        solar_ephemeris = self.devices['solar_ephemeris']
        #start tracking time
        t0 = time.time()
        #get current sun location
        jd_now, el_now, az_now = solar_ephemeris.update()
        #predict where sun will be at next control point
        jd_future, el_future, az_future = solar_ephemeris.predict(seconds_ahead, jd_now)
        self.goto_az_angle(az_future)
        self.goto_el_angle(el_future)
        t1 = time.time()
        used_t = t1-t0
        return used_t
        
    def seek_az_home(self):
        az_motor = self.devices['az_motor']
        az_home_pos = float(self.configuration['az_home_pos'])
        with az_motor.motor_controller._mutex:
            az_motor.seek_home("CCW")
            az_motor.set_home()       #sets motor's ref. pos to zero
        self.az_pos = az_home_pos     #convert to sky coordinates
            
    def seek_el_home(self):
        el_motor = self.devices['el_motor']
        el_home_pos = float(self.configuration['el_home_pos'])
        with el_motor.motor_controller._mutex:
            el_motor.seek_home("CW") 
            el_motor.set_home()       #sets motor's ref. pos to zero
        self.el_pos = el_home_pos     #convert to sky coordinates
        
    def goto_az_angle(self, angle, **kwargs):
        az_motor = self.devices['az_motor']
        az_home_pos = float(self.configuration['az_home_pos'])
        motor_angle = angle - az_home_pos
        az_motor.goto_angle(motor_angle, **kwargs)
        #query the motor for the position
        new_motor_angle = az_motor.get_position()
        self.az_pos = new_motor_angle + az_home_pos
        return self.az_pos
        
    def goto_el_angle(self, angle, **kwargs):
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
#    def main(self):
#        #get dependent devices and controllers
#        solar_ephemeris = self.devices['solar_ephemeris']
#        el_motor = self.devices['el_motor']
#        az_motor = self.devices['az_motor']
#        #get configuration
#        control_point_interval = float(self.configuration.get('control_point_interval', CONTROL_POINT_INTERVAL_DEFAULT))
#        goto_speed             = float(self.configuration.get('goto_speed', GOTO_SPEED_DEFAULT))
#        try:
#            # START TRACKING LOOP  -----------------------------------          
#            #initialize motor devices
#            el_motor.initialize()
#            az_motor.initialize()
#            #FIXME -goto the home position, for now just use starting state
#            el_motor.set_home()
#            az_motor.set_home()
#            #goto the current location 
#            jd_now, el_now, az_now = solar_ephemeris.update()
#            el_motor.goto_angle(el_now, angular_start_speed = goto_speed)
#            az_motor.goto_angle(az_now, angular_start_speed = goto_speed)
#            el_motor.wait_on_move()
#            az_motor.wait_on_move()
#            info = OrderedDict()
#            info['timestamp'] = time.time()
#            info['control_point_interval'] = control_point_interval
#            info['goto_speed'] = goto_speed
#            info['jd_now'] = jd_now
#            info['el_now'] = el_now
#            info['az_now'] = az_now
#            self._send_event("SOLAR_TRACKER_STARTED",info)
#            while True:
#                self._thread_abort_breakout_point()
#                t0 = time.time()
#                #get current sun location
#                jd_now, el_now, az_now = solar_ephemeris.update()
#                #predict where sun will be at next control point
#                jd_future, el_future, az_future = solar_ephemeris.predict(control_point_interval, jd_now)
#                #compute the change and speed of the angular coordinates
#                delta_el = el_future - el_now
#                delta_az = az_future - az_now
#                track_speed_el = abs(delta_el)/control_point_interval #degrees per second
#                track_speed_az = abs(delta_az)/control_point_interval #degrees per second
#                #FIXME - #break trajectory into single steps
#                #delta_el_steps = int(round(delta_el/el_motor.degrees_per_step))
#                #delta_az_steps = int(round(delta_az/az_motor.degrees_per_step))
#                #track_speed_el_steps = int(round(track_speed_el/el_motor.degrees_per_step))
#                #track_speed_az_steps = int(round(delta_az/az_motor.degrees_per_step))
#                #start the motor trajectory, call does not block
#                el_motor.goto_angle(el_future, angular_start_speed = track_speed_el)
#                az_motor.goto_angle(az_future, angular_start_speed = track_speed_az)
#                t1 = time.time()
#                used_t = t1-t0
#                #send information
#                info = OrderedDict()
#                info['timestamp']   = time.time()
#                info['jd_now'] = jd_now
#                info['el_now'] = el_now
#                info['az_now'] = az_now
#                info['delta_el'] = delta_el
#                info['delta_az'] = delta_az
#                info['track_speed_el'] = track_speed_el
#                info['track_speed_az'] = track_speed_az
#                info['used_t']   = used_t
#                self._send_event("SOLAR_TRACKER_CONTROL_POINT",info)
#                self._thread_abort_breakout_point()
#                # SLEEP UNTIL NEXT CYCLE  ----------------------------
#                self.sleep(control_point_interval - used_t)
#                #check if client requests stop
#                if self._thread_check_stop_event():
#                    # END NORMALLY -----------------------------------
#                    info = OrderedDict()
#                    info['timestamp'] = time.time()
#                    self._send_event("SOLAR_TRACKER_STOPPED",info)
#                    return
#        except (AbortInterrupt, Exception), exc:
#            # END ABNORMALLY -----------------------------------------
#            import traceback
#            info = OrderedDict()
#            info['timestamp'] = time.time()
#            info['reason']    = exc
#            if not isinstance(exc, AbortInterrupt): 
#                info['traceback'] = traceback.format_exc()
#            self._send_event("SOLAR_TRACKER_ABORTED",info)
#        finally: #Always clean up!
#            pass
#            #halts any moving motors
#            #el_motor.shutdown()
#            #az_motor.shutdown()
       
        
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

