###############################################################################
#Standard Python provided
import os, time, datetime, signal, socket, shelve, re
import Tkinter as tk
import ttk
#3rd party packages
from PIL import Image, ImageTk, ImageOps
import Pmw
from numpy import arange, savetxt
from FileDialog import SaveFileDialog
import scipy.misc
#Automat framework provided
from automat.core.gui.text_widgets           import TextDisplayBox
from automat.core.gui.pmw_custom.entry_form  import EntryForm
from automat.core.gui.pmw_custom.validation  import Validator
from automat.core.plotting.tk_embedded_plots import EmbeddedFigure
#yes_o2ab framework provided
from yes_o2ab.core.plotting.spectra          import RawSpectrumPlot
#application local
from capture_settings_dialog import CaptureSettingsDialog
from filter_select_dialog import FilterSelectDialog
###############################################################################
# Module Constants
from ..common_defs import FRAMETYPE_DEFAULT, EXPOSURE_TIME_DEFAULT,\
    RBI_NUM_FLUSHES_DEFAULT, RBI_EXPOSURE_TIME_DEFAULT, REPEAT_DELAY_DEFAULT,\
    FIELD_LABEL_FONT, HEADING_LABEL_FONT, SUBHEADING_LABEL_FONT

WINDOW_TITLE      = "YES O2AB Calibrate"
WAIT_DELAY        = 100 #milliseconds
TEXT_BUFFER_SIZE  = 10*2**20 #ten megabytes
SPECTRAL_FIGSIZE  = (6,5) #inches
MAX_IMAGESIZE     = (600,500)
LOOP_DELAY        = 100 #milliseconds

FINE_ADJUST_STEP_SIZE_DEFAULT = 10 #steps

CONFIRMATION_TEXT_DISPLAY_TEXT_HEIGHT = 40
CONFIRMATION_TEXT_DISPLAY_TEXT_WIDTH  = 80

SETTINGS_FILEPATH = os.path.expanduser("~/.yes_o2ab_calibrate_settings.db")

_empty_regex = re.compile('^$')
_positive_integer_regex = re.compile('^0|([1-9]\d*)$')
def positive_integer_validator(text):
    if _positive_integer_regex.match(text):
        return Pmw.OK
    elif _empty_regex.match(text):
        return Pmw.PARTIAL
    else:
        return Pmw.ERROR
    
###############################################################################
def IgnoreKeyboardInterrupt():
    """
    Sets the response to a SIGINT (keyboard interrupt) to ignore.
    """
    return signal.signal(signal.SIGINT,signal.SIG_IGN)

def NoticeKeyboardInterrupt():
    """
    Sets the response to a SIGINT (keyboard interrupt) to the
    default (raise KeyboardInterrupt).
    """
    return signal.signal(signal.SIGINT, signal.default_int_handler)

###############################################################################
#replacement dialog box, since Pmw.MessageDialog appears to mysteriously segfault
import Dialog

def launch_MessageDialog(title, message_text, buttons = ('OK',), bitmap='', default=0):
    d = tk.Dialog.Dialog(title=title, text = message_text, bitmap=bitmap, default=default, strings=buttons)
    return buttons[d.num]
      
