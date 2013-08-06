import Tkinter as tk
from Tkinter import Frame, Button, Label
from Pmw import Dialog, EntryField
try:
    #in python >= 2.7 this is in standard library
    from   collections import OrderedDict
except ImportError:
    #for older python version, use drop in substitue
    from yes_o2ab.support.odict import OrderedDict
#Automat framework provided
from automat.core.gui.pmw_custom.validation import Validator
from automat.core.gui.pmw_custom.entry_form import EntryForm

###############################################################################
from ..common_defs import FIELD_LABEL_FONT
TRACKING_FIELDS_ENTRY_WIDTH = 9
###############################################################################
class TrackingGotoSunDialog(Dialog):
    def __init__(self,
                 parent              = None,
                 ):
        #set up dialog windows
        Dialog.__init__(self,
                        parent = parent,
                        title = "Tracking Goto Sun", 
                        buttons = ('OK',),
                        defaultbutton = 'OK',
                       )
        main_frame = self.interior()
      
    def activate(self):
        "override activate to construct and send back the action and the new values"
        action = Dialog.activate(self)
        return action
        
class TrackingGotoCoordsDialog(Dialog):
    def __init__(self,
                 parent              = None,
                 ):
        #set up dialog windows
        Dialog.__init__(self,
                        parent = parent,
                        title = "Tracking Goto Coords", 
                        buttons = ('OK',),
                        defaultbutton = 'OK',
                       )
        main_frame = self.interior()
        az_frame = Frame(main_frame)
        self.az_field = EntryField(az_frame,
                                   labelpos    = 'w',
                                   label_text  = "  azimuth target:",
                                   label_font  = FIELD_LABEL_FONT,
                                   entry_width = TRACKING_FIELDS_ENTRY_WIDTH,
                                   #entry_state = 'readonly',
                                   )
        self.az_field.pack(side='left', anchor="w", expand='no')
        self.az_limits_label = Label(az_frame, text = "(min=???,max=???)")
        self.az_limits_label.pack(side='right', anchor='w', expand='no')
        az_frame.pack(side='top')
        el_frame = Frame(main_frame)
        self.el_field = EntryField(el_frame,
                                   labelpos    = 'w',
                                   label_text  = "elevation target:",
                                   label_font  = FIELD_LABEL_FONT,
                                   entry_width = TRACKING_FIELDS_ENTRY_WIDTH,
                                   #entry_state = 'readonly',
                                   )
        self.el_field.pack(side='left', anchor="w", expand='no')
        self.el_limits_label = Label(el_frame, text = "(min=???,max=???)")
        self.el_limits_label.pack(side='right', anchor='w', expand='no')
        el_frame.pack(side='top')
        
    def set_limits(self, az_CW_limit, az_CCW_limit, el_CW_limit, el_CCW_limit):
        az_min = min(az_CW_limit, az_CCW_limit)
        az_max = max(az_CW_limit, az_CCW_limit)
        self.az_field.configure( validate = Validator(_min=az_min,_max=az_max,converter=float))
        self.az_limits_label.configure(text="(min=%0.2f,max=%0.2f)" % (az_min,az_max))
        el_min = min(el_CW_limit, el_CCW_limit)
        el_max = max(el_CW_limit, el_CCW_limit)
        self.el_field.configure(validate = Validator(_min=el_min,_max=el_max,converter=float))
        self.el_limits_label.configure(text="(min=%0.2f,max=%0.2f)" % (el_min,el_max))
      
    def activate(self):
        "override activate to construct and send back the action and the new values"
        action = Dialog.activate(self)
        if not (self.az_field.valid() and self.el_field.valid()):
            return self.activate()
        return action

###############################################################################
 

###############################################################################
# TEST CODE - FIXME
###############################################################################
if __name__ == "__main__":
    

    # Initialise Tkinter and Pmw.
    import Tkinter    
    import Pmw
    #create a test window    
    root = Pmw.initialise()    
    
