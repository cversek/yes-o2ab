###############################################################################
#Standard Python
import os, sys, time, datetime, Queue, threading
from warnings import warn
#3rd party
import numpy
try:
    from collections import OrderedDict
except ImportError:
    from yes_o2ab.support.odict import OrderedDict
#Automat framework provided
from automat.core.hwcontrol.config.configuration import Configuration
#from automat.services.configurator import ConfiguratorService
#yes_o2ab framework provided
import yes_o2ab.pkg_info
#application local
from   errors import ConfigurationError, DeviceError
###############################################################################
#Module Constants
INTRO_MSG_TEMPLATE = """
*******************************************************************************
YES O2AB Calibrate %(version)s
    authors: Craig Versek (cwv@yesinc.com)
*******************************************************************************
"""
DEFAULT_EXPTIME = 10 # milliseconds
###############################################################################
#Helper Functions
def stream_print(text, 
                 stream = sys.stdout, 
                 eol = '\n', 
                 prefix = None
                ):
        if prefix:
            stream.write(prefix)
        stream.write(text)
        if eol:
            stream.write(eol)
        stream.flush()
        
 ###############################################################################       
class Application:
    def __init__(self, 
                 intro_msg       = None, 
                 skip_test       = False,
                 ignore_device_errors = False, 
                 output_stream   = sys.stdout, 
                 error_stream    = sys.stderr,
                 textbox_printer = lambda text: None,
                ):
        self.skip_test = skip_test
        self.ignore_device_errors = ignore_device_errors
        self.output_stream   = output_stream
        self.error_stream    = error_stream
        self.textbox_printer = textbox_printer
        self.channels = {}
        #load the configuration file
        #cfg_service = ConfiguratorService(searchpaths=self.searchpaths)
        #self.config = cfg_service.request_config_dialog()
        config_filepath = yes_o2ab.pkg_info.platform['config_filepath'] 
        self.config  = Configuration(config_filepath)
        #print the introductory message
        if intro_msg is None:
            intro_msg = INTRO_MSG_TEMPLATE % {'version' : yes_o2ab.pkg_info.metadata['version']}
        self.print_comment(intro_msg)
#        #reserve port for event server
#        self.event_server_port = int(self.config['server']['event_server_port'])
#        sock_obj = reserve_port(self.event_server_port)
#        if sock_obj is None:
#            raise ConfigurationError("could not reserve port '%s' for the event server; likely another instance of eis_launch is already running" % self.event_server_port) 
#        self.event_server_socket = sock_obj 
        #set up the log file
        log_dir      = self.config['paths']['log_dir']    
        log_filepath = os.sep.join((log_dir,'log.txt'))
        self.log_stream = open(log_filepath,'a')
        self.devices     = {}
        self.controllers = {}
        #create an event for synchronize forced shutdown
        self.abort_event = threading.Event()
        #spectral attributes
        self.last_spectrum = None
 
    def setup_textbox_printer(self, textbox_printer):
        self.textbox_printer = textbox_printer

    def print_comment(self, text, eol = '\n', comment_prefix = '#'):
        lines = text.split(eol)
        buff = eol.join([ comment_prefix + line for line in lines])
        stream_print(buff, stream = self.output_stream, eol = eol)
        #also print to the textbox if available
        self.textbox_printer(buff)
    
    def print_log_msg(self,msg):
        stream_print(msg, stream = self.log_stream)
        self.print_comment("Logged: " + msg)        
              
    def load_device(self,handle):
        self.print_comment("Loading device '%s'" % handle) 
        try:
            device   =  self.config.load_device(handle)
            self.devices[handle] = device   #cache the device
            return device
        except Exception, exc:
            settings = self.config['devices'].get(handle, None)
            if settings is None:
                error_msg = "missing settings for device in config file '%s'" % self.config['config_filepath']
            else:
                error_msg = "bad configuration"
            exc = DeviceError(error_msg = error_msg, 
                              handle    = handle, 
                              settings  = settings, 
                              exc       = exc)
            if not self.ignore_device_errors:
                raise exc
            else:
                warn("ignoring following error:\n---\n%s\n---" % exc, RuntimeWarning)
                
                       

    def load_controller(self, name):
        try:
            self.print_comment("Loading controller '%s'..." % name)
            try:
                controller = self.config.load_controller(name)
                self.controllers[name] = controller
                self.print_comment("    success.")
            except Exception, exc:
                self.print_comment("    failed loading controller '%s' with exception: %s" % (name, exc))
                if not self.ignore_device_errors:
                    raise exc
                else:
                    warn("ignoring following error:\n---\n%s\n---" % exc, RuntimeWarning)
        except KeyError:
            pass
    
#    def set_camera_params(self, image_area, exptime):
#        #configure the camera
#        camera = self.load_device('camera')
#        ul_x, ul_y, lr_x, lr_y = image_area
#        camera.set_image_area(ul_x,ul_y,lr_x,lr_y)
#        camera.set_exposure(exptime)
                
    def acquire_spectrum(self, exptime = DEFAULT_EXPTIME):
        #load devices
        camera = self.load_device('camera')
        #acquire image and process into rudimentary spectrum        
        I = camera.take_photo(exptime)
        S = I.sum(axis=1)
        #cache the last spectrum
        self.last_spectrum = S
        return S 

        