###############################################################################
class GUI:
    def __init__(self, application):
        self.app = application
        self.app.print_comment("Starting GUI interface:")
        self.app.print_comment("please wait while the application loads...")
        #build the GUI interface as a seperate window
        win = tk.Tk()
        Pmw.initialise(win) #initialize Python MegaWidgets
        win.withdraw()
        win.wm_title(WINDOW_TITLE)
        win.focus_set() #put focus on this new window
        self.win = win
        #handle the user hitting the 'X' button
        self.win.protocol("WM_DELETE_WINDOW", self._close)
        #FIXME bind some debugging keystrokes to the window
        #self.win.bind('<Control-f>', lambda e: self.app.force_experiment())        
        #build the left panel
        left_panel = tk.Frame(win)
        #capture controls
        tk.Label(left_panel, text="Capture Controls:", font = HEADING_LABEL_FONT).pack(side='top',anchor="w")
        self.change_capture_settings_button = tk.Button(left_panel,text='Change Settings',command = self.change_capture_settings)
        self.change_capture_settings_button.pack(side='top',fill='x', anchor="sw")
        self._capture_mode = None
        self.capture_once_button = tk.Button(left_panel,text='Run Once',command = self.capture_once)
        self.capture_once_button.pack(side='top',fill='x', anchor="nw")
        self.capture_on_adjust_button = tk.Button(left_panel,text='Run on Adjust',command = self.capture_on_adjust)
        self.capture_on_adjust_button.pack(side='top',fill='x', anchor="nw")
        self.capture_continually_button  = tk.Button(left_panel,text='Run Continually',command = self.capture_continually)
        self.capture_continually_button.pack(side='top',fill='x', anchor="nw")
        self.stop_button = tk.Button(left_panel,text='Stop',command = self.stop, state='disabled')
        self.stop_button.pack(side='top',fill='x', anchor="nw")
        
        #optics controls
        tk.Label(left_panel, pady = 10).pack(side='top',fill='x', anchor="nw")
        tk.Label(left_panel, text="Optics Controls:", font = HEADING_LABEL_FONT).pack(side='top',anchor="w")
        self.flatfield_field = Pmw.EntryField(left_panel,
                                              labelpos='w',
                                              label_text=" flatfield:",
                                              label_font = FIELD_LABEL_FONT,
                                              entry_width=8,
                                              entry_state='readonly',
                                              )
        self.band_field = Pmw.EntryField(left_panel,
                                         labelpos='w',
                                         label_text="             band:",
                                         label_font = FIELD_LABEL_FONT,
                                         entry_width=9,
                                         entry_state='readonly',
                                        )
        self.band_field.pack(side='top', anchor="w", expand='no')
        self.filter_B_field = Pmw.EntryField(left_panel,
                                         labelpos='w',
                                         label_text="(B)and-pass filt.:",
                                         label_font = FIELD_LABEL_FONT,
                                         entry_width=9,
                                         entry_state='readonly',
                                        )
        self.filter_B_field.pack(side='top', anchor="w", expand='no')
        self.filter_A_field = Pmw.EntryField(left_panel,
                                         labelpos='w',
                                         label_text="(A)uxiliary filt.:",
                                         label_font = FIELD_LABEL_FONT,
                                         entry_width=9,
                                         entry_state='readonly',
                                        )
        self.filter_A_field.pack(side='top', anchor="w", expand='no')
        self.filter_position_field = Pmw.EntryField(left_panel,
                                         labelpos='w',
                                         label_text="filt. pos. (5B+A):",
                                         label_font = FIELD_LABEL_FONT,
                                         entry_width=9,
                                         entry_state='readonly',
                                        )
        self.filter_position_field.pack(side='top', anchor="w", expand='no')
        self.filter_select_button = tk.Button(left_panel,text='Band/Filter Select',command = self.filter_select)
        self.filter_select_button.pack(side='top',fill='x', anchor="nw")
        
        
        #band fine adjustment controls
        band_adjust_button_frame = tk.Frame(left_panel)
        tk.Label(band_adjust_button_frame, text="Band Fine Adjust:", font = SUBHEADING_LABEL_FONT).pack(side='top', anchor="nw")        
        self.band_adjustL_button = tk.Button(band_adjust_button_frame,text='<--',command = lambda: self.band_adjust('-1'))
        self.band_adjustL_button.pack(side='left', anchor="nw")
        self.band_adjustR_button = tk.Button(band_adjust_button_frame,text='-->',command = lambda: self.band_adjust('+1'))
        self.band_adjustR_button.pack(side='left', anchor="nw")
        band_adjust_button_frame.pack(side='top',fill='x', anchor="nw")
        self.band_adjust_stepsize_field = Pmw.EntryField(left_panel,
                                                         labelpos='w',
                                                         label_text="step size:",
                                                         label_font = FIELD_LABEL_FONT,
                                                         value = FINE_ADJUST_STEP_SIZE_DEFAULT,
                                                         entry_width=4,
                                                         validate = positive_integer_validator,
                                                         )
        self.band_adjust_stepsize_field.pack(side='top', anchor="w", expand='no')
        self.band_adjust_position_field = Pmw.EntryField(left_panel,
                                                         labelpos='w',
                                                         label_text=" position:",
                                                         label_font = FIELD_LABEL_FONT,
                                                         entry_width=8,
                                                         entry_state='readonly',
                                                         )
        self.band_adjust_position_field.pack(side='top', anchor="w", expand='no')
        
        #focus adjustment controls
        focus_adjust_button_frame = tk.Frame(left_panel)
        tk.Label(focus_adjust_button_frame, text="Focus Adjust:", font = SUBHEADING_LABEL_FONT).pack(side='top', anchor="nw")        
        self.focus_adjustL_button = tk.Button(focus_adjust_button_frame,text='<--',command = lambda: self.focus_adjust('-1'))
        self.focus_adjustL_button.pack(side='left', anchor="nw")
        self.focus_adjustR_button = tk.Button(focus_adjust_button_frame,text='-->',command = lambda: self.focus_adjust('+1'))
        self.focus_adjustR_button.pack(side='left', anchor="nw")
        focus_adjust_button_frame.pack(side='top',fill='x', anchor="nw")
        self.focus_adjust_stepsize_field = Pmw.EntryField(left_panel,
                                                          labelpos='w',
                                                          label_text="step size:",
                                                          label_font = FIELD_LABEL_FONT,
                                                          value = FINE_ADJUST_STEP_SIZE_DEFAULT,
                                                          entry_width=4,
                                                          validate = positive_integer_validator,
                                                          )
        self.focus_adjust_stepsize_field.pack(side='top', anchor="w", expand='no')
        self.focus_adjust_position_field = Pmw.EntryField(left_panel,
                                                          labelpos='w',
                                                          label_text=" position:",
                                                          label_font = FIELD_LABEL_FONT,
                                                          entry_width=8,
                                                          entry_state='readonly',
                                                          )
        self.focus_adjust_position_field.pack(side='top', anchor="w", expand='no')
        
        #flat field
