###############################################################################
#Dependencies
#standard python
import time, re
#Automat framework provided
from automat.core.hwcontrol.devices.instruments import Model
#3rd party hardware vendor, install from Internet


#motor control magic numbers
SPEED_MIN       = 10 #Hz
SPEED_MAX       = 200000 #Hz
SPEED_DEFAULT   = SPEED_MIN
RAMP_MODE_DEFAULT  = 'linear'
JERK_TIME_DEFAULT  = 50
STEPS_MAX          = 16777215
STEPS_MIN          = -STEPS_MAX
STEPS_DEFAULT      = 1
LIMIT_SENSOR_TRUE_DEFAULT = 0
HOME_SENSOR_TRUE_DEFAULT  = 0
SLIT_SENSOR_TRUE_DEFAULT  = 0

def constrain(val, min_val, max_val):
    if val < min_val:
        return min_val
    elif val > max_val:
        return max_val
    return val

###############################################################################
class Interface(Model):
    def __init__(self, 
                 motor_controller,
                 axis, 
                 degrees_per_step,
                 default_start_speed,
                 default_speed,
                 default_ramp_mode,
                 default_jerk_time,
                 limit_sensor_true,
                 home_sensor_true,
                 slit_sensor_true,
                ):
        #initialize GPIB communication
        self.motor_controller  = motor_controller
        self.axis              = axis
        self.degrees_per_step  = degrees_per_step
        self.default_start_speed = default_start_speed
        self.default_speed       = default_speed
        self.default_ramp_mode   = default_ramp_mode
        self.default_jerk_time   = default_jerk_time
        self._limit_sensor_true = limit_sensor_true
        self._home_sensor_true  = home_sensor_true
        self._slit_sensor_true  = slit_sensor_true
        self._limit_sensor_config = None
    #--------------------------------------------------------------------------
    # Implementation of the Instrument Interface
    def initialize(self):
        """configures the ACTL state """
        #clear errors on both axes channels
        cmd = "ACTL%d %d,%d,%d,0,0" % (self.axis,
                                       self._limit_sensor_true,
                                       self._home_sensor_true,
                                       self._slit_sensor_true,
                                      )
        self.motor_controller._send_command(cmd)
        
    def configure_limit_sensors(self,
                                sensor_mode,
                                offset_angle    = 0,
                                start_speed     = None,
                                operating_speed = None,
                                ramp_mode = None,
                                jerk_time = None,
                               ):
        self._limit_sensor_config = {}
        #sensor mode configuration
        if sensor_mode in [2,3]:
            self._limit_sensor_config['sensor_mode'] = sensor_mode
        else:
            raise ValueError, "'sensor_mode' must be 2 or 3"
        #motion configuration
        offset = int(round(offset_angle/self.degrees_per_step))
        self._limit_sensor_config['offset'] = offset
        if start_speed is None:
            start_speed = self.default_start_speed
        if operating_speed is None:
            operating_speed = self.default_speed
        if ramp_mode is None:
            ramp_mode = self.default_ramp_mode
        if jerk_time is None:
            jerk_time = self.default_jerk_time
        self._limit_sensor_config['start_speed']     = start_speed
        self._limit_sensor_config['operating_speed'] = operating_speed
        self._limit_sensor_config['ramp_mode']       = ramp_mode
        self._limit_sensor_config['jerk_time']       = jerk_time
        
    def test(self):
        soft_rev     = self.motor_controller._exchange("? SOFT")
        if not soft_rev:
            return (False, "query returned empty string")
        return (True, soft_rev)  
            
    def identify(self):
        mc_idn = self.motor_controller.identify()
        idn = "motor driver CMD2120P on axis %d of controller: %s" % (self.axis, mc_idn)
        return idn
        
    def shutdown(self):
        self.stop() #ensure that motor is not moving
        
    #--------------------------------------------------------------------------
    # Implementation of the Motor interface
    def get_position(self):
        """returns the position of the motor in degrees"""
        steps =  self.motor_controller.get_position(axis=self.axis)
        return steps*self.degrees_per_step
    
    def get_limit_state(self):
        """returns the state [01] of the limit sensors as (CWLS,CCWLS)"""
        return self.motor_controller.get_limit_state(self.axis)

    def set_home(self):
        """clears current position (set it to zero)"""
        self.motor_controller.set_home(axis=self.axis)  #p. 79

    def goto_angle(self,
                   angle,
                   direction = 'CW',
                   angular_start_speed     = None,
                   angular_operating_speed = None,
                   ramp_mode = None,
                   jerk_time = None,
                   blocking = True,
                  ):
        "move to an absolute angle (degrees), at angular speed (degrees/second)"
        #print "!!! DEBUG goto_angle, angle=",angle
        if angular_start_speed is None:
            angular_start_speed = self.default_start_speed*self.degrees_per_step
        if angular_operating_speed is None:
            angular_operating_speed = self.default_speed*self.degrees_per_step
        if ramp_mode is None:
            ramp_mode = self.default_ramp_mode
        if jerk_time is None:
            jerk_time = self.default_jerk_time
        #compute step position and step speed from angle
        pos = int(round(angle/self.degrees_per_step))
        start_speed     = int(round(angular_start_speed/self.degrees_per_step))
        operating_speed = int(round(angular_operating_speed/self.degrees_per_step)) 
        self.motor_controller.goto_position(
                                            axis = self.axis,
                                            pos = pos,
                                            direction = direction,
                                            start_speed     = start_speed,
                                            operating_speed = operating_speed,
                                            ramp_mode = ramp_mode,
                                            jerk_time = jerk_time,
                                           )
        if blocking:
            self.wait_on_move()
        #send back the actual angle for the closest position
        return pos*self.degrees_per_step
    
    def rotate(self,
               angle,
               angular_start_speed     = None, 
               angular_operating_speed = None,
               ramp_mode = None,
               jerk_time = None,
               blocking = True,
              ):
        "move by an angle (degrees) relative to current position, at angular speed (degrees/second)"
        if angular_start_speed is None:
            angular_start_speed = self.default_speed*self.degrees_per_step
        if angular_operating_speed is None:
            angular_operating_speed = angular_start_speed
        if ramp_mode is None:
            ramp_mode = self.default_ramp_mode
        if jerk_time is None:
            jerk_time = self.default_jerk_time
        #compute steps and step speed from angle
        steps = int(round(angle/self.degrees_per_step))
        start_speed     = int(round(angular_start_speed/self.degrees_per_step))
        operating_speed = int(round(angular_operating_speed/self.degrees_per_step))
        self.motor_controller.rotate(
                                     axis  = self.axis,
                                     steps = steps,
                                     start_speed     = start_speed,
                                     operating_speed = operating_speed,
                                     ramp_mode = ramp_mode,
                                     jerk_time = jerk_time,
                                    )
        if blocking:
            self.wait_on_move()
        #send back the actual angle that was rotated
        return steps*self.degrees_per_step
        
    def seek_home(self,
                  direction,
                  blocking = True
                 ):
        #print "!!! DEBUG seek_home, direction =", direction
        if self._limit_sensor_config is None:
            raise RuntimeError, "user must first call 'configure_limit_sensors'"
        self._limit_sensor_config['axis']      = self.axis
        self._limit_sensor_config['direction'] = direction
        self.motor_controller.seek_home(**self._limit_sensor_config)
        if blocking:
            self.wait_on_move()
    
    def is_moving(self):
        return self.motor_controller.is_moving()
    
    def wait_on_move(self):
        self.motor_controller.wait_on_move()
        
    def stop(self):
        self.motor_controller.stop(self.axis)    
    

