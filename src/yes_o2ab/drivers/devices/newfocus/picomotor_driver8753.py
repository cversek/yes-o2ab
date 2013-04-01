###############################################################################
#Dependencies
#standard python
import time
#Automat framework provided
from automat.core.hwcontrol.devices.instruments import Model
#other in-house packages
from Ldcn.network import Network
#3rd party hardware vendor, install from Internet
###############################################################################
#module constants
IDN = "New Focus Intelligent Picomotor Driver 8753"
DEFAULT_BAUDRATE = 19200
SPEED_DEFAULT    = 1
ACC_DEFAULT      = 1
DEFAULT_POLLING_INTERVAL = 0.1 #seconds
#motor control magic numbers
SPEED_MIN       = 1    #Hz
SPEED_MAX       = 2000 #Hz
SPEED_DEFAULT   = SPEED_MIN
SPEED_FACTOR_SIZE = 250

def constrain(val, min_val, max_val):
    if val < min_val:
        return min_val
    elif val > max_val:
        return max_val
    return val

###############################################################################
class Interface(Model):
    def __init__(self, port, addr, baudrate):
        self.addr = addr        
        self._ldcn = Network(port=port, baudrate=baudrate)
        self._stepper_mod = None
        self._initialized = False
        self._current_channel = None    
    #--------------------------------------------------------------------------
    # Implementation of the Instrument Interface
    def initialize(self):
        """ """
        if not self._initialized:
            self._ldcn.initialize()
            self._stepper_mod = self._ldcn.getModule(self.addr)
        self._initialized = True
        
    def test(self):
        return (True, "")  
            
    def identify(self):
        buff = [IDN]
        buff.append("\taddr = %d" %  self.addr)
        if self._initialized:
            buff.append("\tmod_type = %d" % self._stepper_mod.mod_type)
            buff.append("\tmod_version = %d" % self._stepper_mod.mod_version)        
        else:
            buff.append("\t(not initialized)")        
        return "\n".join(buff)

    #--------------------------------------------------------------------------
    # Implementation of the Picomotor Motion Interface
    def get_position(self):
        self.initialize()
        return self._stepper_mod.getPosition()

    def goto_position(self,
                      channel,
                      pos, 
                      speed = SPEED_DEFAULT, 
                      acc   = ACC_DEFAULT,
                      ):
        self.initialize()
        #set up the driver
        self.stop_motion()
        self._stepper_mod.setOutputs(channel) #set the motor channel
        #recalculate the speed with the multiplier        
        speed = constrain(speed,SPEED_MIN,SPEED_MAX)        
        speed_factor = 1.0
        if   speed <= 1.0*SPEED_FACTOR_SIZE:
            pass
        elif speed <= 2.0*SPEED_FACTOR_SIZE:   
            speed_factor = 2.0
        elif speed <= 4.0*SPEED_FACTOR_SIZE:   
            speed_factor = 4.0
        elif speed <= 8.0*SPEED_FACTOR_SIZE:   
            speed_factor = 8.0
        speed = int(speed/speed_factor)
        speed_factor = int(speed_factor)
        self._stepper_mod.setParams(speed_factor='%dx' % speed_factor)
        #self._stepper_mod.resetPosition()
        self._stepper_mod.enableDriver()
        self._stepper_mod.loadTrajectory(pos=pos,speed=speed,acc=acc)

    def stop_motion(self):
        self._stepper_mod.stopMotor(stop_mode = 'abrupt')
    
    def wait(self, polling_interval = DEFAULT_POLLING_INTERVAL):
        while True:
            if not self._stepper_mod.isMotorMoving():
                break
            time.sleep(polling_interval)
            
        
    #--------------------------------------------------------------------------
            
            
    #--------------------------------------------------------------------------
      

#------------------------------------------------------------------------------
# INTERFACE CONFIGURATOR         
def get_interface(port, addr, baudrate = DEFAULT_BAUDRATE):
    addr     = int(addr)    
    baudrate = int(baudrate)
    return Interface(port=port, addr=addr, baudrate=baudrate)
    
###############################################################################
# TEST CODE
###############################################################################
if __name__ == "__main__":
    d = get_interface(port="ttyS0", addr=1)
