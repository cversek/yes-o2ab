###############################################################################
#Standard Python provided
import os, time, datetime, signal, socket, shelve
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
from settings_dialog import SettingsDialog
from filter_select_dialog import FilterSelectDialog
###############################################################################
# Module Constants
WINDOW_TITLE      = "YES O2AB Calibrate"
WAIT_DELAY        = 100 #milliseconds
TEXT_BUFFER_SIZE  = 10*2**20 #ten megabytes
SPECTRAL_FIGSIZE  = (6,5) #inches
MAX_IMAGESIZE     = (600,500)
LOOP_DELAY        = 100 #milliseconds

DEFAULT_EXPOSURE_TIME = 10 #milliseconds
DEFAULT_CAPTURE_INTERVAL  = 10 #seconds
FINE_ADJUST_STEP_SIZE_DEFAULT = 10 #steps

CONFIRMATION_TEXT_DISPLAY_TEXT_HEIGHT = 40
CONFIRMATION_TEXT_DISPLAY_TEXT_WIDTH  = 80

FIELD_LABEL_FONT = "Courier 10 normal"

SETTINGS_FILEPATH = os.path.expanduser("~/.yes_o2ab_calibrate_settings.db")
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
        tk.Label(left_panel, text="Capture Controls:", font = "Helvetica 14 bold").pack(side='top',anchor="w")
        self.change_settings_button = tk.Button(left_panel,text='Change Settings',command = self.change_settings)
        self.change_settings_button.pack(side='top',fill='x', anchor="sw")
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
        tk.Label(left_panel, text="Optics Controls:", font = "Helvetica 14 bold").pack(side='top',anchor="w")
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
        tk.Label(band_adjust_button_frame, text="Band Fine Adjust:", font = "Helvetica 10 bold").pack(side='top', anchor="nw")        
        self.band_adjustL_button = tk.Button(band_adjust_button_frame,text='<--',command = lambda: self.band_adjust('L'))
        self.band_adjustL_button.pack(side='left', anchor="nw")
        self.band_adjustR_button = tk.Button(band_adjust_button_frame,text='-->',command = lambda: self.band_adjust('R'))
        self.band_adjustR_button.pack(side='left', anchor="nw")
        band_adjust_button_frame.pack(side='top',fill='x', anchor="nw")
        self.band_adjust_stepsize_field = Pmw.EntryField(left_panel,
                                                         labelpos='w',
                                                         label_text="step size:",
                                                         label_font = FIELD_LABEL_FONT,
                                                         value = FINE_ADJUST_STEP_SIZE_DEFAULT,
                                                         entry_width=4,
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
        tk.Label(focus_adjust_button_frame, text="Focus Adjust:", font = "Helvetica 10 bold").pack(side='top', anchor="nw")        
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
        
        #white field
        flatfield_pos_frame = tk.Frame(left_panel)
        tk.Label(flatfield_pos_frame, text="Flat Field Pos.:", font = "Helvetica 10 bold").pack(side='top', anchor="nw")        
        self.flatfield_posIN_button = tk.Button(flatfield_pos_frame,text='IN',command = lambda: self.set_flatfield(True))
        self.flatfield_posIN_button.pack(side='left', anchor="nw")
        self.flatfield_posOUT_button = tk.Button(flatfield_pos_frame,text='OUT',command = lambda: self.set_flatfield(False))
        self.flatfield_posOUT_button.pack(side='left', anchor="nw")
        flatfield_pos_frame.pack(side='top',fill='x', anchor="nw")
                          
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
        self.export_spectrum_button = tk.Button(tab1,text='Export Spectrum',command = self.export_spectrum, state='disabled')
        self.export_spectrum_button.pack(side='bottom',anchor="sw")
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
        self.settings_dialog = SettingsDialog(self.win)
        self.settings_dialog.withdraw()
        self._load_settings()
        
    def launch(self):
        #run the GUI handling loop
        IgnoreKeyboardInterrupt()
        self.update_fields()
        self.win.deiconify()
        self.win.mainloop()
        NoticeKeyboardInterrupt()   
        
    def update_fields(self):
        md = self.app.query_metadata()
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
        band = md['band']
        self.band_field.setvalue(band)
        if band in ['O2A','H2O']:
            self.filter_select_dialog.select_band(band)
        focuser_pos = md['focuser_pos']
        self.focus_adjust_position_field.setvalue(str(focuser_pos))
    
    def busy(self):
        self.disable_buttons()
        self.win.config(cursor="watch")
        
    def not_busy(self):
        self.enable_buttons()
        self.win.config(cursor="")
        
    def disable_buttons(self):
        self.change_settings_button.configure(state="disabled")
        self.capture_continually_button.configure(state="disabled")
        #self.stop_button.configure(state="disabled")
        self.capture_once_button.configure(state="disabled")
        self.capture_on_adjust_button.configure(state="disabled")
        self.filter_select_button.configure(state="disabled")
        self.band_adjustL_button.configure(state="disabled")
        self.band_adjustR_button.configure(state="disabled")
        self.focus_adjustL_button.configure(state="disabled")
        self.focus_adjustR_button.configure(state="disabled")
        self.flatfield_posIN_button.configure(state="disabled")
        self.flatfield_posOUT_button.configure(state="disabled")
        self.export_spectrum_button.configure(state="disabled")
        self.save_image_button.configure(state="disabled")
        
    def enable_buttons(self):
        self.change_settings_button.configure(state="normal")
        self.capture_continually_button.configure(state="normal")
        #self.stop_button.configure(state="normal")
        self.capture_once_button.configure(state="normal")
        self.filter_select_button.configure(state="normal")
        self.band_adjustL_button.configure(state="normal")
        self.band_adjustR_button.configure(state="normal")
        self.focus_adjustL_button.configure(state="normal")
        self.focus_adjustR_button.configure(state="normal")
        self.flatfield_posIN_button.configure(state="normal")
        self.flatfield_posOUT_button.configure(state="normal")
        self.export_spectrum_button.configure(state="normal")
        self.save_image_button.configure(state="normal")
       
    

    def change_settings(self):
        self.app.print_comment("changing capture settings...")
        self.settings_dialog.activate()
    
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
        capture_interval = int(1000*float(self.settings_dialog.form['capture_interval'])) #convert to milliseconds
        #reschedule loop            
        self.win.after(capture_interval,self._capture_continually_loop)

    def _capture_continually_loop(self):
        if self._capture_mode == "continual":
            self.capture_once()
            capture_interval = int(1000*float(self.settings_dialog.form['capture_interval'])) #convert to milliseconds
            #reschedule loop            
            self.win.after(capture_interval,self._capture_continually_loop)
        else:
            #enable all the buttons, except the stop button
            self.capture_once_button.config(state='normal')
            self.capture_on_adjust_button.config(state='normal', bg='light gray', relief = 'raised')
            self.capture_continually_button.config(state='normal', bg='light gray', relief = 'raised')
            self.stop_button.config(state='disabled')
            #do not reschedule loop
            

    def capture_once(self):
        exptime = int(self.settings_dialog.form['exposure_time'])
        self.app.print_comment("Acquiring spectrum.")
        #acquire image and process into rudimentary spectrum
        self.app.print_comment("Exposing for %d milliseconds..." % (exptime,), eol='')
        self.app.acquire_image(exptime=exptime, blocking = False)
        #self.busy()
        #prevent multiple presses
        self.capture_once_button.configure(state='disabled')
        self.win.after(LOOP_DELAY,self._wait_on_capture_loop)
        
    def _wait_on_capture_loop(self):
        image_capture = self.app.load_controller('image_capture')
        if image_capture.thread_isAlive(): 
            #reschedule loop
            self.win.after(LOOP_DELAY,self._wait_on_capture_loop)
        else:
            self.update_fields()
            #self.not_busy()
            self.capture_once_button.configure(state='normal')
            self.app.print_comment("completed")
            self.app.compute_spectrum()
            S = self.app.last_spectrum
            I = self.app.last_image
            self._update_spectral_plot(S)
            self._update_image(I)
            self.export_spectrum_button.config(state='normal') #data can now be exported
            self.save_image_button.config(state='normal') #data can now be exported
        

    def stop(self):
        self._capture_mode = None
    
    def filter_select(self):
        self.app.print_comment("Selecting filter:")
        self.update_fields()
        choice = self.filter_select_dialog.activate()
        if choice == 'OK':
            self._set_band_and_filter_pos()


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
        if band_switcher.thread_isAlive() or filter_switcher.thread_isAlive(): 
            #reschedule loop
            self.win.after(LOOP_DELAY,self._wait_on_band_and_filter_change_loop)
        else:
            self.update_fields()
            self.not_busy()
            self.app.print_comment("finished")
            self.wait_msg_window.destroy()
            self.filter_select_dialog.deactivate()
            
    def band_adjust(self, step_direction):
        raise NotImplementedError
        self._wait_on_band_adjust()
        
    def _wait_on_band_adjust(self):
        if self._capture_mode == "on_adjust":
                self.capture_once()
                
        
    def focus_adjust(self, step_direction):
        #get the stepsize from the field
        step_size = self.focus_adjust_stepsize_field.getvalue()
        step_size = int(step_size)
        if step_direction == "+1":
            step = step_size
        elif step_direction == "-1": 
            step = -step_size
        self.app.print_comment("adjust the focus by step: %s" % step)
        self.focus_adjust_position_field.configure(entry_fg = "gray")
        self.busy()
        self.app.adjust_focus(step, blocking = False) #don't block
        self._wait_focus_adjust_loop()
        
    def _wait_focus_adjust_loop(self):
        #check the controller states
        focus_adjuster  = self.app.load_controller('focus_adjuster')
        if focus_adjuster.thread_isAlive():
            #FIXME is this the way the update should be done?
            while not focus_adjuster.event_queue.empty():
                event, info = focus_adjuster.event_queue.get()
                if event == 'FOCUS_ADJUSTER_STEP_POLL':
                    pos = info['position']
                    self.focus_adjust_position_field.setvalue(pos) 
            #reschedule loop
            self.win.after(LOOP_DELAY,self._wait_focus_adjust_loop)
        else:
            self.update_fields()
            self.focus_adjust_position_field.configure(entry_fg = "black")
            self.not_busy()
            self.app.print_comment("finished")
            if self._capture_mode == "on_adjust":
                self.capture_once()
        
        

    def set_flatfield(self, state):
        if state == True:
            inactive_color = self.flatfield_posIN_button.cget('bg')
            self.flatfield_posIN_button.config(state='disabled', bg='green')
            self.flatfield_posOUT_button.config(state='normal', bg= inactive_color)
        elif state == False:
            inactive_color = self.flatfield_posOUT_button.cget('bg')
            self.flatfield_posOUT_button.config(state='disabled', bg='green')
            self.flatfield_posIN_button.config(state='normal', bg= inactive_color)
        #self.app.set_flatfield(state) #TODO

    def export_spectrum(self):
        self.app.print_comment("Exporting data...")
        dt_now = datetime.datetime.utcnow()
        dt_now_str = dt_now.strftime("%Y-%m-%d-%H_%m_%S")
        exptime = int(self.settings_dialog.form['exposure_time'])
        default_filename = "%s_raw_spectrum_exptime=%dms.csv" % (dt_now_str,exptime) 
        fdlg = SaveFileDialog(self.win,title="Save Raw Spectrum Data")
        userdata_path = self.app.config['paths']['data_dir']    

        filename = fdlg.go(dir_or_file = userdata_path, 
                           pattern="*.csv", 
                           default=default_filename, 
                           key = None
                          )
        if filename:
            self.app.export_spectrum(filename)
            

    def save_image(self):
        self.app.print_comment("saving image...")
        dt_now = datetime.datetime.utcnow()
        dt_now_str = dt_now.strftime("%Y-%m-%d-%H_%m_%S")
        exptime = int(self.settings_dialog.form['exposure_time'])
        default_filename = "%s_raw_image_exptime=%dms.png" % (dt_now_str,exptime) 
        fdlg = SaveFileDialog(self.win,title="Save Raw Spectrum Data")
        ws = self.win.winfo_screenwidth()
        hs = self.win.winfo_screenheight()
        w = ws/2
        h = hs/4
        # calculate position x, y
        x = (ws/2) - (w/2)
        y = (hs/2) - (h/2)
        fdlg.geometry("%dx%d+%d+%d" % (w,h,x,y))
        
        userdata_path = self.app.config['paths']['data_dir']    
        filename = fdlg.go(dir_or_file = userdata_path, 
                           pattern="*.png", 
                           default=default_filename, 
                           key = None
                          )
        if filename:
            I = self.last_image_data
            img = scipy.misc.toimage(I,mode='I') #convert  to 16-bit greyscale
            img.save(filename)
            
    
    def _update_spectral_plot(self, S):
        figure        = self.spectral_figure_widget.get_figure()        
        plot_template = self.spectral_plot_template
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
        self.photo_label_widget.config(image = photo)     #update the widget
 
#    def wait_on_experiment(self):
#        if self.app.check_experiment_completed():
#            self.app.shutdown_experiment() 
#            self.win.after(WAIT_DELAY,self.wait_on_experiment_shutdown)           
#        else:
#            self.win.after(WAIT_DELAY,self.wait_on_experiment)


    def print_to_text_display(self, text, eol='\n'):
        self.text_display.print_text(text, eol=eol)   
     

    def _load_settings(self):
        if os.path.exists(SETTINGS_FILEPATH):
            self.app.print_comment("loading from settings file '%s'" % SETTINGS_FILEPATH)
            settings = shelve.open(SETTINGS_FILEPATH)
            self.settings_dialog.form['exposure_time'] = settings.get('exposure_time',DEFAULT_EXPOSURE_TIME)
            self.settings_dialog.form['capture_interval']  = settings.get('capture_interval', DEFAULT_CAPTURE_INTERVAL)
            settings.close() 
        else:
            self.app.print_comment("failed to find settings file '%s'" % SETTINGS_FILEPATH)
                  
    def _cache_settings(self):
        self.app.print_comment("caching to settings file '%s'" % SETTINGS_FILEPATH)
        settings = shelve.open(SETTINGS_FILEPATH)
        settings['exposure_time'] = self.settings_dialog.form['exposure_time']
        settings['capture_interval']  = self.settings_dialog.form['capture_interval']
        settings.close()
        
            
    def _close(self):
        #cache the GUI settings FIXME - is this necessary?
        self._cache_settings()
        self.win.destroy()
