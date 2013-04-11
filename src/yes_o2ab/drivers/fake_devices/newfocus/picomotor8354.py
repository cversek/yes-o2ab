###############################################################################
#Dependencies
#standard python
import time, re
#Automat framework provided
from automat.core.hwcontrol.devices.instruments import Model
#other in-house packages
from Ldcn.network import Network
#3rd party hardware vendor, install from Internet

DEFAULT_BAUDRATE = 19200
SPEED_DEFAULT    = 1
ACC_DEFAULT      = 1
###############################################################################
class Interface(Model):
    def __init__(self, channel, driver):
        self.channel = channel
        self._driver = driver 
        self._initialized = False   
    #--------------------------------------------------------------------------
    # Implementation of the Instrument Interface
    def initialize(self):
        """ """
        if not self._initialized:
            self._driver.initialize()
        self._initialized = True
        
    def test(self):
        return (True, "")  
            
    def identify(self):
        buff = ["New Focus Intelligent Pico Motor 8354"]
        buff.append("\taddr = %d" % self._driver.addr)
        buff.append("\tchannel = %s" % self.channel)        
        if self._initialized:
            buff.append("\tmod_type = %d" % self._stepper_mod.mod_type)
            buff.append("\tmod_version = %d" % self._stepper_mod.mod_version)        
        else:
            buff.append("(not initialized)")        
        return "\n".join(buff)

    #--------------------------------------------------------------------------
    # Implementation of the Motor Interface
    def get_position(self):
        self.initialize()
        return self._driver.get_position()

    def goto_position(self,
                      pos, 
                      speed = SPEED_DEFAULT, 
                      acc   = ACC_DEFAULT,
                      ):
        self.initialize()
        self._driver.goto_position(self.channel,pos=pos,speed=speed,acc=acc)
    
    def move_relative(self,
                      steps, 
                      speed = SPEED_DEFAULT, 
                      acc   = ACC_DEFAULT,
                      ):
        self.initialize()
        pos = self.get_position()
        pos += steps
        self._driver.goto_position(self.channel,pos=pos,speed=speed,acc=acc)
    
    def stop_motion(self):
        self._driver.stop_motion()
        
    def wait(self):
        self._driver.wait()
    #--------------------------------------------------------------------------
        
    #--------------------------------------------------------------------------
      

#------------------------------------------------------------------------------
# INTERFACE CONFIGURATOR         
def get_interface(channel, driver):
    return Interface(channel=channel, driver=driver)
    
###############################################################################
# TEST CODE
###############################################################################
if __name__ == "__main__":
    pass
