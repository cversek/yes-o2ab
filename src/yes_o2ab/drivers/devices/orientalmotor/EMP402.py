###############################################################################
#Dependencies
#standard python
import time, re
#Automat framework provided
from automat.core.hwcontrol.devices.instruments import Model
#3rd party hardware vendor, install from Internet

#mixin interfaces
from automat.core.hwcontrol.communication.serial_mixin import SerialCommunicationsMixIn

PROMPT_REGEX       = re.compile("\s*0[>]\s*$")
SYNTAX_ERROR_REGEX = re.compile(r"\s+[*]\s+Syntax\s+error[.]\s+$") 

#motor control magic numbers
SPEED_MIN       = 10 #Hz
SPEED_MAX       = 200000 #Hz
SPEED_DEFAULT   = SPEED_MIN
STEPS_MAX          = 16777215
STEPS_MIN          = -STEPS_MAX
STEPS_DEFAULT      = 1
DELAY = 0.05
PROMPT_RETRY_TIME  = 0.2
RESET_SLEEP_TIME   = 1.0

def constrain(val, min_val, max_val):
    if val < min_val:
        return min_val
    elif val > max_val:
        return max_val
    return val

###############################################################################
class Interface(Model, SerialCommunicationsMixIn):
    def __init__(self, port, **kwargs):
        #initialize GPIB communication
        SerialCommunicationsMixIn.__init__(self, port, delay = DELAY, **kwargs)
