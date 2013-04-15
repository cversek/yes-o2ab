import Tkinter
from Tkinter import Frame, Button, Label
from Pmw import Dialog

#Automat framework provided
from automat.core.gui.pmw_custom.validation import Validator
from automat.core.gui.pmw_custom.entry_form import EntryForm
###############################################################################
TITLE = "Change Settings"
EXPOSURE_TIME_DEFAULT = 10
RUN_INTERVAL_DEFAULT  = 10
###############################################################################
class SettingsDialog(Dialog):
    def __init__(self,
                 parent              = None,
                 ):
        self.validator = Validator()           
        #set up dialog windows
        Dialog.__init__(self,
                        parent = parent,
                        title = TITLE, 
                        buttons = ('OK',),
                        defaultbutton = 'OK',
                       )
        frame = self.interior()
        form = EntryForm(frame)
        form.new_field('exposure_time',
                       labelpos='w',
                       label_text="Exposure Time (ms):",
                       entry_width=6,
                       value = EXPOSURE_TIME_DEFAULT,
                       validate = self.validator 
        
                      )
        form.new_field('run_interval',
                       labelpos='w',
                       label_text="Run Interval (s):",
                       entry_width=6,
                       value = RUN_INTERVAL_DEFAULT,
                       validate = self.validator 
                      )
        form.pack(expand='yes', fill='both')
      
        self.form = form
    def activate(self):
        "override activate to construct and send back the action and the new values"
        action = Dialog.activate(self)
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
    
