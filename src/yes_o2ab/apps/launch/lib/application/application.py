###############################################################################
#Standard Python
import os, sys, time, datetime, Queue, threading
from warnings import warn
try:
    from collections import OrderedDict
except ImportError:
    from yes_o2ab.support.odict import OrderedDict
#Automat framework provided
from automat.core.events.event_server import EventServer, reserve_port
from automat.core.hwcontrol.config.configuration import Configuration
#from automat.services.configurator import ConfiguratorService
#yes_o2ab framework provided
from yes_o2ab.core.events.event_parser import EventParser
import yes_o2ab.pkg_info
#application local
from   event_caching_process      import EventCachingProcess
from   errors import ConfigurationError, DeviceError
###############################################################################
#Module Constants
INTRO_MSG_TEMPLATE = """
*******************************************************************************
YES O2AB Launcher %(version)s
    authors: Craig Versek (cwv@yesinc.com)
*******************************************************************************
"""

DEFAULT_SEARCHPATHS = ['.', yes_o2ab.pkg_info.platform['config_filedir']]
MAIN_LOOP_DELAY = 0.100
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
                 event_queue     = None,
                 searchpaths     = DEFAULT_SEARCHPATHS[:],
                ):
        self.skip_test = skip_test
        self.ignore_device_errors = ignore_device_errors
        self.output_stream   = output_stream
        self.error_stream    = error_stream
        self.textbox_printer = textbox_printer
        if event_queue is None:
            event_queue = Queue.Queue()
        self.event_queue  = event_queue
        self.searchpaths  = searchpaths
        self.event_parser = None   #used to overload event parsing for a particular experiment
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
 
    def setup_textbox_printer(self, textbox_printer):
        self.textbox_printer = textbox_printer

    def print_comment(self, text, eol = '\n', comment_prefix = '#'):
        lines = text.split(eol)
        buff = eol.join([ comment_prefix + line for line in lines])
        stream_print(buff, stream = self.output_stream, eol = eol)
        #also print to the textbox if available
        self.textbox_printer(buff)

    def print_event(self, event):
        event_type, info = event
        buff = []
        buff.append("---")
        buff.append("Event:")
        buff.append("  type: %s" % event_type)
        buff.append("  info:")
        for key in info.keys():
            buff.append("    %s: %s" % (key,info[key]))
        buff.append("...")
        buff = "\n".join(buff)
        stream_print(buff, stream = self.output_stream)
        #also print to the textbox if available
        self.textbox_printer(buff)
    
    def print_log_msg(self,msg):
        stream_print(msg, stream = self.log_stream)
        self.print_comment("Logged: " + msg)        
          
    def load_and_test_devices(self):
        device_handles = self.config['devices'].keys()
        self.print_comment('Running diagnostics on devices: %s' % device_handles)
        for handle in device_handles:
            self.load_device(handle)
            if not self.skip_test:
                self.test_device(handle)
    
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
                
    
    def test_device(self, handle):
        try:
            device = self.devices[handle]
        except KeyError:
            device = self.load_device(handle)
        self.print_comment("Testing device '%s'..." % handle)
        #try test first using test function
        error_msg = None
        try: 
            passed, msg = device.test()
            error_msg = msg
            self.print_comment("    self test passed?: %s" % passed) 
            if not passed:
                raise IOError, 'self test failure'
        except NotImplementedError:
                pass
        except Exception, exc:
            settings = self.config['devices'].get(handle,{})
            if error_msg is None:
                error_msg = 'communications failed'
            exc = DeviceError(error_msg = error_msg, 
                              handle    = handle, 
                              settings  = settings, 
                              exc       = exc)
            if not self.ignore_device_errors:
                raise exc
            else:
                warn("ignoring following error:\n---\n%s\n---" % exc, RuntimeWarning)
        
        #try test by requesting idn
        error_msg = None
        try: 
            idn = device.identify()
            self.print_comment("    idn: %s" % idn)
        except NotImplementedError:
                pass
        except Exception, exc:
            settings = self.config['devices'].get(handle,{})
            if error_msg is None:
                error_msg = 'communications failed'
            exc = DeviceError(error_msg = error_msg, 
                              handle    = handle, 
                              settings  = settings, 
                              exc       = exc)
            if not self.ignore_device_errors:
                raise exc
            else:
                warn("ignoring following error:\n---\n%s\n---" % exc, RuntimeWarning)                     

    def load_all_controllers(self):
        try:
            controllers_dict = self.config['controllers']
            for name in controllers_dict.keys():
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
        
    #---MAIN ------------------------------------------------------------------    
    def main(self):
        #load and test the devices
        self.load_and_test_devices()
        #load the controllers
        self.load_all_controllers()
        #setup the event_parser -----------------------------------------------
        self.event_parser = EventParser()
        # start up all sub process threads ------------------------------------           
        #start the threads that handle events
        self.start_event_caching_process()
        #start up the event server
        #self.start_event_server()
        #start the controller threads
        for name, controller in self.controllers.items():
            self.print_comment("Launching controller '%s'" % name)
            controller.initialize_devices()
            controller.thread_init(  
                                   event_queue = self.event_queue,  #to pass back controller events
                                   #stop_event  = self.stop_event,  #to synchronize controlled exit
                                   abort_event = self.abort_event,  #to synchronize forced exit
                                  )
            controller.start()        
        try:
            while True:
                time.sleep(MAIN_LOOP_DELAY)
        except KeyboardInterrupt:
            self.shutdown()
        
        
           
    def shutdown(self, blocking = True):
        "signal all the experiment threads to stop in a controlled manner w/ _experiment_shutdown__sequence"
        if blocking:
            self._shutdown_sequence()
        else:
            self._shutdown_thread = threading.Thread(target = self._shutdown_sequence)
            self._shutdown_thread.start()       
    
    def _shutdown_sequence(self):  
        for name, controller in self.controllers.items():
                self.print_comment("Stopping controller '%s'.  Please wait until thread cleans up..." % name)            
                controller.stop()
                controller.shutdown()
        #self.shutdown_event_server()
        self.shutdown_event_caching_process()
    
    #---EVENT CACHING PROCESS -----------------------------------
    def start_event_caching_process(self):
        #set up the data bundle path
        userdata_path = self.config['paths']['data_dir']
        date = datetime.datetime.now().date()
        bundle_dir = "%s" % (date,)
        bundle_path = os.path.sep.join( (userdata_path,bundle_dir) )
        #ensure that data_path is unique
        index = 1
        while os.path.isdir(bundle_path):
            index += 1
            bundle_path = os.path.sep.join( (userdata_path,bundle_dir + " (%d)" % index) )
        os.mkdir(bundle_path)
        
        #set up database path
        #repo_path = self.config['paths']['repo_dir'] #FIXME - this should point to the repo location 
        repo_path = None

        #configure the event caching process   
        self.event_caching_process = EventCachingProcess( application   = self,
                                                          event_parser  = self.event_parser,
                                                          event_queue   = self.event_queue, 
                                                          bundle_path   = bundle_path,
                                                          repo_path     = repo_path,  
                                                         )
        #start up the event handling threads
        self.event_caching_process.start()

    def shutdown_event_caching_process(self):
        self.print_comment("shutting down the event caching process...")
        self.event_caching_process.shutdown()
            
    #---EVENT SERVER --------------------------------------------
    def start_event_server(self):
        #reserve standard port if it hasn't been
        if self.event_server_socket is None:
            self.event_server_socket = reserve_port(self.event_server_port)
            if self.event_server_socket is None:
                raise ConfigurationError("could not reserve port '%s' for the event server; likely another instance of eis_launch is already running" % self.event_server_port)
        #configure the event server
        self.event_server = EventServer(event_queue  = self.event_queue,
                                        sock_obj     = self.event_server_socket,
                                        log_func     = self.print_log_msg,
                                        event_caching_process = self.event_caching_process,
                                       )
        
        #start up the server
        self.event_server.start()
        
    def shutdown_event_server(self):
        self.print_comment("shutting down event server...")
        #shutdown the event server thread
        self.event_server.shutdown(close_sock_obj = False) #leave the socket open until the application exits
        self.event_server_socket.close() #force close the socket object so completed experiments will not block a new experiment
        self.event_server_socket = None

        
