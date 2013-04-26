import Tkinter as tk
import Pmw

#Automat framework provided
from automat.core.gui.pmw_custom.validation import Validator
from automat.core.gui.pmw_custom.entry_form import EntryForm
###############################################################################
TITLE = "Change Capture Settings"
from ..common_defs import FRAMETYPE_DEFAULT, EXPOSURE_TIME_DEFAULT,\
    RBI_NUM_FLUSHES_DEFAULT, RBI_EXPOSURE_TIME_DEFAULT, REPEAT_DELAY_DEFAULT,\
    FIELD_LABEL_FONT
###############################################################################
class CaptureSettingsDialog(Pmw.Dialog):
    def __init__(self,
                 parent = None,
                 ):
                  
        #set up dialog windows
        Pmw.Dialog.__init__(self,
                            parent = parent,
                            title = TITLE, 
                            buttons = ('OK',),
                            defaultbutton = 'OK',
                           )
        frame = self.interior()
        #number of choices for frametype
        self.frametype_var = tk.StringVar(value=FRAMETYPE_DEFAULT)
        self.frametype_optionmenu = Pmw.OptionMenu(frame,
                                                   labelpos = 'w',
                                                   label_text = 'Frame Type:',
                                                   label_font  = FIELD_LABEL_FONT,
                                                   menubutton_textvariable = self.frametype_var,
                                                   items = ['normal','dark','bias','flatfield','opaque'],
                                                   menubutton_width = 6,
                                                  )
        self.frametype_optionmenu.pack(expand='no',fill='x')
        #form widget for a bunch of entries with validation and conversion
        form = EntryForm(frame)
        form.new_field('exposure_time',
                       labelpos    = 'w',
                       label_text  = "   Exposure Time (ms):",
                       label_font  = FIELD_LABEL_FONT,
                       entry_width = 6,
                       value       = EXPOSURE_TIME_DEFAULT,
                       validate    = Validator(_min=0,converter=int)
                      )
        form.new_field('rbi_num_flushes',
                       labelpos    = 'w',
                       label_text  = "Number of RBI Flushes:",
                       label_font  = FIELD_LABEL_FONT,
                       entry_width = 6,
                       value       = RBI_NUM_FLUSHES_DEFAULT,
                       validate    = Validator(_min=0,converter=int)
                      )
        form.new_field('rbi_exposure_time',
                       labelpos    = 'w',
                       label_text  = "  RBI Flood Time (ms):",
                       label_font  = FIELD_LABEL_FONT,
                       entry_width = 6,
                       value       = RBI_EXPOSURE_TIME_DEFAULT,
                       validate    = Validator(_min=0,converter=int)
                      )
        form.new_field('repeat_delay',
                       labelpos    = 'w',
                       label_text  = "     Repeat Delay (s):",
                       label_font  = FIELD_LABEL_FONT,
                       entry_width = 6,
                       value       = REPEAT_DELAY_DEFAULT,
                       validate    = Validator(_min=0,converter=int)
                      )
        form.pack(expand='yes', fill='both')
      
        self.form = form
    def activate(self):
        "override activate to construct and send back the action and the new values"
        action = Pmw.Dialog.activate(self)
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
    