#--------------------------------------------------------------------------
#      

#------------------------------------------------------------------------------
# INTERFACE CONFIGURATOR         
def get_interface(motor_controller, 
                  axis, 
                  degrees_per_step,
                  default_start_speed = None,
                  default_speed       = None,
                  default_ramp_mode   = None,
                  default_jerk_time   = None,
                  limit_sensor_true   = None,
                  home_sensor_true    = None,
                  slit_sensor_true    = None,
                  ):
    axis = int(axis)
    degrees_per_step = float(degrees_per_step)
    
    if default_start_speed is None:
        default_start_speed = SPEED_DEFAULT
    else:
        default_start_speed = int(default_start_speed)
    
    if default_speed is None:
        default_speed = SPEED_DEFAULT
    else:
        default_speed = int(default_speed)
    
    if default_ramp_mode is None:
        default_ramp_mode = RAMP_MODE_DEFAULT
    elif not default_ramp_mode in ['linear','limit jerk']:
        raise ValueError("'default_ramp_mode' must be either 'linear' or 'limit jerk'")
    
    if default_jerk_time is None:
        default_jerk_time = JERK_TIME_DEFAULT
    else:
        default_jerk_time = int(default_jerk_time)
    
    if limit_sensor_true is None:
        limit_sensor_true = LIMIT_SENSOR_TRUE_DEFAULT
    else:
        limit_sensor_true = int(bool(int(limit_sensor_true)))
    
    if home_sensor_true is None:
        home_sensor_true = HOME_SENSOR_TRUE_DEFAULT
    else:
        home_sensor_true = int(bool(int(home_sensor_true)))
    
    if slit_sensor_true is None:
        slit_sensor_true = SLIT_SENSOR_TRUE_DEFAULT
    else:
        slit_sensor_true = int(bool(int(slit_sensor_true)))
    
    return Interface(motor_controller    = motor_controller,
                     axis                = axis,
                     degrees_per_step    = degrees_per_step,
                     default_start_speed = default_start_speed,
                     default_speed       = default_speed,
                     default_ramp_mode   = default_ramp_mode,
                     default_jerk_time   = default_jerk_time,
                     limit_sensor_true   = limit_sensor_true,
                     home_sensor_true    = home_sensor_true,
                     slit_sensor_true    = slit_sensor_true,
                    )
    
###############################################################################
# TEST CODE
###############################################################################
if __name__ == "__main__":
    iface = Interface()
