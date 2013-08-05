###############################################################################
#Dependencies
#standard python
import time, re
#Automat framework provided
from automat.core.hwcontrol.devices.instruments import Model
#3rd party hardware vendor, install from Internet

#mixin interfaces
from automat.core.hwcontrol.communication.serial_mixin import SerialCommunicationsMixIn

PROMPT_REGEX       = re.compile("0[>]\s*$")
SYNTAX_ERROR_REGEX = re.compile(r"\s+[*]\s+Syntax\s+error[.]\s+$") 

#motor control magic numbers
SPEED_MIN       = 10 #Hz
SPEED_MAX       = 200000 #Hz
SPEED_DEFAULT   = SPEED_MIN
STEPS_MAX          = 16777215
STEPS_MIN          = -STEPS_MAX
STEPS_DEFAULT      = 1
DELAY = 0.05
RESET_SLEEP_TIME   = 1.0

def constrain(val, min_val, max_val):
    if val < min_val:
        return min_val
    elif val > max_val:
        return max_val
    return val

###############################################################################
class Interface(Model, SerialCommunicationsMixIn):
    def __init__(self, port):
        pass
        #SerialCommunicationsMixIn.__init__(self, port, delay = DELAY)
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
        idn = "(!!! DEBUGGING FAKE) EMP402 on port: (no port)" 
        return idn

    # Motor interface
    def get_position(self, axis):
        return 0
            
    # Motor interface
    def get_limit_state(self, axis):
        return (0,0)
        
    def is_moving(self):
        return False
    
    def wait_on_move(self):
        while self.is_moving():
            pass
        return
            
    def set_home(self, axis):
        """clears current position (set it to zero)"""
        pass

    def goto_position(self,
                      axis,
                      pos,
                      direction = 'CW',
                      start_speed     = SPEED_DEFAULT,
                      operating_speed = SPEED_DEFAULT,
                     ):
        pass
                
    
    def rotate(self,
               axis,
               steps           = STEPS_DEFAULT, 
               start_speed     = SPEED_DEFAULT,
               operating_speed = SPEED_DEFAULT,
              ):
        pass
        
    def seek_home(self,
                  axis,
                  sensor_mode,
                  direction,
                  offset,
                  start_speed,
                  operating_speed,
                 ):
        pass
    
    def stop(self, axis = None):
        if axis is None:
            pass
        elif axis==1:
            pass
        elif axis==2:
            pass
        else:
            raise ValueError("'axis' must be either 1 or 2")
     
    def write_digital_output(self,chan,state):
        chan  = int(chan)
        assert 1 <= chan <= 6
        state = int(bool(state))
        cmd = "OUT %d,%d" % (chan,state)
        #do nothing
            
    #Cleanup
    def shutdown(self):
        "leave the system in a safe state"
        self.stop()
        self._reset()
    
    def _send_command(self, cmd):
        self._send(cmd)
        
    def _exchange_command(self, cmd):
        return ""

    def _read_until_prompt(self):
        return (False, "")
          
    def _reset(self):
        time.sleep(RESET_SLEEP_TIME)

    #--------------------------------------------------------------------------
      

#------------------------------------------------------------------------------
# INTERFACE CONFIGURATOR         
def get_interface(port):
    return Interface(port)
    
###############################################################################
# TEST CODE
###############################################################################
if __name__ == "__main__":
    iface = Interface(serial_number)
