import Tkinter as tk
from Tkinter import Frame, Button, Label
import Pmw
try:
    #in python >= 2.7 this is in standard library
    from   collections import OrderedDict
except ImportError:
    #for older python version, use drop in substitue
    from yes_o2ab.support.odict import OrderedDict

###############################################################################
# Module Constants
from ..common_defs import FRAMETYPE_DEFAULT, EXPOSURE_TIME_DEFAULT,\
    RBI_NUM_FLUSHES_DEFAULT, RBI_EXPOSURE_TIME_DEFAULT, REPEAT_DELAY_DEFAULT,\
    FIELD_LABEL_FONT, HEADING_LABEL_FONT, SUBHEADING_LABEL_FONT
    
CONDITION_FIELDS_ENTRY_WIDTH = 7
###############################################################################
class ConditionFields(Frame):
    def __init__(self, parent):
        self.parent = parent
        Frame.__init__(self, parent)
        self.sample_datetime_field =  Pmw.EntryField(parent,
                                                 labelpos    = 'w',
                                                 label_text  = "   Sample Date/Time (UTC):",
                                                 label_font  = FIELD_LABEL_FONT,
                                                 entry_width = 17,
                                                 entry_state = 'readonly',
                                                 )
        self.fields = OrderedDict()
        self.fields['CC_temp']  = Pmw.EntryField(parent,
                                                 labelpos    = 'w',
                                                 label_text  = "           CCD Cold-side (CC) Temp.:",
                                                 label_font  = FIELD_LABEL_FONT,
                                                 entry_width = CONDITION_FIELDS_ENTRY_WIDTH,
                                                 entry_state = 'readonly',
                                                 )
        self.fields['CH_temp']  = Pmw.EntryField(parent,
                                                 labelpos    = 'w',
                                                 label_text  = "            CCD Hot-side (CH) Temp.:",
                                                 label_font  = FIELD_LABEL_FONT,
                                                 entry_width = CONDITION_FIELDS_ENTRY_WIDTH,
                                                 entry_state = 'readonly',
                                                 )
        self.fields['CC_power'] = Pmw.EntryField(parent,
                                                 labelpos    = 'w',
                                                 label_text  = "          CCD Cooler (CC) Power [%]:",
                                                 label_font  = FIELD_LABEL_FONT,
                                                 entry_width = CONDITION_FIELDS_ENTRY_WIDTH,
                                                 entry_state = 'readonly',
                                                 )
        self.fields['SA_press'] = Pmw.EntryField(parent,
                                                 labelpos    = 'w',
                                                 label_text  = "      Spect. Air (SA) Press. [inHg]:",
                                                 label_font  = FIELD_LABEL_FONT,
                                                 entry_width = CONDITION_FIELDS_ENTRY_WIDTH,
                                                 entry_state = 'readonly',
                                                 )
        self.fields['SA_temp'] = Pmw.EntryField(parent,
                                                 labelpos    = 'w',
                                                 label_text  = "              Spect. Air (SA) Temp.:",
                                                 label_font  = FIELD_LABEL_FONT,
                                                 entry_width = CONDITION_FIELDS_ENTRY_WIDTH,
                                                 entry_state = 'readonly',
                                                 )
        self.fields['SA_humid'] = Pmw.EntryField(parent,
                                                 labelpos    = 'w',
                                                 label_text  = "       Spect. Air (SA) Humid. [%RH]:",
                                                 label_font  = FIELD_LABEL_FONT,
                                                 entry_width = CONDITION_FIELDS_ENTRY_WIDTH,
                                                 entry_state = 'readonly',
                                                 )
        self.fields['FW_temp']  = Pmw.EntryField(parent,
                                                 labelpos    = 'w',
                                                 label_text  = "            Filter Wheel (FW) Temp.:",
                                                 label_font  = FIELD_LABEL_FONT,
                                                 entry_width = CONDITION_FIELDS_ENTRY_WIDTH,
                                                 entry_state = 'readonly',
                                                 )
        self.fields['OT_temp']  = Pmw.EntryField(parent,
                                                 labelpos    = 'w',
                                                 label_text  = "      Optic Table Center (OT) Temp.:",
                                                 label_font  = FIELD_LABEL_FONT,
                                                 entry_width = CONDITION_FIELDS_ENTRY_WIDTH,
                                                 entry_state = 'readonly',
                                                 )
        self.fields['FB_temp']  = Pmw.EntryField(parent,
                                                 labelpos    = 'w',
                                                 label_text  = "      Fore Optic Bracket (FB) Temp.:",
                                                 label_font  = FIELD_LABEL_FONT,
                                                 entry_width = CONDITION_FIELDS_ENTRY_WIDTH,
                                                 entry_state = 'readonly',
                                                 )
        self.fields['GR_temp']  = Pmw.EntryField(parent,
                                                 labelpos    = 'w',
                                                 label_text  = "                 Grating (GR) Temp.:",
                                                 label_font  = FIELD_LABEL_FONT,
                                                 entry_width = CONDITION_FIELDS_ENTRY_WIDTH,
                                                 entry_state = 'readonly',
                                                 )
        self.fields['MB_temp']  = Pmw.EntryField(parent,
                                                 labelpos    = 'w',
                                                 label_text  = "          Mirror Bracket (MB) Temp.:",
                                                 label_font  = FIELD_LABEL_FONT,
                                                 entry_width = CONDITION_FIELDS_ENTRY_WIDTH,
                                                 entry_state = 'readonly',
                                                 )
        self.fields['EB_temp']  = Pmw.EntryField(parent,
                                                 labelpos    = 'w',
                                                 label_text  = "          Electrical Box (EB) Temp.:",
                                                 label_font  = FIELD_LABEL_FONT,
                                                 entry_width = CONDITION_FIELDS_ENTRY_WIDTH,
                                                 entry_state = 'readonly',
                                                 )
        self.fields['RA_temp']  = Pmw.EntryField(parent,
                                                 labelpos    = 'w',
                                                 label_text  = "                Room Air (RA) Temp.:",
                                                 label_font  = FIELD_LABEL_FONT,
                                                 entry_width = CONDITION_FIELDS_ENTRY_WIDTH,
                                                 entry_state = 'readonly',
                                                 )
        self.fields['OA_temp']  = Pmw.EntryField(parent,
                                                 labelpos    = 'w',
                                                 label_text  = "             Outside Air (OA) Temp.:",
                                                 label_font  = FIELD_LABEL_FONT,
                                                 entry_width = CONDITION_FIELDS_ENTRY_WIDTH,
                                                 entry_state = 'readonly',
                                                 )
        self.fields['windspeed']  = Pmw.EntryField(parent,
                                                 labelpos    = 'w',
                                                 label_text  = "                  Wind Speed (MPH).:",
                                                 label_font  = FIELD_LABEL_FONT,
                                                 entry_width = CONDITION_FIELDS_ENTRY_WIDTH,
                                                 entry_state = 'readonly',
                                                 )
                                                 
    def pack(self,*args,**kwargs):
        self.sample_datetime_field.pack(*args,**kwargs)
        for key, widget in self.fields.items():
            widget.pack(*args,**kwargs)