#        flatfield_pos_frame = tk.Frame(left_panel)
#        tk.Label(flatfield_pos_frame, text="Flat Field Pos.:", font = "Helvetica 10 bold").pack(side='top', anchor="nw")        
#        self.flatfield_posIN_button = tk.Button(flatfield_pos_frame,text='IN',command = lambda: self.set_flatfield(True))
#        self.flatfield_posIN_button.pack(side='left', anchor="nw")
#        self.flatfield_posOUT_button = tk.Button(flatfield_pos_frame,text='OUT',command = lambda: self.set_flatfield(False))
#        self.flatfield_posOUT_button.pack(side='left', anchor="nw")
#        flatfield_pos_frame.pack(side='top',fill='x', anchor="nw")
                          
        left_panel.pack(fill='y',expand='no',side='left', padx = 10)
        #build the middle panel - a tabbed notebook
        mid_panel = tk.Frame(win)
        nb        = ttk.Notebook(mid_panel)
        nb.pack(fill='both', expand='yes',side='right')
        tab1 = tk.Frame(nb)
        tab2 = tk.Frame(nb)
        nb.add(tab1, text="Raw Spectrum Display")
        nb.add(tab2, text="Raw Image Display")
        #create an tk embedded figure for spectral display
        self.spectral_plot_template = RawSpectrumPlot()
        self.spectral_figure_widget = EmbeddedFigure(tab1, figsize=SPECTRAL_FIGSIZE)
        self.spectral_figure_widget.pack(side='top',fill='both', expand='yes')
        self.replot_spectrum_button = tk.Button(tab1,text='Replot Spectrum',command = self.replot_spectrum, state='disabled')
        self.replot_spectrum_button.pack(side='bottom',anchor="sw")
        self.export_spectrum_button = tk.Button(tab1,text='Export Spectrum',command = self.export_spectrum, state='disabled')
        self.export_spectrum_button.pack(side='left',anchor="sw")
        #create a tk Label widget for image display
        self.photo_label_widget = tk.Label(tab2)
        self.photo_label_widget.pack(side='top',fill='both', expand='yes')
        self.save_image_button = tk.Button(tab2,text='Save Image',command = self.save_image, state='disabled')
        self.save_image_button.pack(side='bottom',anchor="sw")
        mid_panel.pack(fill='both', expand='yes',side='left')
        #build the right panel
        right_panel = tk.Frame(win)
        self.text_display  = TextDisplayBox(right_panel,text_height=15, buffer_size = TEXT_BUFFER_SIZE)
        self.text_display.pack(side='left',fill='both',expand='yes')
        right_panel.pack(fill='both', expand='yes',side='right')
        
        #build the filter selection dialog
        self.filter_select_dialog = FilterSelectDialog(
                                                       parent = self.win, 
                                                       choicesB = self.app.filter_B_types,
                                                       choicesA = self.app.filter_A_types,
                                                       )
        self.filter_select_dialog.withdraw()
        #build the confirmation dialog
        self.capture_settings_dialog = CaptureSettingsDialog(self.win)
        self.capture_settings_dialog.withdraw()
        self._load_settings()
        
    def launch(self):
        #run the GUI handling loop
        IgnoreKeyboardInterrupt()
        #get metadata from devices to update the fields
        md = self.app.query_metadata()
        self._update_fields(md)
        #reveal the main window
        self.win.deiconify()
        self.win.mainloop()
        NoticeKeyboardInterrupt()   
    
    def busy(self):
        self.disable_buttons()
        self.win.config(cursor="watch")
        
    def not_busy(self):
        self.enable_buttons()
        self.win.config(cursor="")
        
    def disable_buttons(self):
        self.change_capture_settings_button.configure(state="disabled")
        self.capture_continually_button.configure(state="disabled")
        #self.stop_button.configure(state="disabled")
        self.capture_once_button.configure(state="disabled")
        self.capture_on_adjust_button.configure(state="disabled")
        self.filter_select_button.configure(state="disabled")
        self.band_adjustL_button.configure(state="disabled")
        self.band_adjustR_button.configure(state="disabled")
        self.focus_adjustL_button.configure(state="disabled")
        self.focus_adjustR_button.configure(state="disabled")