#    def __del__(self):
#        self.shutdown()
    #--------------------------------------------------------------------------
    # Implementation of the Instrument Interface
    def initialize(self):
        """ """
        self._reset()
        
    def test(self):
        return (True, "")  
            
    def identify(self):
        idn = "EMP402 on port: %s" % self.ser.port
        return idn

    # Motor interface
    def get_position(self, axis):
        pattern = r"PC[12]\s+[=]\s+([+-]?\d+)"
        resp = self._exchange_command("R%d" % axis)
        m = re.search(pattern, resp)
        if not m is None:
            return int(m.group(1))
        else:
            raise IOError, "could not verify response"
            
    # Motor interface
    def get_limit_state(self, axis):
        pattern1 = r"CWLS[12]\s+[=]\s+([01])"
        pattern2 = r"CCWLS[12]\s+[=]\s+([01])"
        resp = self._exchange_command("R%d" % axis)
        m = re.search(pattern1, resp)
        if not m is None:
            CW =  int(m.group(1))
        else:
            raise IOError, "could not verify response"
        m = re.search(pattern2, resp)
        if not m is None:
            CCW = int(m.group(1))
        else:
            raise IOError, "could not verify response"
        return (CW,CCW)
        
    def is_moving(self):
        pattern = r"Move\s+[=]\s+([01])"
        resp = self._exchange_command("R")
        m = re.search(pattern, resp)
        if not m is None:
            return bool(int(m.group(1)))
        else:
            raise IOError, "could not verify response"
    
    def wait_on_move(self):
        while self.is_moving():
            pass
        return
            
    def set_home(self, axis):
        """clears current position (set it to zero)"""
        self._send_command("RTNCR%d" % axis)

    def goto_position(self,
                      axis,
                      pos,
                      direction = 'CW',
                      start_speed     = SPEED_DEFAULT,
                      operating_speed = SPEED_DEFAULT,
                      acceleration = None,
                      ramp_mode    = None,
                      jerk_time    = None,
                     ):
        self._send_command("PULSE%d 1" % axis)                     #p. 77, set pulse output mode to "1-pulse mode"
        start_speed = constrain(start_speed, SPEED_MIN, SPEED_MAX)
        #configure speed ramping
        self._send_command("VS%d %d" % (axis,start_speed))         #p. 85, start speed Hz 
        operating_speed = constrain(operating_speed, SPEED_MIN, SPEED_MAX)
        self._send_command("V%d %d" % (axis,operating_speed))      #p. 85, operating speed Hz
        if acceleration is None:
            acceleration = self.default_acceleration
        self._send_command("T%d %0.1f" % (axis,acceleration))      #p. 82, acceleration/deceleration
        if not ramp_mode is None:
            if ramp_mode == 'linear':
                self._send_command("RAMP%d 0" % (axis,))        #p. 78, ramp mode
            elif ramp_mode == 'limit jerk':
                if not jerk_time is None:
                    jerk_time = float(jerk_time)
                    self._send_command("RAMP%d 1, %0.1f" % (axis,jerk_time)) #p. 78, ramp mode
                else:
                    self._send_command("RAMP%d 1" % (axis,))    #p. 78, ramp mode
            else:
                raise ValueError("'ramp_mode' must be either 'linear' or 'limit jerk', got %s" % ramp_mode)
        #configure direction
        if direction == 'CW':
            self._send_command("H%d +" % axis)                     #p. 70, set direction flag
        elif direction == 'CCW':
            self._send_command("H%d -" % axis)                     #p. 70, set direction flag
        else:
            raise ValueError("Invalid direction '%s', must be 'CW' or 'CCW'" % direction)
        pos_sign = '+'
        if pos < 0:
            pos_sign = '-'
            pos = abs(pos)
        self._send_command("D%d %s%d" % (axis, pos_sign, pos))                 #p. 64, steps to rotate
        #start the motion, absolute
        self._send_command("ABS%d" % axis)
                
    
    def rotate(self,
               axis,
               steps           = STEPS_DEFAULT, 
               start_speed     = SPEED_DEFAULT,
               operating_speed = SPEED_DEFAULT,
               acceleration = None,
               ramp_mode    = None,
               jerk_time    = None,
              ):
        self._send_command("PULSE%d 1" % (axis,))               #p. 77, set pulse output mode to "1-pulse mode"
        start_speed = constrain(start_speed, SPEED_MIN, SPEED_MAX)
        #configure speed ramping
        self._send_command("VS%d %d" % (axis,start_speed))      #p. 85, start speed Hz 
        operating_speed = constrain(operating_speed, SPEED_MIN, SPEED_MAX)
        self._send_command("V%d %d" % (axis,operating_speed))   #p. 85, operating speed Hz
        if acceleration is None:
            acceleration = self.default_acceleration
        self._send_command("T%d %0.1f" % (axis,acceleration))      #p. 82, acceleration/deceleration
        if not ramp_mode is None:
            if ramp_mode == 'linear':
                self._send_command("RAMP%d 0" % (axis,))        #p. 78, ramp mode
            elif ramp_mode == 'limit jerk':
                if not jerk_time is None:
                    jerk_time = float(jerk_time)
                    self._send_command("RAMP%d 1, %0.1f" % (axis,jerk_time)) #p. 78, ramp mode
                else:
                    self._send_command("RAMP%d 1" % (axis,))    #p. 78, ramp mode
            else:
                raise ValueError("'ramp_mode' must be either 'linear' or 'limit jerk', got %s" % ramp_mode)
        #configure direction
        self._send_command("H%d +" % (axis,))                   #p. 70, set direction flag
        self._send_command("D%d %d" % (axis, steps))            #p. 64, steps to rotate
        #start the motion, incremental
        self._send_command("INC%d" % (axis,))
        
    def seek_home(self,
                  axis,
                  sensor_mode,
                  direction,
                  offset,
                  start_speed,
                  operating_speed,
                  acceleration = None,
                  ramp_mode    = None,
                  jerk_time    = None,
                 ):
        #sensor mode configuration
        if sensor_mode == 2:
            self._send_command("SEN%d 2" % (axis,))                #p. 81, set 2-sensor mode
        elif sensor_mode == 3:
            self._send_command("SEN%d 3" % (axis,))                #p. 81, set 3-sensor mode
        #ignore both TIM and SLIT inputs
        self._send_command("TIM%d 0,0" % (axis,))                  #p. 82, subsensor config
        #motion configuration
        self._send_command("OFS%d %d" % (axis,offset))             #p. 76, number of offset steps
        if   direction == "CW":
            self._send_command("H%d +" % (axis,))                  #p. 70, set direction flag
        elif direction == "CCW":
            self._send_command("H%d -" % (axis,))
        self._send_command("PULSE%d 1" % (axis,))                  #p. 77, set pulse output mode to "1-pulse mode"
        start_speed = constrain(start_speed, SPEED_MIN, SPEED_MAX)
        #configure speed ramping
        self._send_command("VS%d %d" % (axis,start_speed))         #p. 85, start speed Hz 
        operating_speed = constrain(operating_speed, SPEED_MIN, SPEED_MAX)
        self._send_command("V%d %d" % (axis,operating_speed))      #p. 85, operating speed Hz
        if acceleration is None:
            acceleration = self.default_acceleration
        self._send_command("T%d %0.1f" % (axis,acceleration))      #p. 82, acceleration/deceleration
        if not ramp_mode is None:
            if ramp_mode == 'linear':
                self._send_command("RAMP%d 0" % (axis,))        #p. 78, ramp mode
            elif ramp_mode == 'limit jerk':
                if not jerk_time is None:
                    jerk_time = float(jerk_time)
                    self._send_command("RAMP%d 1, %0.1f" % (axis,jerk_time)) #p. 78, ramp mode
                else:
                    self._send_command("RAMP%d 1" % (axis,))    #p. 78, ramp mode
            else:
                raise ValueError("'ramp_mode' must be either 'linear' or 'limit jerk', got %s" % ramp_mode)
        #start the mechanical home seeking
        self._send_command("MHOME%d" % axis)
    
    def stop(self, axis = None):
        if axis is None:
            self._send_command("S1")
            self._send_command("S2")
        elif axis==1:
            self._send_command("S1")
        elif axis==2:
            self._send_command("S2")
        else:
            raise ValueError("'axis' must be either 1, 2 or None (both)")
     
    def write_digital_output(self,chan,state):
        chan  = int(chan)
        assert 1 <= chan <= 6
        state = int(bool(state))
        cmd = "OUT %d,%d" % (chan,state)
        resp = self._exchange_command(cmd)
            
    #Cleanup
    def shutdown(self):
        "leave the system in a safe state"
        self.stop()
        self._reset()
        
    def _init_command_prompt(self, attempts = 5):
        for i in range(attempts):
            #initialize the prompt
            #print "!!! INIT PROMPT"
            self._send('')
            success, resp = self._read_until_prompt()
            #print "!!! INIT PROMPT RESP:", success, resp
            if success:
                return
            time.sleep(PROMPT_RETRY_TIME)
        else:
            raise IOError("could not initialize command prompt of %s in %d attempts" % (self.identify(),attempts))
    
    def _send_command(self, cmd):
        print "!!! SEND COMMAND:", cmd
        self._send(cmd)
        self.ser.flushOutput()
        
    def _exchange_command(self, cmd):
        #print "!!! EXCHANGE COMMAND:", cmd
        self.ser.flushInput()  #ignore crap in the buffer
        #self._init_command_prompt()
        self._send_command(cmd)
        time.sleep(0.5)
        success, buff = self._read_until_prompt()
        print "!!! RESP:", success,buff
        if not success:
            raise IOError, "could not verify command: %s" % cmd
        return "".join(buff)

    def _read_until_prompt(self):
        buff = []
        while True:
            line = self._read(strip_EOL = False)
            if line == "":
                return (False, buff)
            buff.append(line)
            #check for prompt
            m = PROMPT_REGEX.match(line)
            if not m is None:
                return (True, buff)
            #check for syntax error
            m = SYNTAX_ERROR_REGEX.match(line)
            if not m is None:
                raise ValueError, "bad command syntax: %s" % line
 
    def _reset(self):
        #print "!!! BEFORE RESET"
        #self._init_command_prompt()
        self._send_command("RESET\r\n")
        time.sleep(RESET_SLEEP_TIME)
        #self.ser.flushInput()  #ignore crap in the buffer
        #self.ser.flushOutput()  #ignore crap in the buffer
        #print "!!! AFTER RESET"
        #self._init_command_prompt()

    #--------------------------------------------------------------------------
      

#------------------------------------------------------------------------------
# INTERFACE CONFIGURATOR         
def get_interface(port, **kwargs):
    return Interface(port, **kwargs)
    
###############################################################################
# TEST CODE
###############################################################################
if __name__ == "__main__":
    iface = Interface(serial_number)
