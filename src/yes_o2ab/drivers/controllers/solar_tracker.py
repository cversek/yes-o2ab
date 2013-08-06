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
        
    def thread_init(self, **kwargs):
        Controller.thread_init(self, **kwargs)
        #chain the event queues
        kwargs['event_queue'] = self.event_queue
        tracking_mirror_positioner = self.controllers['tracking_mirror_positioner']
        tracking_mirror_positioner.thread_init(**kwargs)
        
    def initialize(self, **kwargs):
        if not "thread_initialized" in self._controller_mode_set:
            self.thread_init(**kwargs)
        try:
            #get dependent devices and controllers
            solar_ephemeris = self.devices['solar_ephemeris']
            tracking_mirror_positioner = self.controllers['tracking_mirror_positioner']
            #send initialize event
            info = OrderedDict()
            info['timestamp'] = time.time()
            self._send_event("SOLAR_TRACKER_INITIALIZE_STARTED", info)
            #initialize
            self.initialize_devices()
            tracking_mirror_positioner.initialize()
            self.is_initialized = True
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
        
    def goto_zenith(self, blocking = True):
        assert self.is_initialized
        tracking_mirror_positioner = self.controllers['tracking_mirror_positioner']
        #send start event
        info = OrderedDict()
        info['timestamp'] = time.time()
        self._send_event("SOLAR_TRACKER_GOTO_ZENITH_STARTED", info)
        #ensure windings are off FIXME do we need this?
        #self.set_windings('on')
        #start tracking time
        t0 = time.time()
        tracking_mirror_positioner.goto(el_target = 90.0,
                                        blocking = blocking,
                                        )
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
        
    def goto_sun(self, seconds_ahead = 0, blocking = True):
        """goto to where the sun is predicted to be 'seconds_ahead' from now"""
        assert self.is_initialized
        solar_ephemeris = self.devices['solar_ephemeris']
        tracking_mirror_positioner = self.controllers['tracking_mirror_positioner']
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
        tracking_mirror_positioner.goto(az_target = az_future,
                                        el_target = el_future,
                                        blocking = blocking,
                                        )
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

    def main(self):
        ##get dependent devices and controllers
        solar_ephemeris = self.devices['solar_ephemeris']
        tracking_mirror_positioner = self.controllers['tracking_mirror_positioner']
        #get configuration
        control_point_interval = float(self.configuration.get('control_point_interval', CONTROL_POINT_INTERVAL_DEFAULT))
        #goto_speed             = float(self.configuration.get('goto_speed', GOTO_SPEED_DEFAULT))
        try:
            # INITIALIZE -------------------------------------------------------
            if not self.is_initialized:
                self.initialize()
            self.goto_sun()
            # START TRACKING LOOP  -----------------------------------          
            info = OrderedDict()
            info['timestamp'] = time.time()
            info['control_point_interval'] = control_point_interval
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
            import traceback
            info = OrderedDict()
            info['timestamp'] = time.time()
            info['reason']    = exc
            if not isinstance(exc, AbortInterrupt): 
                info['traceback'] = traceback.format_exc()
            self._send_event("SOLAR_TRACKER_ABORTED",info)
        finally: #Always clean up!
            #halts any moving motors
            tracking_mirror_positioner.shutdown()
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

