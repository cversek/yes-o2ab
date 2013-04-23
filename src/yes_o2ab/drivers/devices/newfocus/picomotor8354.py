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
DEFAULT_SPEED    = 10
DEFAULT_ACC      = 1
###############################################################################
class Interface(Model):
    def __init__(self, channel, driver, 
                 default_speed = DEFAULT_SPEED, 
                 default_acc   = DEFAULT_ACC,
                ):
        self.channel = channel
        self._driver = driver
        self.default_speed = default_speed
        self.default_acc   = default_acc 
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
                      speed = None, 
                      acc   = None,
                      blocking = True,
                      ):
        if speed is None:
            speed = self.default_speed
        if acc is None:
            acc = self.default_acc    
        self.initialize()
        self._driver.goto_position(self.channel,pos=pos,speed=speed,acc=acc)
        if blocking:
            self.wait()
    
    def move_relative(self,
                      steps, 
                      speed = None, 
                      acc   = None,
                      blocking = True,
                      ):
        if speed is None:
            speed = self.default_speed
        if acc is None:
            acc = self.default_acc 
        self.initialize()
        pos = self.get_position()
        pos += steps
        self._driver.goto_position(self.channel,pos=pos,speed=speed,acc=acc)
        if blocking:
            self.wait()
    
    def stop_motion(self):
        self._driver.stop_motion()
        
    def wait(self):
        self._driver.wait()
    #--------------------------------------------------------------------------
        
    #--------------------------------------------------------------------------
      

#------------------------------------------------------------------------------
# INTERFACE CONFIGURATOR         
def get_interface(channel, driver, **kwargs):
    return Interface(channel=channel, driver=driver, **kwargs)
    
###############################################################################
# TEST CODE
###############################################################################
if __name__ == "__main__":
    pass
