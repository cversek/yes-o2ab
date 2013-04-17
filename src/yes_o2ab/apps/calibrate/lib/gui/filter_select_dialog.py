import Tkinter as tk
from Tkinter import Frame, Button, Label
from Pmw import Dialog
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
TITLE = "Select Filter"
HEADING_FONT = "Helvetica 14 bold"
HEADING_PADX = 30
###############################################################################
class FilterSelectDialog(Dialog):
    def __init__(self,
                 parent              = None,
                 choicesA = [],
                 choicesB = [],
                 command = lambda e: None,
                 ):
        self.varB = tk.IntVar()
        self.varA = tk.IntVar()
        padxB = max([len(text) for index, text in choicesB])
        padxA = max([len(text) for index, text in choicesA])

        #set up dialog windows
        Dialog.__init__(self,
                        parent = parent,
                        title = TITLE, 
                        buttons = ('OK',),
                        defaultbutton = 'OK',
                        command = command,
                       )
        frame = self.interior()
        #build buttons for wheel B
        frameB = tk.Frame(frame)
        tk.Label(frameB, text="Wheel B (Band Pass)", font = HEADING_FONT).pack(anchor='w', padx=HEADING_PADX)
        for index, text in choicesB:
            tk.Radiobutton(frameB,
                           text=text,
                           padx = padxB, 
                           variable=self.varB, 
                           value=index).pack(side="top", anchor='w')
        #build buttons for wheel A
        frameA = tk.Frame(frame)
        tk.Label(frameA, text="Wheel A (Auxiliary)", font = HEADING_FONT).pack(anchor='w', padx=HEADING_PADX)
        for index, text in choicesA:
            tk.Radiobutton(frameA,
                           text=text,
                           padx = padxA, 
                           variable=self.varA, 
                           value=index).pack(side="top",anchor='w')
        frameB.pack(side='left')
        frameA.pack(side='right')
      
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
    
