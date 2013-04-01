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
CONTROL_POINT_INTERVAL_DEFAULT = 120 #seconds
GOTO_SPEED_DEFAULT = 10 #degrees per second
###############################################################################
class Interface(Controller):
    def __init__(self,**kwargs):
        self.band = None
        Controller.__init__(self, **kwargs)
    
    def main(self):
        #get dependent devices and controllers
        solar_ephemeris = self.devices['solar_ephemeris']
        el_motor = self.devices['el_motor']
        az_motor = self.devices['az_motor']
        #get configuration
        control_point_interval = float(self.configuration.get('control_point_interval', CONTROL_POINT_INTERVAL_DEFAULT))
        goto_speed             = float(self.configuration.get('goto_speed', GOTO_SPEED_DEFAULT))
        try:
            # START TRACKING LOOP  -----------------------------------          
            #initialize motor devices
            el_motor.initialize()
            az_motor.initialize()
            #FIXME -goto the home position, for now just use starting state
            el_motor.set_home()
            az_motor.set_home()
            #goto the current location 
            jd_now, el_now, az_now = solar_ephemeris.update()
            el_motor.goto_angle(el_now, angular_start_speed = goto_speed)
            az_motor.goto_angle(az_now, angular_start_speed = goto_speed)
            el_motor.wait_on_move()
            az_motor.wait_on_move()
            info = OrderedDict()
            info['timestamp'] = time.time()
            info['control_point_interval'] = control_point_interval
            info['goto_speed'] = goto_speed
            info['jd_now'] = jd_now
            info['el_now'] = el_now
            info['az_now'] = az_now
            self._send_event("SOLAR_TRACKER_STARTED",info)
            while True:
                self._thread_abort_breakout_point()
                t0 = time.time()
                #get current sun location
                jd_now, el_now, az_now = solar_ephemeris.update()
                #predict where sun will be at next control point
                jd_future, el_future, az_future = solar_ephemeris.predict(control_point_interval, jd_now)
                #compute the change and speed of the angular coordinates
                delta_el = el_future - el_now
                delta_az = az_future - az_now
                track_speed_el = abs(delta_el)/control_point_interval #degrees per second
                track_speed_az = abs(delta_az)/control_point_interval #degrees per second
                #FIXME - #break trajectory into single steps
                #delta_el_steps = int(round(delta_el/el_motor.degrees_per_step))
                #delta_az_steps = int(round(delta_az/az_motor.degrees_per_step))
                #track_speed_el_steps = int(round(track_speed_el/el_motor.degrees_per_step))
                #track_speed_az_steps = int(round(delta_az/az_motor.degrees_per_step))
                #start the motor trajectory, call does not block
                el_motor.goto_angle(el_future, angular_start_speed = track_speed_el)
                az_motor.goto_angle(az_future, angular_start_speed = track_speed_az)
                t1 = time.time()
                used_t = t1-t0
                #send information
                info = OrderedDict()
                info['timestamp']   = time.time()
                info['jd_now'] = jd_now
                info['el_now'] = el_now
                info['az_now'] = az_now
                info['delta_el'] = delta_el
                info['delta_az'] = delta_az
                info['track_speed_el'] = track_speed_el
                info['track_speed_az'] = track_speed_az
                info['used_t']   = used_t
                self._send_event("SOLAR_TRACKER_CONTROL_POINT",info)
                self._thread_abort_breakout_point()
                # SLEEP UNTIL NEXT CYCLE  ----------------------------
                self.sleep(control_point_interval - used_t)
                #check if client requests stop
                if self._thread_check_stop_event():
                    # END NORMALLY -----------------------------------
                    info = OrderedDict()
                    info['timestamp'] = time.time()
                    self._send_event("SOLAR_TRACKER_STOPPED",info)
                    return
        except (AbortInterrupt, Exception), exc:
            # END ABNORMALLY -----------------------------------------
            import traceback
            info = OrderedDict()
            info['timestamp'] = time.time()
            info['reason']    = exc
            if not isinstance(exc, AbortInterrupt): 
                info['traceback'] = traceback.format_exc()
            self._send_event("SOLAR_TRACKER_ABORTED",info)
        finally: #Always clean up!
            pass
            #halts any moving motors
            #el_motor.shutdown()
            #az_motor.shutdown()
       
class InteractiveInterface: 
    def __init__(self,**kwargs):
        self.band = None
        self.controller = Interface(**kwargs)
        
            
def get_interface(interface_mode = 'threaded', **kwargs):
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

