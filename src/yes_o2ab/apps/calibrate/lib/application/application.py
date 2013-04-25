###############################################################################
#Standard Python
import os, sys, time, datetime, Queue, threading
from warnings import warn
#3rd party
import numpy as np
try:
    from collections import OrderedDict
except ImportError:
    from yes_o2ab.support.odict import OrderedDict
#Automat framework provided
from automat.core.hwcontrol.config.configuration import Configuration
#from automat.services.configurator import ConfiguratorService
#yes_o2ab framework provided
import yes_o2ab.pkg_info
from yes_o2ab.core.data_processing.spectrum_dataset import SpectrumDataSet
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
DEFAULT_EXPTIME         = 10 # milliseconds
DEFAULT_RBI_NUM_FLUSHES = 0

USED_CONTROLLERS = [
                    'image_capture',
                    'condition_monitor',
                    'band_switcher',
                    'filter_switcher', 
                    'band_adjuster',  #FIXME can't be initialized with known state!
                    'focus_adjuster',
                   ]

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
        
################################################################################       
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
        self.devices     = OrderedDict()
        self.controllers = OrderedDict()
        self.metadata = OrderedDict()
        #create an event for synchronize forced shutdown
        self.abort_event = threading.Event()
        #spectral attributes
        self.last_spectrum = None
        
    def initialize(self):
        for name in USED_CONTROLLERS:
            self.print_comment("\tLoading and initializing controller '%s'..." % name)
            controller = self.load_controller(name)
            controller.initialize()
            self.print_comment("\tcompleted")
        #get some configuration details
        filter_wheel = self.load_device('filter_wheel')
        itemsB = sorted(filter_wheel.kwargs['wheel_B'].items())
        self.filter_B_types = [(int(slot.strip("slot")),text) for slot, text in itemsB]
        itemsA = sorted(filter_wheel.kwargs['wheel_A'].items())
        self.filter_A_types = [(int(slot.strip("slot")),text) for slot, text in itemsA]
        self.query_metadata()
            
    def query_metadata(self):
        band_switcher   = self.load_controller('band_switcher')
        filter_switcher = self.load_controller('filter_switcher')
        band_adjuster   = self.load_controller('band_adjuster')
        focus_adjuster  = self.load_controller('focus_adjuster')
        image_capture   = self.load_controller('image_capture')
        condition_monitor = self.load_controller('condition_monitor')
        
        band = band_switcher.band
        if band is None:
            band = "(unknown)"
        filt_pos = filter_switcher.position
        B = filt_pos // 5
        A = filt_pos %  5
        
        focuser_pos     = focus_adjuster.query_position()
        band_adjust_pos = band_adjuster.query_position()
        
        self.metadata['timestamp']   = time.time()
        self.metadata['band']        = band
        self.metadata['filt_pos']    = filt_pos
        self.metadata['filt_B_num']  = B
        self.metadata['filt_A_num']  = A
        self.metadata['filt_B_type'] = self.filter_B_types[B][1]
        self.metadata['filt_A_type'] = self.filter_A_types[A][1]
        self.metadata['band_adjust_pos'] = band_adjust_pos
        self.metadata['focuser_pos'] = focuser_pos
        #gets a lot of condition readings (temperature, pressure, etc.)
        sample = condition_monitor.acquire_sample()
        self.metadata.update(sample)
        return self.metadata
    
    def setup_textbox_printer(self, textbox_printer):
        self.textbox_printer = textbox_printer
    
    def print_comment(self, text, eol = '\n', comment_prefix = '#'):
        buff = ""        
        if eol:        
            lines = text.split(eol)
            buff = eol.join([comment_prefix + line for line in lines])
        else:
            buff = comment_prefix + text
        stream_print(buff, stream = self.output_stream, eol = eol)
        #also print to the textbox if available
        self.textbox_printer(buff)
    
    def print_log_msg(self,msg):
        stream_print(msg, stream = self.log_stream)
        self.print_comment("Logged: " + msg)        
    
    def load_device(self,handle):
        #self.print_comment("Loading device '%s'..." % handle, eol='') 
        try:
            device   =  self.config.load_device(handle)
            self.devices[handle] = device   #cache the device
            self.print_comment("    success.")
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
            try:
                controller = self.config.load_controller(name)
                self.controllers[name] = controller
                #self.print_comment("    success.")
                return controller
            except Exception, exc:
                #self.print_comment("    failed loading controller '%s' with exception: %s" % (name, exc))
                if not self.ignore_device_errors:
                    raise exc
                else:
                    warn("ignoring following error:\n---\n%s\n---" % exc, RuntimeWarning)
        except KeyError:
            pass
    
    def acquire_image(self,
                      frametype = 'normal', 
                      exptime   = DEFAULT_EXPTIME, 
                      rbi_num_flushes = DEFAULT_RBI_NUM_FLUSHES,
                      blocking  = True,
                      ):
        image_capture = self.load_controller('image_capture')
        
        self.last_capture_metadata = self.query_metadata() #get freshest copy
        image_capture.set_configuration(frametype=frametype,
                                        exposure_time=exptime,
                                        num_captures = 1,
                                       )
        if blocking:
            image_capture.run() #this will block until image is acquired
            return image_capture.last_image
        else:
            image_capture.start() #this should not block
            
    def compute_spectrum(self, I = None):
        image_capture = self.load_controller('image_capture')
        if I is None:
            I = image_capture.last_image
        S = None
        if not I is None:
            S = I.sum(axis=0)
        #cache the last spectrum and image
        self.last_image = I
        self.last_spectrum = S
        return S
        
    def export_spectrum(self, filename):
        """export the spectrum in a data format matching the file extension
           valid extensions: .csv 
        """
        S  = self.last_spectrum
        md = self.last_capture_metadata.copy()
        
        spectrum_dataset = SpectrumDataSet(S,metadata=md)
        
        if   filename.endswith(".csv"):
            spectrum_dataset.to_csv_file(filename)
        elif filename.endswith(".db"):
            spectrum_dataset.to_shelf(filename)
        elif filename.endswith(".hd5"):
            raise NotImplementedError("HDF5 formatting is not ready, please check back later!")
        else:
            raise ValueError("the filename extension was not recognized, it must end with: .csv or .hd5")

    def select_band(self, band, blocking = True):
        "run the band switcher "
        self.print_comment("select band")
        band_switcher = self.load_controller('band_switcher')
        band_switcher.set_configuration(band=band)
        if blocking:
            band_switcher.run()
        else:
            band_switcher.start() #run as seperate thread
        
    def select_filter(self, pos, blocking = True):
        "run the filter switcher in a seperate thread"
        filter_switcher = self.load_controller('filter_switcher')
        filter_switcher.set_configuration(position=pos)
        if blocking:
            filter_switcher.run()
        else:
            filter_switcher.start() #run as seperate thread
    
    def adjust_band(self, step, blocking = True):
        step_size = abs(step)
        step_direction = "+1"
        if step < 0:
            step_direction = "-1"
        band_adjuster  = self.load_controller('band_adjuster')
        band_adjuster.set_configuration(step_size=step_size,step_direction=step_direction)
        if blocking:
            band_adjuster.run()
        else:
            band_adjuster.start() #run as seperate thread       
            
    def adjust_focus(self, step, blocking = True):
        step_size = abs(step)
        step_direction = "+1"
        if step < 0:
            step_direction = "-1"
        focus_adjuster = self.load_controller('focus_adjuster')
        focus_adjuster.set_configuration(step_size=step_size,step_direction=step_direction)
        if blocking:
            focus_adjuster.run()
        else:
            focus_adjuster.start() #run as seperate thread
