###############################################################################
#Standard python
import copy
try:
    from collections import OrderedDict
except ImportError:
    from yes_o2ab.support.odict import OrderedDict
#Automat framework provided
from automat.core.events.event_parser import EventParser as BaseEventParser
#yes_o2ab framework provided

###############################################################################
class EventParser(BaseEventParser):
    def __init__(self, event_stream = None):
        self.current_solar_tracker_data      = OrderedDict()
        self.current_optics_data             = OrderedDict()
        self.temperature_dataset             = []
        self.curr_temperature_data           = OrderedDict()
        BaseEventParser.__init__(self, event_stream = event_stream)

    # solar_tracker events ----------------------------------------------- 
    def handle_SOLAR_TRACKER_STARTED(self,event_info):
        pass

    def handle_SOLAR_TRACKER_CONTROL_POINT(self,event_info):
        self.current_solar_tracker_data.update(event_info)   
    
    def handle_SOLAR_TRACKER_STOPPED(self,event_info):
        pass
        
    def handle_SOLAR_TRACKER_ABORTED(self,event_info):
        pass
            
    # temperature_monitor events --------------------------------------------  
    def handle_TEMPERATURE_MONITOR_STARTED(self, event_info):
        pass

    def handle_TEMPERATURE_MONITOR_STOPPED(self, event_info):
        pass
        #self.temperature_dataset.set_metadata('end_timestamp',event_info['timestamp'])
        #return ('TEMPERATURE_DATASET',self.temperature_dataset)

    def handle_TEMPERATURE_SAMPLE(self, event_info):
        self.curr_temperature_data.update(event_info)
        #self.temperature_dataset.append_record(**self.curr_temperature_data)  #add another temperature record
        
    def handle_TEMPERATURE_MONITOR_ABORTED(self, event_info):
        pass
        #self.temperature_dataset.set_metadata('end_timestamp',event_info['timestamp'])
        #return ('TEMPERATURE_DATASET',self.temperature_dataset)
            
    # band_switcher events --------------------------------------------------
    def handle_BAND_SWITCHER_SELECT_BAND_STARTED(self, event_info):
        pass

    def handle_BAND_SWITCHER_SELECT_BAND_COMPLETED(self, event_info):
        self.current_optics_data['band'] = event_info.get('band')

    def handle_BAND_SWITCHER_SELECT_BAND_ABORTED(self, event_info):
        pass

###############################################################################
# TEST CODE
###############################################################################
if __name__ == "__main__":
    from automat.filetools.pickle_file import PickleFile
    import sys
    PF = PickleFile(sys.argv[1])
    EP = EventParser(PF)
    print EP.parse_all()
