"""
Controller to monitor safety conditions
"""
###############################################################################
import time, datetime, traceback, socket
from threading import Thread
from Queue import Queue

try:
    from collections import OrderedDict
except ImportError:
    from yes_o2ab.support.odict import OrderedDict

from automat.core.hwcontrol.controllers.controller           import AbortInterrupt, NullController
from automat.core.hwcontrol.controllers.networked_controller import ClientController, NetworkedController


###############################################################################
DEFAULT_PORT = 9000

DEFAULT_CONFIGURATION = OrderedDict([
    ("port", DEFAULT_PORT),
])
      
###############################################################################
class ServerInterface(NetworkedController):
    def __init__(self, **kwargs):
        NetworkedController.__init__(self, **kwargs)
        
    def main(self):
        try:
            port = int(self.configuration['port'])
            # START MONITORING LOOP  -----------------------------------
            info = OrderedDict()
            info['timestamp'] = time.time()
            info['port']  = port
            self._send_event("SAFETY_MONITOR_STARTED",info)
            while True:
                self._thread_abort_breakout_point()
                self.accept_connection()
                self._thread_abort_breakout_point()
                #check if client requests stop
                if self._thread_check_stop_event():
                    # END NORMALLY -----------------------------------
                    info = OrderedDict()
                    info['timestamp'] = time.time()
                    self._send_event("SAFETY_MONITOR_STOPPED",info)
                    return
        except (AbortInterrupt, Exception), exc:
            # END ABNORMALLY -----------------------------------------
            info = OrderedDict()
            info['timestamp'] = time.time()
            info['reason']    = exc
            if not isinstance(exc, AbortInterrupt): 
                info['traceback'] = traceback.format_exc()
            self._send_event("SAFETY_MONITOR_ABORTED",info)
        finally: #Always clean up!
            self.reset()
            
class ClientInterface(ClientController):
    def __init__(self, **kwargs):
        ClientController.__init__(self, **kwargs)
        
        

       
#------------------------------------------------------------------------------
# INTERFACE CONFIGURATOR
def get_interface(**kwargs):
    interface_mode = kwargs.pop('interface_mode','server')
    if   interface_mode == 'server':
        return ServerInterface(**kwargs)
    elif interface_mode == 'client':
        return ClientInterface(**kwargs)
    else:
        raise ValueError("interface_mode '%s' is not valid" % interface_mode)
            
    
    
###############################################################################
# TEST CODE - Run the Controller, collect events, and plot
###############################################################################
# FIXME
if __name__ == "__main__":
    pass

