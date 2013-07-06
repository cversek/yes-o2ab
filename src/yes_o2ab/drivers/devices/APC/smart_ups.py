""" automat Device object for interacting with APC "Smart" UPSes
"""
###############################################################################
#Dependencies
#standard python
import os, re
#Standard or substitute
OrderedDict = None
try:
    from collections import OrderedDict
except ImportError:
    from yes_o2ab.support.odict import OrderedDict
#3rd party provided

#Automat framework provided
from automat.core.hwcontrol.devices.device import Device
################################################################################
STATUS_COMMAND = "apcaccess status"
STATUS_FIELD_REGEX = re.compile(r"^([A-Z]+\d*)\s*[:]\s*(.*)$")
################################################################################

class Interface(Device):
    def __init__(self):
        self.last_status = None
        
    def initialize(self):
        pass

    def identify(self):
        if self.last_status is None:
            self.query_status()
        model = self.last_status['MODEL']
        return model
    
    def query_status(self):
        status = OrderedDict()
        p = os.popen(STATUS_COMMAND) #open command lined process pipe
        for line in p:
            m = STATUS_FIELD_REGEX.match(line.strip())
            if m:
                key = m.group(1)
                val = m.group(2)
                status[key] = val
            else:
                RuntimeWarning("cannot match status line: %s" % line)
        self.last_status = status
        return status
        
    def shutdown(self):
        pass 
        
#-------------------------------------------------------------------------------
# INTERFACE CONFIGURATOR         
def get_interface(**kwargs):
    iface = Interface()
    return iface
    
################################################################################
# TEST CODE
################################################################################
if __name__ == "__main__":
   ups = Interface()
