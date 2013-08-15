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
                 ):
        self.varBand = tk.StringVar(value='(unknown)')
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
                       )
        main_frame = self.interior()
        #band selection
        band_select_frame = tk.Frame(main_frame)
        tk.Label(band_select_frame, text="Band Selection:", font = HEADING_FONT).pack(side='top', anchor="nw",padx=HEADING_PADX)        
        self.band_selectO2A_button = tk.Button(band_select_frame,text='O2A',command = lambda: self.select_band('O2A'))
        self.band_selectO2A_button.pack(side='left', anchor="nw", padx = 10)
        self.band_selectH2O_button = tk.Button(band_select_frame,text='H2O',command = lambda: self.select_band('H2O'))
        self.band_selectH2O_button.pack(side='left', anchor="nw")
        band_select_frame.pack(side='top',fill='x', anchor="nw", padx = 10)
        #build buttons for wheel B
        frameB = tk.Frame(main_frame)
        tk.Label(frameB, text="Filter Wheel B (Band Pass)", font = HEADING_FONT).pack(anchor='w', padx=HEADING_PADX)
        for index, text in choicesB:
            tk.Radiobutton(frameB,
                           text=text,
                           padx = padxB, 
                           variable=self.varB, 
                           value=index).pack(side="top", anchor='w')
        #build buttons for wheel A
        frameA = tk.Frame(main_frame)
        tk.Label(frameA, text="Filter Wheel A (Auxiliary)", font = HEADING_FONT).pack(anchor='w', padx=HEADING_PADX)
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
        
    def select_band(self, band):
        if band == 'O2A':
            inactive_color = 'gray'
            self.band_selectO2A_button.config(state='disabled', bg='green')
            self.band_selectH2O_button.config(state='normal', bg= inactive_color)
            self.varBand.set('O2A')
        elif band == 'H2O':
            inactive_color = 'gray'
            self.band_selectH2O_button.config(state='disabled', bg='green')
            self.band_selectO2A_button.config(state='normal', bg= inactive_color)
            self.varBand.set('H2O')
        else:
            inactive_color = 'gray'
            self.band_selectO2A_button.config(state='normal', bg=inactive_color)
            self.band_selectH2O_button.config(state='normal', bg=inactive_color)
            self.varBand.set('(unknown)')

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
    
