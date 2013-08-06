###############################################################################
#Standard Python
import os, sys, time, datetime, Queue, threading
from warnings import warn
from Queue import Queue
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
from yes_o2ab.core.data_processing.spectrum_dataset   import SpectrumDataSet
from yes_o2ab.core.data_processing.conditions_dataset import ConditionsDataSet
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

#Common Definitions
from ..common_defs import FRAMETYPE_DEFAULT, EXPOSURE_TIME_DEFAULT,\
    RBI_NUM_FLUSHES_DEFAULT, RBI_EXPOSURE_TIME_DEFAULT, REPEAT_DELAY_DEFAULT,\
    CCD_TEMP_SETPOINT_DEFAULT
    
FOCUSER_CENTER_POS = 3500
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
    USED_CONTROLLERS = [
                        'image_capture',
                        'condition_monitor',
                        'band_switcher',
                        'filter_switcher', 
                        'band_adjuster',  #FIXME can't be initialized with known state!
                        'focus_adjuster',
                        'solar_tracker',
                       ]
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
        #structures for holding conditions data
        self.conditions_Ydata = OrderedDict()
        self.conditions_sample_times = []
        #create thread initeraction objects
        self.event_queue = Queue()
        self.abort_event = threading.Event()
        #self.stop_event  = threading.Event()
        #spectral attributes
        self.last_raw_spectrum           = None
        self.background_spectrum_dataset = None
        
    def initialize(self):
        for handle in self.USED_CONTROLLERS:
            self.print_comment("\tLoading and initializing controller '%s'..." % handle)
            controller = self.load_controller(handle)
            controller.initialize(event_queue = self.event_queue, abort_event = self.abort_event)
            self.print_comment("\tcompleted")
        #get some configuration details
        filter_wheel = self.load_device('filter_wheel')
        itemsB = sorted(filter_wheel.kwargs['wheel_B'].items())
        self.filter_B_types = [(int(slot.strip("slot")),text) for slot, text in itemsB]
        itemsA = sorted(filter_wheel.kwargs['wheel_A'].items())
        self.filter_A_types = [(int(slot.strip("slot")),text) for slot, text in itemsA]
        self.query_metadata()
            
    def abort_controllers(self):
        self.print_comment("ABORTING ALL CONTROLLERS!" )
        self.abort_event.set()
        for handle in self.USED_CONTROLLERS:
            self.print_comment("\tJoining controller '%s'..." % handle)
            controller = self.load_controller(handle)
            if controller.thread_isAlive():
                controller.join()
            self.print_comment("\tcompleted")
    
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
        
    def query_metadata(self):
        image_capture      = self.load_controller('image_capture')
        flatfield_switcher = self.load_controller('flatfield_switcher')
        band_switcher      = self.load_controller('band_switcher')
        filter_switcher    = self.load_controller('filter_switcher')
        band_adjuster      = self.load_controller('band_adjuster')
        focus_adjuster     = self.load_controller('focus_adjuster')
        tracking_mirror_positioner = self.load_controller('tracking_mirror_positioner')
        condition_monitor  = self.load_controller('condition_monitor')
        
        #query controllers for state
        flatfield_state = flatfield_switcher.query_state()
        if flatfield_state is None:
            flatfield_state = "(unknown)"
        band = band_switcher.query_band()
        if band is None:
            band = "(unknown)"
        
        filt_pos = filter_switcher.query_position()
        B = filt_pos // 5
        A = filt_pos %  5
        
        focuser_pos     = focus_adjuster.query_position()
        band_adjust_pos = band_adjuster.query_position()
        
        sample = condition_monitor.get_last_sample()
        
        #write the metadata in an importance order (OrderedDict structure)
        self.metadata['timestamp']         = time.time()
        self.metadata['frametype']         = image_capture.configuration['frametype']
        self.metadata['exposure_time']     = int(image_capture.configuration['exposure_time'])
        self.metadata['rbi_num_flushes']   = int(image_capture.configuration['rbi_num_flushes'])
        self.metadata['rbi_exposure_time'] = int(image_capture.configuration['rbi_exposure_time'])
        self.metadata['flatfield_state']   = flatfield_state
        self.metadata['band']              = band
        self.metadata['filt_pos']          = filt_pos
        self.metadata['filt_B_num']        = B
        self.metadata['filt_A_num']        = A
        self.metadata['filt_B_type']       = self.filter_B_types[B][1]
        self.metadata['filt_A_type']       = self.filter_A_types[A][1]
        self.metadata['band_adjust_pos']   = band_adjust_pos
        self.metadata['focuser_pos']       = focuser_pos
        self.metadata['azimuth']           = tracking_mirror_positioner.az_pos
        self.metadata['elevation']         = tracking_mirror_positioner.el_pos
        if not sample is None:
            self.metadata.update(sample) # a whole bunch of conditions
        return self.metadata
        
    def query_filter_status(self):
        filter_switcher   = self.load_controller('filter_switcher')
        filt_pos = filter_switcher.query_position()
        B = filt_pos // 5
        A = filt_pos %  5
        self.metadata['filt_pos']          = filt_pos
        self.metadata['filt_B_num']        = B
        self.metadata['filt_A_num']        = A
        self.metadata['filt_B_type']       = self.filter_B_types[B][1]
        self.metadata['filt_A_type']       = self.filter_A_types[A][1]
        return self.metadata
    
    def acquire_image(self,
                      frametype         = FRAMETYPE_DEFAULT, 
                      exposure_time     = EXPOSURE_TIME_DEFAULT,
                      rbi_num_flushes   = RBI_NUM_FLUSHES_DEFAULT,
                      rbi_exposure_time = RBI_EXPOSURE_TIME_DEFAULT,
                      CCD_temp_setpoint = None,
                      blocking          = True,
                      ):
        image_capture = self.load_controller('image_capture')
        image_capture.set_configuration(frametype         = frametype,
                                        num_captures      = 1,
                                        exposure_time     = exposure_time,
                                        rbi_num_flushes   = rbi_num_flushes,
                                        rbi_exposure_time = rbi_exposure_time,
                                        CCD_temp_setpoint = CCD_temp_setpoint,
                                       )
        self.last_capture_metadata = self.query_metadata() #get freshest copy
        if blocking:
            image_capture.run() #this will block until image is acquired
            return image_capture.last_image
        else:
            image_capture.start() #this should not block
            
            
    def compute_raw_spectrum(self, I = None):
        image_capture = self.load_controller('image_capture')
        if I is None:
            I = image_capture.last_image
        S = None
        if not I is None:
            S = I.sum(axis=0)
        #cache the last spectrum and image
        self.last_image    = I
        self.last_raw_spectrum = S
        return S
    
    def get_last_image(self):
        return self.last_image
            
    def get_raw_spectrum(self):
        return self.last_raw_spectrum
        
    def get_background_spectrum(self):
        B = None
        if self.background_spectrum_dataset:
            #try loading corrected data first
            B = self.background_spectrum_dataset.get('corrected_intensity')
            if B is None: #default to raw for old file formats
                raise Warning("'corrected_intensity' field not found, likely using an old format, defaulting to 'raw_intensity' field")
            B = self.background_spectrum_dataset.get('raw_intensity')
        return B
        
    def export_raw_spectrum(self, filename):
        """export the spectrum in a data format matching the file extension
           valid extensions: .csv, .db, .hd5
        """
        S  = self.get_raw_spectrum()
        md = self.last_capture_metadata.copy()

        spectrum_dataset = SpectrumDataSet(S,metadata=md)
        if   filename.endswith(".csv"):
            spectrum_dataset.to_csv_file(filename)
        elif filename.endswith(".db"):
            spectrum_dataset.to_shelf(filename)
        elif filename.endswith(".hd5"):
            raise NotImplementedError("HDF5 formatting is not ready, please check back later!")
        else:
            raise ValueError("the filename extension was not recognized, it must end with: .csv, .db, or .hd5")
            
    def import_background_spectrum(self, filename):
        """export the spectrum in a data format matching the file extension
           valid extensions: .csv, .db, .hd5
        """
        if   filename.endswith(".csv"):
            self.background_spectrum_dataset = SpectrumDataSet.from_csv(filename)
        elif filename.endswith(".db"):
            self.background_spectrum_dataset = SpectrumDataSet.from_shelf(filename)
        elif filename.endswith(".hd5"):
            raise NotImplementedError("HDF5 formatting is not ready, please check back later!")
        else:
            raise ValueError("the filename extension was not recognized, it must end with: .csv, .db, or .hd5")
        path, fn = os.path.split(filename)
        self.metadata['background_filename'] = fn
    
    def compute_processed_spectrum_dataset(self):
        image_capture = self.load_controller('image_capture')
        S  = self.get_raw_spectrum()
        B  = self.get_background_spectrum()
        C = S - B
        md = self.last_capture_metadata.copy()
        md['background_filename'] = self.metadata['background_filename']
        spectrum_dataset = SpectrumDataSet(raw_intensity = S,
                                           background_intensity = B,
                                           corrected_intensity = C,
                                           metadata=md)
        return spectrum_dataset
            
    def export_processed_spectrum(self, filename):
        """export the spectrum in a data format matching the file extension
           valid extensions: .csv, .db, .hd5
        """
        spectrum_dataset = self.compute_processed_spectrum_dataset()
        
        if   filename.endswith(".csv"):
            spectrum_dataset.to_csv_file(filename)
        elif filename.endswith(".db"):
            spectrum_dataset.to_shelf(filename)
        elif filename.endswith(".hd5"):
            raise NotImplementedError("HDF5 formatting is not ready, please check back later!")
        else:
            raise ValueError("the filename extension was not recognized, it must end with: .csv, .db, or .hd5")    
        
    def export_conditions(self, filename):
        """export the conditions in a data format matching the file extension
           valid extensions: .csv 
        """
        Ys = [Y for key, Y in self.conditions_Ydata.items()]
        t  = np.array(self.conditions_sample_times)
        
        dataset = ConditionsDataSet(t,Ys)
        
        if   filename.endswith(".csv"):
            dataset.to_csv_file(filename)
        elif filename.endswith(".db"):
            dataset.to_shelf(filename)
        elif filename.endswith(".hd5"):
            raise NotImplementedError("HDF5 formatting is not ready, please check back later!")
        else:
            raise ValueError("the filename extension was not recognized, it must end with: .csv, .db, or .hd5")
        
    def clear_conditions_data(self):
        """export the conditions in a data format matching the file extension
           valid extensions: .csv 
        """
        #structures for holding conditions data
        self.conditions_Ydata = OrderedDict()
        self.conditions_sample_times = []

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
    
    def center_focus(self, blocking = True):
        focus_adjuster = self.load_controller('focus_adjuster')
        focuser_pos    = focus_adjuster.query_position()
        step = FOCUSER_CENTER_POS - focuser_pos
        self.adjust_focus(step,blocking=blocking)
