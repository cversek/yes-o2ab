###############################################################################
#Standard Python
import socket, sys, os, time, datetime, Queue, thread, threading, bz2, numpy,\
       copy, warnings

#use the faster library if available
try: 
    import cPickle as pickle 
except ImportError:
    import pickle

#get the Process class from preffered source
try:
    from multiprocessing import Process #for python >2.6
except ImportError:
    from processing import Process   #older pyprocessing package for python 2.4,2.5

try:
    from collections import OrderedDict
except ImportError:
    from yes_o2ab.support.odict import OrderedDict

#Automat framework provides
from automat.core.events.event_caching  import EventCachingProcess as BaseEventCachingProcess
#yes_o2ab framework provided
from yes_o2ab.core.events.event_parser import EventParser 

###############################################################################
BUNDLE_EVENTS_FILENAME            = "events.pkl"
BUNDLE_SPECTRA_SUBDIR_NAME        = "spectra"

def gen_unique_index():
    index = 0
    while True:
        yield index
        index += 1
###############################################################################

###############################################################################
class EventCachingProcess(BaseEventCachingProcess):
    def __init__(self, application, event_queue, bundle_path, repo_path = None, event_parser = None):        
        self.app            = application
        self.bundle_path    = bundle_path
        self.repo_path      = repo_path
        if event_parser is None:
            event_parser = EventParser()
        self.event_parser   = event_parser
        self.event_filename = os.path.sep.join( (self.bundle_path, BUNDLE_EVENTS_FILENAME) )
        self.event_file     = open(self.event_filename,'w')
        self.unique_index   = gen_unique_index()
        BaseEventCachingProcess.__init__(self, event_queue, event_file = self.event_file)
   
    def __del__(self):
        "cleanup on destruction"
        self.shutdown()
    
    def print_comment(self, text):
        "send a comment to the application"
        text = "Event Caching Process: %s" % text
        self.app.print_comment(text)

    def shutdown(self):
        "compress the events file and remove the uncompressed"
        #shutdown the thread
        BaseEventCachingProcess.shutdown(self)
        self.print_comment("please wait while the events file is compressed...")
        self.event_file.close() 
        event_file     = open(self.event_filename,'r')
        bz2_event_file = bz2.BZ2File(self.event_filename + '.bz2','w')
        bz2_event_file.writelines(event_file)
        bz2_event_file.close()
        os.remove(self.event_filename)
        #cleanup        
        self.clear() #clear the events cache

    def event_callback(self, event):
        "overload this function to process events as they come in"      
        #print out the event
        self.app.print_event(event)
        #cache events in events file
        pickled_data = pickle.dumps(event)
        #compressed_data = self.bz2_compressor.compress(pickled_data) 
        self.event_file.write(pickled_data)
        self.event_file.flush()
        #parse the event stream one at a time
        parsend = self.event_parser.feed(event)
        if not parsend is None: #something has been parsed from the stream, so handle it
            obj_type, obj = parsend
            #construct the obj handler name
            handler_name = "handle_%s" % obj_type  
            #retrieve and call the handler 
            handler = None    
            try:               
                handler = self.__getattribute__(handler_name)
            except AttributeError:    #handler not found for the object type
                warnings.warn("handler not found for Event Parsing object '%s'" % obj_type)
                handler = lambda o: o #do nothing handler
            obj = handler(obj)
        #send back the event
        return event

    #--------------------------------------------------------------------------
    # Helper Methods
    def _construct_bundle_paths(self):
        #build all the bundle paths
        paths = {}
        paths['spectra_subdir'] = spectra_subdir_path = os.path.sep.join( (self.bundle_path, BUNDLE_SPECTRA_SUBDIR_NAME) )
        if not os.path.isdir(spectra_subdir_path):
            os.mkdir(spectra_subdir_path)
            self.print_comment("created subdirectory for spectra: '%s'" % spectra_subdir_path) 
        return paths
    #--------------------------------------------------------------------------
    # Parsed Object Handlers    
    def handle_TEMPERATURE_DATASET(self, obj):
        self.print_comment("parsed temperature history data from event stream")
        TDS = obj
 

###############################################################################
# TEST CODE - FIXME
###############################################################################
if __name__ == "__main__":
    from automat.filetools.pickle_file import PickleFile
    import sys
    PF = PickleFile(sys.argv[1])
    
    DATA_DIR = "data"
    EQ = Queue.Queue() 
    ECP = EventCachingProcess(EQ,DATA_DIR)
    
    for event in PF:
        name, content = event
        content['timestamp'] = content.get('time') 
        ECP.event_callback(event) 