#        self.flatfield_posIN_button.configure(state="disabled")
#        self.flatfield_posOUT_button.configure(state="disabled")
        self.replot_spectrum_button.configure(state="disabled")
        self.export_spectrum_button.configure(state="disabled")
        self.save_image_button.configure(state="disabled")
        
    def enable_buttons(self):
        self.change_capture_settings_button.configure(state="normal")
        self.capture_continually_button.configure(state="normal")
        #self.stop_button.configure(state="normal")
        self.capture_once_button.configure(state="normal")
        self.capture_on_adjust_button.configure(state="normal")
        self.filter_select_button.configure(state="normal")
        self.band_adjustL_button.configure(state="normal")
        self.band_adjustR_button.configure(state="normal")
        self.focus_adjustL_button.configure(state="normal")
        self.focus_adjustR_button.configure(state="normal")
#        self.flatfield_posIN_button.configure(state="normal")
#        self.flatfield_posOUT_button.configure(state="normal")
        self.replot_spectrum_button.configure(state="normal")
        self.export_spectrum_button.configure(state="normal")
        self.save_image_button.configure(state="normal")
       
    

    def change_capture_settings(self):
        self.app.print_comment("changing capture settings...")
        self.capture_settings_dialog.activate()
        
    def capture_once(self):
        #prevent multiple presses
        self.capture_once_button.configure(state='disabled')
        #get parameters
        frametype         = self.capture_settings_dialog.frametype_var.get()
        exposure_time     = int(self.capture_settings_dialog.form['exposure_time'])
        rbi_num_flushes   = int(self.capture_settings_dialog.form['rbi_num_flushes'])
        rbi_exposure_time = int(self.capture_settings_dialog.form['rbi_exposure_time'])
        repeat_delay      = int(self.capture_settings_dialog.form['repeat_delay'])
        self.app.print_comment("Capturing image:")
        #acquire image and process into rudimentary spectrum
        self.app.print_comment("\texposing for %d milliseconds..." % (exposure_time,))
        self.app.acquire_image(frametype         = frametype,
                               exposure_time     = exposure_time,
                               rbi_num_flushes   = rbi_num_flushes,
                               rbi_exposure_time = rbi_exposure_time,
                               blocking = False)
        #self.busy()
        self.win.after(LOOP_DELAY,self._wait_on_capture_loop)
        
    def _wait_on_capture_loop(self):
        image_capture = self.app.load_controller('image_capture')
        #read out all pending events
        while not image_capture.event_queue.empty():
            event, info = image_capture.event_queue.get()
            self.print_event(event,info)
            if  event == "FILTER_SWITCHER_STARTED":
                #filter is changing like in the 'opaque' frametype
                self._update_filter_status(None)
            elif event == "FILTER_SWITCHER_COMPLETED":
               md = self.app.query_filter_status()
               self._update_filter_status(md)
        if image_capture.thread_isAlive(): 
            #reschedule loop
            self.win.after(LOOP_DELAY,self._wait_on_capture_loop)
        else:
            #finish up
            #md = self.app.last_capture_metadata.copy()
            md = self.app.query_metadata.copy()
            self._update_fields(md)
            #self.not_busy()
            self.capture_once_button.configure(state='normal')
            self.app.print_comment("capture completed")
            self.app.compute_spectrum()
            S = self.app.last_spectrum
            I = self.app.last_image
            self._update_spectral_plot(S)
            self._update_image(I)
            self.replot_spectrum_button.config(state='normal') #data can now be replotted
            self.export_spectrum_button.config(state='normal') #data can now be exported
            self.save_image_button.config(state='normal')      #data can now be exported
    
    def capture_on_adjust(self):
        if self._capture_mode == "on_adjust": #toggle it off
            self.capture_on_adjust_button.config(bg='light gray', relief="raised")
            self._capture_mode = None
        else: #toggle it on
            self.capture_on_adjust_button.config(bg='green', relief="sunken")
            self.capture_continually_button.config(state='normal', bg='light gray', relief="raised")
            self.stop_button.config(state='disabled')
            self._capture_mode = "on_adjust"
        self.stop_button.config(state='normal')
        
     
    def capture_continually(self):
        #disable all the buttons, except the stop button
        self.capture_once_button.config(state='disabled')
        self.capture_on_adjust_button.config(state='disabled', bg='light gray', relief="raised")
        self.capture_continually_button.config(state='disabled', bg='green', relief="sunken")
        self.stop_button.config(state='normal')
        self._capture_mode = "continual"
        #get parameters
        frametype         = self.capture_settings_dialog.frametype_var.get()
        exposure_time     = int(self.capture_settings_dialog.form['exposure_time'])
        rbi_num_flushes   = int(self.capture_settings_dialog.form['rbi_num_flushes'])
        rbi_exposure_time = int(self.capture_settings_dialog.form['rbi_exposure_time'])
        repeat_delay      = int(self.capture_settings_dialog.form['repeat_delay'])
        #set up the image capture controller in loop mode
        image_capture = self.app.load_controller('image_capture')
        image_capture.set_configuration(frametype         = frametype,
                                        num_captures      = None, #will cause infinite loop
                                        exposure_time     = exposure_time,
                                        rbi_num_flushes   = rbi_num_flushes,
                                        rbi_exposure_time = rbi_exposure_time,
                                        repeat_delay      = repeat_delay,
                                       )
        self.app.print_comment("Starting image capture loop with repeat delay %d seconds." % (repeat_delay,))
        image_capture.start() #should not block
        #schedule loop
        self._capture_continually_loop()
        

    def _capture_continually_loop(self):
        image_capture = self.app.load_controller('image_capture')
        #read out all pending events
        while not image_capture.event_queue.empty():
            event, info = image_capture.event_queue.get()
            self.print_event(event,info)
            if event == "IMAGE_CAPTURE_EXPOSURE_COMPLETED":
                #grab the image, comput the spectrum, then update them
                I = info['image_array']
                S = self.app.compute_spectrum(I)
                self._update_spectral_plot(S)
                self._update_image(I)
                self.replot_spectrum_button.config(state='normal') #data can now be replotted
                self.export_spectrum_button.config(state='normal') #data can now be exported
                self.save_image_button.config(state='normal')      #data can now be exported
        #reschedule loop
        if image_capture.thread_isAlive():  #wait for the capture to finish, important!
            self.win.after(LOOP_DELAY,self._capture_continually_loop)
        else:
            #finish up
            md = self.app.query_metadata()
            self._update_fields(md)
            #enable all the buttons, except the stop button
            self.capture_once_button.config(state='normal')
            self.capture_on_adjust_button.config(state='normal', bg='light gray', relief = 'raised')
            self.capture_continually_button.config(state='normal', bg='light gray', relief = 'raised')
            self.stop_button.config(state='disabled')
            #do not reschedule loop

    def stop(self):
        image_capture = self.app.load_controller('image_capture')
        image_capture.stop()
        self._capture_mode = None
    
    def filter_select(self):
        self.app.print_comment("Selecting filter:")
        #self._update_fields() #FIXME does this need to be done?
        choice = self.filter_select_dialog.activate()
        if choice == 'OK':
            self._set_band_and_filter_pos()
        else:
            self.app.print_comment("cancelled.")


    def _set_band_and_filter_pos(self):
        new_band = self.filter_select_dialog.varBand.get()
        B = self.filter_select_dialog.varB.get()
        A = self.filter_select_dialog.varA.get()
        pos = 5*B + A
        filter_B_type = self.app.filter_B_types[B][1]
        #if no explicit choice was made, choose based on B filter_select
        if (new_band == '(unknown)') and (B == 1 or B == 2): 
            if   B == 1:
                default_band = 'O2A'
            elif B == 2:
                default_band = 'H2O'
            msg = "The band state was (unknown), but the '%s' filter was selected, should we set the band state to '%s'?" % (filter_B_type,default_band)
            dlg = Pmw.MessageDialog(parent = self.win,
                                    message_text = msg,
                                    buttons = ('OK','Cancel'),
                                    defaultbutton = 'OK',
                                    title = "Unknown Band Warning",
                                    )
            choice = dlg.activate()
            dlg.deactivate()
            if choice == 'OK':
                self.app.print_comment("Defaulting band selection.")
                new_band = default_band
            elif choice == 'Cancel':
                self.app.print_comment("Forcing through '(unknown)' band state.")  
        #this is a conflict
        elif (new_band == '(unknown)') or (new_band == 'O2A' and B == 2) or (new_band == 'H2O' and B == 1):      #conflict
            if new_band == '(unknown)':
                msg = "Warning: the band state is '%s', please 'Retry' or 'Force' the selection." % new_band
            else:
                msg = "Warning: the band state '%s' is in conflict with the filter selection '%s', please 'Retry' or 'Force' the selection." % (new_band,filter_B_type)
            dlg = Pmw.MessageDialog(parent = self.win,
                                    message_text = msg,
                                    buttons = ('Retry','Force'),
                                    defaultbutton = 'Retry',
                                    title = "Unknown Band Warning",
                                    )
            choice = dlg.activate()
            dlg.deactivate()
            if choice == 'Retry':
                self.app.print_comment("Retrying selection.")
                self.filter_select_dialog.deactivate()
                self.filter_select()
                #do not run the rest of this function on recursive return!
                return
            elif choice == 'Force':
                self.app.print_comment("forcing through '(unknown)' band state.")
        #throw up a busy message
        msg = "Please wait while the band is switched to '%s' and the filter is switched to position %d..." % (new_band,pos)
        self.busy()
        self.wait_msg_window = tk.Toplevel(self.win)
        tk.Label(self.wait_msg_window,text=msg).pack(fill="both",expand="yes", padx=1,pady=1)
        # get screen width and height
        ws = self.win.winfo_screenwidth()
        hs = self.win.winfo_screenheight()
        w = ws/2
        h = hs/4
        # calculate position x, y
        x = (ws/2) - (w/2)
        y = (hs/2) - (h/2)
        self.wait_msg_window.geometry("%dx%d+%d+%d" % (w,h,x,y))
        self.wait_msg_window.update()
        self.wait_msg_window.lift()
        self.wait_msg_window.grab_set()
        self.app.print_comment(msg)
        #get the current settings
        band_switcher = self.app.config.load_controller('band_switcher')
        curr_band = band_switcher.band
        #change band state if specified
        if (new_band != '(unknown)') and (curr_band != new_band):
            #change the band
            self.band_field.setvalue("(changing)")
            self.app.print_comment("changing band from '%s' to '%s'... (thread)" % (curr_band,new_band))
            self.app.select_band(new_band, blocking = False) #threaded!
        else:
            self.app.print_comment("not changing band")
        #change the filter position
        self.filter_position_field.setvalue("(changing)")
        self.filter_B_field.setvalue("(changing)")
        self.filter_A_field.setvalue("(changing)")
        self.app.print_comment("changing filter wheel to position %d... (thread)" % pos)
        self.app.select_filter(pos, blocking = False) #threaded!
        #now wait for the parts to move
        self._wait_on_band_and_filter_change_loop()
        
    def _wait_on_band_and_filter_change_loop(self):
        #check the controller states
        band_switcher   = self.app.load_controller('band_switcher')
        filter_switcher = self.app.load_controller('filter_switcher')
        #read out all pending events
        while not band_switcher.event_queue.empty():
            event, info = band_switcher.event_queue.get()
            self.print_event(event,info)
        while not filter_switcher.event_queue.empty():
            event, info = filter_switcher.event_queue.get()
            self.print_event(event,info)
        #check thread state
        if band_switcher.thread_isAlive() or filter_switcher.thread_isAlive():
            #reschedule loop
            self.win.after(LOOP_DELAY,self._wait_on_band_and_filter_change_loop)
        else:
            #finish up
            md = self.app.query_metadata()
            self._update_fields(md)
            self.not_busy()
            self.app.print_comment("finished")
            self.wait_msg_window.destroy()
            self.filter_select_dialog.deactivate()
            
    def band_adjust(self, step_direction):
        curr_band = self.band_field.getvalue()
        #handle unknown band state
        if curr_band == '(unknown)':
            msg = "Warning: the band state is '%s', please select from 'Band/Filter Selection' dialog" % curr_band
            dlg = Pmw.MessageDialog(parent = self.win,
                                    message_text = msg,
                                    buttons = ('OK',),
                                    defaultbutton = 'OK',
                                    title = "Unknown Band Warning",
                                    )
            choice = dlg.activate()
            if choice == 'OK':
                self.filter_select_button.invoke()
                return #important must exit here 
            else:
                return
        #schedule the adjustment
        #get the stepsize from the field
        step_size = int(self.band_adjust_stepsize_field.getvalue())
        step = None
        if step_direction == "+1":
            step = step_size
        elif step_direction == "-1": 
            step = -step_size
        self.app.print_comment("adjust the band by step: %s" % step)
        self.band_adjust_position_field.configure(entry_fg = "dark gray")
        self.busy()
        self.app.adjust_band(step, blocking = False) #don't block
        self._wait_on_band_adjust_loop()
        
    def _wait_on_band_adjust_loop(self):
        #check the controller states
        band_adjuster  = self.app.load_controller('band_adjuster')
        #read out all pending events
        while not band_adjuster.event_queue.empty():
            event, info = band_adjuster.event_queue.get()
            self.print_event(event,info)
            if event == 'BAND_ADJUSTER_STEP_POLL':
                position = info['position']
                self.band_adjust_position_field.setvalue(position)
        #check thread state
        if band_adjuster.thread_isAlive():
            #reschedule loop
            self.win.after(LOOP_DELAY,self._wait_on_band_adjust_loop)
        else:
            #finish up
            md = self.app.query_metadata()
            self._update_fields(md)
            self.band_adjust_position_field.configure(entry_fg = "black")
            self.not_busy()
            self.app.print_comment("finished")
            if self._capture_mode == "on_adjust":
                self.capture_once()
        
    def focus_adjust(self, step_direction):
        #get the stepsize from the field
        step_size = self.focus_adjust_stepsize_field.getvalue()
        step_size = int(step_size)
        step = None
        if step_direction == "+1":
            step = step_size
        elif step_direction == "-1": 
            step = -step_size
        self.app.print_comment("adjust the focus by step: %s" % step)
        self.focus_adjust_position_field.configure(entry_fg = "dark gray")
        self.busy()
        self.app.adjust_focus(step, blocking = False) #don't block
        self._wait_on_focus_adjust_loop()
        
    def _wait_on_focus_adjust_loop(self):
        #check the controller states
        focus_adjuster  = self.app.load_controller('focus_adjuster')
        #read out all pending events
        while not focus_adjuster.event_queue.empty():
            event, info = focus_adjuster.event_queue.get()
            self.print_event(event,info)
            if event == 'FOCUS_ADJUSTER_STEP_POLL':
                position = info['position']
                self.focus_adjust_position_field.setvalue(position)
        #check thread state
        if focus_adjuster.thread_isAlive():
            #reschedule loop
            self.win.after(LOOP_DELAY,self._wait_on_focus_adjust_loop)
        else:
            md = self.app.query_metadata()
            self._update_fields(md)
            self.focus_adjust_position_field.configure(entry_fg = "black")
            self.not_busy()
            self.app.print_comment("finished")
            if self._capture_mode == "on_adjust":
                self.capture_once()

    def export_spectrum(self):
        self.app.print_comment("Exporting data...")
        dt_now = datetime.datetime.utcnow()
        dt_now_str = dt_now.strftime("%Y-%m-%d-%H_%m_%S")
        #get some metadata for title
        frametype = self.app.last_capture_metadata['frametype']
        exptime   = int(self.app.last_capture_metadata['exposure_time'])
        default_filename = "%s_raw_spectrum-%s_exptime=%dms.csv" % (dt_now_str,frametype,exptime) 
        fdlg = SaveFileDialog(self.win,title="Save Raw Spectrum Data")
        userdata_path = self.app.config['paths']['data_dir']    

        filename = fdlg.go(dir_or_file = userdata_path, 
                           pattern="*.csv", 
                           default=default_filename, 
                           key = None
                          )
        if filename:
            self.app.export_spectrum(filename)
        self.app.print_comment("finished")

    def save_image(self):
        self.app.print_comment("saving image...")
        dt_now = datetime.datetime.utcnow()
        dt_now_str = dt_now.strftime("%Y-%m-%d-%H_%m_%S")
        #get some metadata for title
        frametype = self.app.last_capture_metadata['frametype']
        exptime   = int(self.app.last_capture_metadata['exposure_time'])
        default_filename = "%s_raw_image-%s_exptime=%dms.png" % (dt_now_str,frametype,exptime) 
        fdlg = SaveFileDialog(self.win,title="Save Raw Spectrum Data")
        #ws = self.win.winfo_screenwidth()
        #hs = self.win.winfo_screenheight()
        #w = ws/2
        #h = hs/4
        ## calculate position x, y
        #x = (ws/2) - (w/2)
        #y = (hs/2) - (h/2)
        #fdlg.geometry("%dx%d+%d+%d" % (w,h,x,y))
        userdata_path = self.app.config['paths']['data_dir']    
        filename = fdlg.go(dir_or_file = userdata_path, 
                           pattern="*.png", 
                           default=default_filename, 
                           key = None
                          )
        if filename:
            I = self.app.last_image
            img = scipy.misc.toimage(I,mode='I') #convert  to 16-bit greyscale
            img.save(filename)
            
    def replot_spectrum(self):
        self.spectral_plot_template._has_been_plotted = False
        S = self.app.last_spectrum
        self._update_spectral_plot(S)
    
    def _update_spectral_plot(self, S):
        figure        = self.spectral_figure_widget.get_figure()        
        plot_template = self.spectral_plot_template
        #get some metadata for plot formatting
        frametype = self.app.last_capture_metadata['frametype']
        exptime   = int(self.app.last_capture_metadata['exposure_time'])
        title     = "Raw Spectrum (%s, %d ms)" % (frametype, exptime)
        self.spectral_plot_template.configure(title=title)
        if not plot_template.has_been_plotted(): 
            self.app.print_comment("Replotting the spectrum.")
            figure.clear()
            Xs = [arange(len(S))]
            Ys = [S]
            plot_template.plot(Xs, Ys,figure = figure)
            self.spectral_figure_widget.update()
        else:
            self.app.print_comment("Updating spectrum data.")
            #get the plot line from the figure FIXME is there an easier way?
            line = figure.axes[0].lines[0]
            line.set_ydata(S)
            figure.axes[0].set_title(title)
            self.spectral_figure_widget.update()
            
    def _update_image(self, I):
        #downsample to 8-bit for display
        I2 = (I/2**8).astype('uint8')
        disp_img = Image.fromarray(I2)
        x,y = disp_img.size
        scale = min(MAX_IMAGESIZE[0]/float(x),MAX_IMAGESIZE[1]/float(y))
        new_size = (int(x*scale),int(y*scale))
        disp_img.thumbnail(new_size, Image.ANTIALIAS)       
        disp_img = ImageOps.autocontrast(disp_img)
        self.last_image_data    = I        
        self.last_image_display = disp_img
        self.last_photo = photo = ImageTk.PhotoImage(disp_img) #keep the reference
        self.photo_label_widget.config(image = photo)          #update the widget
    
    def _update_filter_status(self, md):
        if md is None:
            self.filter_position_field.setvalue("(changing)")
            self.filter_B_field.setvalue("(changing)")
            self.filter_A_field.setvalue("(changing)")
        else:
            self.filter_position_field.setvalue(str(md['filt_pos']))
            B = md['filt_B_num']
            A = md['filt_A_num']
            B_type = md['filt_B_type']
            A_type = md['filt_A_type']
            B_label = "%d, \"%s\"" % (B,B_type)
            A_label = "%d, \"%s\"" % (A,A_type)
            self.filter_B_field.setvalue(B_label)
            self.filter_A_field.setvalue(A_label)
            self.filter_select_dialog.varB.set(B)
            self.filter_select_dialog.varA.set(A)
        
        
    def _update_fields(self, md):
        self._update_filter_status(md)
        band = md['band']
        self.band_field.setvalue(band)
        if band in ['O2A','H2O']:
            self.filter_select_dialog.select_band(band)
        band_adjust_pos = md['band_adjust_pos']
        if band_adjust_pos is None:
            band_adjust_pos = "(unknown)"
        self.band_adjust_position_field.setvalue(str(band_adjust_pos))
        focuser_pos = md['focuser_pos']
        self.focus_adjust_position_field.setvalue(str(focuser_pos))

    def print_to_text_display(self, text, eol='\n'):
        self.text_display.print_text(text, eol=eol) 
        
    def print_event(self, event, info = {}):
        buff = ["%s:" % event]
        for key,val in info.items():
            buff.append("%s: %s" % (key,val))
        buff = "\n".join(buff)
        self.print_to_text_display(buff)

    def _load_settings(self):
        if os.path.exists(SETTINGS_FILEPATH):
            self.app.print_comment("loading from settings file '%s'" % SETTINGS_FILEPATH)
            settings = shelve.open(SETTINGS_FILEPATH)
            self.capture_settings_dialog.frametype_var.set(FRAMETYPE_DEFAULT) #always load this as default
            self.capture_settings_dialog.form['exposure_time']     = settings.get('exposure_time'    , EXPOSURE_TIME_DEFAULT)
            self.capture_settings_dialog.form['rbi_num_flushes']   = settings.get('rbi_num_flushes'  , RBI_NUM_FLUSHES_DEFAULT)
            self.capture_settings_dialog.form['rbi_exposure_time'] = settings.get('rbi_exposure_time', RBI_EXPOSURE_TIME_DEFAULT)
            self.capture_settings_dialog.form['repeat_delay']      = settings.get('repeat_delay'     , REPEAT_DELAY_DEFAULT)
            settings.close() 
        else:
            self.app.print_comment("failed to find settings file '%s'" % SETTINGS_FILEPATH)
                  
    def _cache_settings(self):
        self.app.print_comment("caching to settings file '%s'" % SETTINGS_FILEPATH)
        settings = shelve.open(SETTINGS_FILEPATH)
        #settings['frametype']         = self.capture_settings_dialog.frametype_var.get()
        settings['exposure_time']     = self.capture_settings_dialog.form['exposure_time']
        settings['rbi_num_flushes']   = self.capture_settings_dialog.form['rbi_num_flushes']
        settings['rbi_exposure_time'] = self.capture_settings_dialog.form['rbi_exposure_time']
        settings['repeat_delay']      = self.capture_settings_dialog.form['repeat_delay']
        settings.close()
        
            
    def _close(self):
        #abort all active controllers
        image_capture = self.app.load_controller('image_capture')
        image_capture.abort()
        #cache the GUI settings FIXME - is this necessary?
        self._cache_settings()
        self.win.destroy()
