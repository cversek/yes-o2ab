###############################################################################
#Standard Python provided
import os, time, datetime, signal, socket, shelve, re
import Tkinter as tk
import ttk
#Standard or substitute
OrderedDict = None
try:
    from collections import OrderedDict
except ImportError:
    from yes_o2ab.support.odict import OrderedDict
#3rd party packages
from PIL import Image, ImageTk, ImageOps
import Pmw
from numpy import array, arange, savetxt
import numpy as np
from FileDialog import SaveFileDialog, LoadFileDialog
import scipy.misc
#Automat framework provided
from automat.core.gui.text_widgets           import TextDisplayBox
from automat.core.gui.pmw_custom.entry_form  import EntryForm
from automat.core.gui.pmw_custom.validation  import Validator
from automat.core.plotting.tk_embedded_plots import EmbeddedFigure
#yes_o2ab framework provided
from yes_o2ab.core.plotting.spectra          import RawSpectrumPlot, ProcessedSpectrumPlot
from yes_o2ab.core.plotting.temperature      import TemperaturePlot
#application local
from condition_fields        import ConditionFields
from capture_settings_dialog import CaptureSettingsDialog
from filter_select_dialog    import FilterSelectDialog
from tracking_dialog         import TrackingGotoSunDialog, TrackingGotoCoordsDialog
###############################################################################
# Module Constants
from ..common_defs import FRAMETYPE_DEFAULT, EXPOSURE_TIME_DEFAULT,\
    RBI_NUM_FLUSHES_DEFAULT, RBI_EXPOSURE_TIME_DEFAULT, REPEAT_DELAY_DEFAULT,\
    FIELD_LABEL_FONT, HEADING_LABEL_FONT, SUBHEADING_LABEL_FONT

WINDOW_TITLE      = "YES O2AB Control"
WAIT_DELAY        = 100 #milliseconds
TEXT_BUFFER_SIZE  = 10*2**20 #ten megabytes
SPECTRAL_FIGSIZE  = (6,5) #inches
SPECTRUM_PLOT_STYLE = 'r-'
SPECTRUM_BACKGROUND_PLOT_STYLE = 'b-'
MAX_IMAGESIZE     = (600,500)
TEMPERATURE_FIGSIZE  = (6,5) #inches
LOOP_DELAY        = 100 #milliseconds
CONDITIONS_BACKUP_FILENAME = os.path.expanduser("~/.yes_o2ab_control_conditions.csv")

FINE_ADJUST_STEP_SIZE_DEFAULT = 10 #steps

MONITOR_INTERVAL_DEFAULT = 120  #seconds
MONITOR_INTERVAL_MIN     = 10   #seconds
MONITOR_INTERVAL_MAX     = 9999 #seconds

BUTTON_WIDTH = 20
SECTION_PADY = 2
CONFIRMATION_TEXT_DISPLAY_TEXT_HEIGHT = 40
CONFIRMATION_TEXT_DISPLAY_TEXT_WIDTH  = 80

SETTINGS_FILEPATH = os.path.expanduser("~/.yes_o2ab_control_settings.db")

#_empty_regex = re.compile('^$')
#_positive_integer_regex = re.compile('^0|([1-9]\d*)$')
#def positive_integer_validator(text):
#    if _positive_integer_regex.match(text):
#        return Pmw.OK
#    elif _empty_regex.match(text):
#        return Pmw.PARTIAL
#    else:
#        return Pmw.ERROR
    
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
        #self.win.bind('<Control-f>', lambda e: self.app.force_experiment()
        #-----------------------------------------------------------------------
        #build the left panel
        left_panel = tk.Frame(win)
        #capture controls
        self._capture_mode     = None
        self._capture_after_id = None
        tk.Label(left_panel, text="Capture Controls:", font = HEADING_LABEL_FONT).pack(side='top',anchor="w")
        self.change_capture_settings_button = tk.Button(left_panel,
                                                        text    = 'Change Settings',
                                                        command = self.change_capture_settings, 
                                                        width   = BUTTON_WIDTH)
        self.change_capture_settings_button.pack(side='top', anchor="sw")
        self.capture_once_button = tk.Button(left_panel,text='Run Once',command = self.capture_once, width = BUTTON_WIDTH)
        self.capture_once_button.pack(side='top', anchor="nw")
        self.capture_on_adjust_button = tk.Button(left_panel,text='Run on Adjust',command = self.capture_on_adjust, width = BUTTON_WIDTH)
        self.capture_on_adjust_button.pack(side='top', anchor="nw")
        self.capture_continually_button  = tk.Button(left_panel,text='Run Continually',command = self.capture_continually, width = BUTTON_WIDTH)
        self.capture_continually_button.pack(side='top', anchor="nw")
        self.capture_stop_button = tk.Button(left_panel,text='Stop',command = self.capture_stop, state='disabled', width = BUTTON_WIDTH)
        self.capture_stop_button.pack(side='top', anchor="nw")
        self.capture_time_left_field = Pmw.EntryField(left_panel,
                                                      labelpos    = 'w',
                                                      label_text  = "time left (s):",
                                                      label_font  = FIELD_LABEL_FONT,
                                                      entry_width = 8,
                                                      entry_state = 'readonly',
                                                      )
        self.capture_time_left_field.pack(side='top',anchor='w',expand='no')
        #build the capture settings dialog
        self.capture_settings_dialog = CaptureSettingsDialog(self.win)
        self.capture_settings_dialog.withdraw()
        
        #optics controls
        tk.Label(left_panel, pady = SECTION_PADY).pack(side='top',fill='x', anchor="nw")
        tk.Label(left_panel, text="Optics Controls:", font = HEADING_LABEL_FONT).pack(side='top',anchor="w")
        OPTICS_FIELDS_ENTRY_WIDTH = 9
        self.optics_fields = OrderedDict()
        self.optics_fields['flatfield'] = Pmw.EntryField(left_panel,
                                                         labelpos    = 'w',
                                                         label_text  = "        flatfield:",
                                                         label_font  = FIELD_LABEL_FONT,
                                                         entry_width = OPTICS_FIELDS_ENTRY_WIDTH,
                                                         entry_state = 'readonly',
                                                         )
        self.optics_fields['band']      = Pmw.EntryField(left_panel,
                                                         labelpos    = 'w',
                                                         label_text  = "             band:",
                                                         label_font  = FIELD_LABEL_FONT,
                                                         entry_width = OPTICS_FIELDS_ENTRY_WIDTH,
                                                         entry_state = 'readonly',
                                                        )
        self.optics_fields['filter_B']  = Pmw.EntryField(left_panel,
                                                         labelpos    = 'w',
                                                         label_text  = "(B)and-pass filt.:",
                                                         label_font  = FIELD_LABEL_FONT,
                                                         entry_width = OPTICS_FIELDS_ENTRY_WIDTH,
                                                         entry_state = 'readonly',
                                                        )
        self.optics_fields['filter_A']  = Pmw.EntryField(left_panel,
                                                         labelpos    = 'w',
                                                         label_text  = "(A)uxiliary filt.:",
                                                         label_font  = FIELD_LABEL_FONT,
                                                         entry_width = OPTICS_FIELDS_ENTRY_WIDTH,
                                                         entry_state = 'readonly',
                                                        )
        self.optics_fields['filter_pos'] = Pmw.EntryField(left_panel,
                                                         labelpos    = 'w',
                                                         label_text  = "filt. pos. (5B+A):",
                                                         label_font  = FIELD_LABEL_FONT,
                                                         entry_width = OPTICS_FIELDS_ENTRY_WIDTH,
                                                         entry_state = 'readonly',
                                                        )
        for key, widget in self.optics_fields.items():
            widget.pack(side='top', anchor="w", expand='no')
        
        self.filter_select_button = tk.Button(left_panel,text='Band/Filter Select',command = self.filter_select, width = BUTTON_WIDTH)
        self.filter_select_button.pack(side='top', anchor="nw")
        #build the filter selection dialog
        self.filter_select_dialog = FilterSelectDialog(
                                                       parent = self.win, 
                                                       choicesB = self.app.filter_B_types,
                                                       choicesA = self.app.filter_A_types,
                                                       )
        self.filter_select_dialog.withdraw()
        
        #band fine adjustment controls
        band_adjust_frame = tk.Frame(left_panel)
        tk.Label(band_adjust_frame, text="Band Fine Adjust:", font = SUBHEADING_LABEL_FONT).pack(side='top', anchor="nw")        
        self.band_adjustL_button = tk.Button(band_adjust_frame,text='<--',command = lambda: self.band_adjust('-1'))
        self.band_adjustL_button.pack(side='left', anchor="nw")
        self.band_adjustR_button = tk.Button(band_adjust_frame,text='-->',command = lambda: self.band_adjust('+1'))
        self.band_adjustR_button.pack(side='left', anchor="nw")
        
        self.band_adjust_stepsize_field = Pmw.EntryField(band_adjust_frame,
                                                         labelpos='e',
                                                         label_text="step size",
                                                         label_font = FIELD_LABEL_FONT,
                                                         value = FINE_ADJUST_STEP_SIZE_DEFAULT,
                                                         entry_width=9,
                                                         validate = Validator(_min=0,_max=1000,converter=int),
                                                         )
        self.band_adjust_stepsize_field.pack(side='top', anchor="w", expand='no')
        self.band_adjust_position_field = Pmw.EntryField(band_adjust_frame,
                                                         labelpos='e',
                                                         label_text="position",
                                                         label_font = FIELD_LABEL_FONT,
                                                         entry_width=9,
                                                         entry_state='readonly',
                                                         )
        self.band_adjust_position_field.pack(side='top', anchor="w", expand='no')
        band_adjust_frame.pack(side='top', anchor="nw")
        
        #focus adjustment controls
        focus_adjust_button_frame = tk.Frame(left_panel)
        tk.Label(focus_adjust_button_frame, text="Focus Adjust:", font = SUBHEADING_LABEL_FONT).pack(side='top', anchor="nw")   
        self.focus_adjust_goto_center_button = tk.Button(focus_adjust_button_frame,text='Goto Center',command = self.center_focus, width = BUTTON_WIDTH)
        self.focus_adjust_goto_center_button.pack(side='top',anchor='nw')     
        self.focus_adjustL_button = tk.Button(focus_adjust_button_frame,text='<--',command = lambda: self.focus_adjust('-1'))
        self.focus_adjustL_button.pack(side='left', anchor="nw")
        self.focus_adjustR_button = tk.Button(focus_adjust_button_frame,text='-->',command = lambda: self.focus_adjust('+1'))
        self.focus_adjustR_button.pack(side='left', anchor="nw")
        
        focus_adjust_button_frame.pack(side='top',fill='x', anchor="nw")
        self.focus_adjust_stepsize_field = Pmw.EntryField(focus_adjust_button_frame,
                                                          labelpos    = 'e',
                                                          label_text  ="step size",
                                                          label_font  = FIELD_LABEL_FONT,
                                                          value       = FINE_ADJUST_STEP_SIZE_DEFAULT,
                                                          entry_width = 9,
                                                          validate    = Validator(_min=0,_max=1000,converter=int),
                                                          )
        self.focus_adjust_stepsize_field.pack(side='top', anchor="w", expand='no')
        self.focus_adjust_position_field = Pmw.EntryField(focus_adjust_button_frame,
                                                          labelpos    = 'e',
                                                          label_text  = "position",
                                                          label_font  = FIELD_LABEL_FONT,
                                                          entry_width = 9,
                                                          entry_state = 'readonly',
                                                          )
        self.focus_adjust_position_field.pack(side='top', anchor="w", expand='no')
        #-----------------------------------------------------------------------
        #tracking controls
        self._tracking_initialized = False
        self._tracking_mode = None
        tk.Label(left_panel, pady = SECTION_PADY).pack(side='top',fill='x', anchor="nw")
        tk.Label(left_panel, text="Tracking Controls:", font = HEADING_LABEL_FONT).pack(side='top',anchor="w")
        TRACKING_FIELDS_ENTRY_WIDTH = 9
        self.tracking_fields = OrderedDict()
        self.tracking_fields['azimuth']   = Pmw.EntryField(left_panel,
                                                         labelpos    = 'w',
                                                         label_text  = "  azimuth:",
                                                         label_font  = FIELD_LABEL_FONT,
                                                         entry_width = TRACKING_FIELDS_ENTRY_WIDTH,
                                                         entry_state = 'readonly',
                                                         )
        self.tracking_fields['elevation'] = Pmw.EntryField(left_panel,
                                                         labelpos    = 'w',
                                                         label_text  = "elevation:",
                                                         label_font  = FIELD_LABEL_FONT,
                                                         entry_width = TRACKING_FIELDS_ENTRY_WIDTH,
                                                         entry_state = 'readonly',
                                                         )

        for key, widget in self.tracking_fields.items():
            widget.pack(side='top', anchor="w", expand='no')
        
        self.tracking_seek_home_button = tk.Button(left_panel,
                                                   text='Seek Home',
                                                   command = lambda: self.tracking_goto('home'), 
                                                   width = BUTTON_WIDTH,
                                                   )
        self.tracking_seek_home_button.pack(side='top', anchor="nw")
        self.tracking_goto_store_button = tk.Button(left_panel,
                                                    text='Go to Store Pos.',
                                                    command = lambda: self.tracking_goto('store'), 
                                                    width = BUTTON_WIDTH,
                                                    state='disabled',
                                                    )
        self.tracking_goto_store_button.pack(side='top', anchor="nw")
        self.tracking_goto_zenith_button = tk.Button(left_panel,
                                                     text='Go to Zenith',
                                                     command = lambda: self.tracking_goto('zenith'),
                                                     width = BUTTON_WIDTH,
                                                     state='disabled',
                                                     )
        self.tracking_goto_zenith_button.pack(side='top', anchor="nw")
        self.tracking_goto_sun_button = tk.Button(left_panel,
                                                  text='Go to Sun',
                                                  command = lambda: self.tracking_goto('sun'), 
                                                  width = BUTTON_WIDTH,
                                                  state='disabled',
                                                  )
        self.tracking_goto_sun_button.pack(side='top', anchor="nw")
        self.tracking_goto_coords_button = tk.Button(left_panel,
                                                     text='Go to Coords',
                                                     command = lambda: self.tracking_goto('coords'),
                                                     width = BUTTON_WIDTH,
                                                     state='disabled',
                                                     )
        self.tracking_goto_coords_button.pack(side='top', anchor="nw")
        #build the tracking dialogs
        self.tracking_goto_sun_dialog = TrackingGotoSunDialog(self.win)
        self.tracking_goto_sun_dialog.withdraw()
        self.tracking_goto_coords_dialog = TrackingGotoCoordsDialog(self.win)
        self.tracking_goto_coords_dialog.withdraw()
        #finish the left panel
        left_panel.pack(fill='y',expand='no',side='left', padx = 10)
        #-----------------------------------------------------------------------
        #build the middle panel - a tabbed notebook
        mid_panel = tk.Frame(win)
        nb        = ttk.Notebook(mid_panel)
        nb.pack(fill='both', expand='yes',side='right')
        tab1 = tk.Frame(nb)
        tab2 = tk.Frame(nb)
        tab3 = tk.Frame(nb)
        tab4 = tk.Frame(nb)
        nb.add(tab1, text="Raw Spectrum")
        nb.add(tab2, text="Proc. Spectrum")
        nb.add(tab3, text="Raw Image")
        nb.add(tab4, text="Conditions")
        #create an tk embedded figure for spectral display
        self.raw_spectrum_plot_template = RawSpectrumPlot()
        self.raw_spectrum_figure_widget = EmbeddedFigure(tab1, figsize=SPECTRAL_FIGSIZE)
        self.raw_spectrum_figure_widget.pack(side='top',fill='both', expand='yes')
        self.replot_raw_spectrum_button = tk.Button(tab1,text='Replot Spectrum',command = self.replot_raw_spectrum, state='disabled', width = BUTTON_WIDTH)
        self.replot_raw_spectrum_button.pack(side='left',anchor="sw")
        self.export_raw_spectrum_button = tk.Button(tab1,text='Export Spectrum',command = self.export_raw_spectrum, state='disabled', width = BUTTON_WIDTH)
        self.export_raw_spectrum_button.pack(side='left',anchor="sw")
        self.import_background_spectrum_button = tk.Button(tab1,text='Import Background',command = self.import_background_spectrum, width = BUTTON_WIDTH)
        self.import_background_spectrum_button.pack(side='left',anchor="sw")
        #create an tk embedded figure for spectral display
        self.processed_spectrum_plot_template = ProcessedSpectrumPlot()
        self.processed_spectrum_figure_widget = EmbeddedFigure(tab2, figsize=SPECTRAL_FIGSIZE)
        self.processed_spectrum_figure_widget.pack(side='top',fill='both', expand='yes')
        self.replot_processed_spectrum_button = tk.Button(tab2,text='Replot Spectrum',command = self.replot_processed_spectrum, state='disabled', width = BUTTON_WIDTH)
        self.replot_processed_spectrum_button.pack(side='left',anchor="sw")
        self.export_processed_spectrum_button = tk.Button(tab2,text='Export Spectrum',command = self.export_processed_spectrum, state='disabled', width = BUTTON_WIDTH)
        self.export_processed_spectrum_button.pack(side='left',anchor="sw")
        #create a tk Label widget for image display
        self.photo_label_widget = tk.Label(tab3)
        self.photo_label_widget.pack(side='top',fill='both', expand='yes')
        self.save_image_button = tk.Button(tab3,text='Save Image',command = self.save_image, state='disabled', width = BUTTON_WIDTH)
        self.save_image_button.pack(side='bottom',anchor="sw")
        #create an tk embedded figure for temperature display
        self.temperature_plot_template = TemperaturePlot()
        self.temperature_figure_widget = EmbeddedFigure(tab4, figsize=TEMPERATURE_FIGSIZE)
        self.temperature_figure_widget.pack(side='top',fill='both', expand='yes')
        self.export_conditions_button = tk.Button(tab4,text='Export Conditions',command = self.export_conditions, state='disabled', width = BUTTON_WIDTH)
        self.export_conditions_button.pack(side='left',anchor="sw")
        self.clear_conditions_data_button = tk.Button(tab4,text='Clear Data',command = self.clear_conditions_data, width = BUTTON_WIDTH)
        self.clear_conditions_data_button.pack(side='left',anchor="sw")
        mid_panel.pack(fill='both', expand='yes',side='left')
        #-----------------------------------------------------------------------
        #build the right panel
        right_panel = tk.Frame(win)
        
        #Condition Monitoring
        self._condition_monitor_mode = False
        self._condition_monitor_after_id = None
        tk.Label(right_panel, pady = SECTION_PADY).pack(side='top',fill='x', anchor="nw")
        tk.Label(right_panel, text="Condition Monitoring:", font = HEADING_LABEL_FONT).pack(side='top',anchor="w")
        self.condition_monitor_button = tk.Button(right_panel,text='Monitor',command = self.condition_monitor_mode_toggle, width = BUTTON_WIDTH)
        self.condition_monitor_button.pack(side='top', anchor="nw")
        self.monitor_interval_field = Pmw.EntryField(right_panel,
                                                     labelpos    = 'e',
                                                     label_text  ="interval [s] (min=10,max=9999)",
                                                     label_font  = FIELD_LABEL_FONT,
                                                     value       = MONITOR_INTERVAL_DEFAULT,
                                                     entry_width = 4,
                                                     validate    = Validator(_min=MONITOR_INTERVAL_MIN,
                                                                             _max=MONITOR_INTERVAL_MAX,
                                                                              converter=int),
                                                     )
        self.monitor_interval_field.pack(side='top', anchor="w", expand='no')
        tk.Label(right_panel, pady = SECTION_PADY//2).pack(side='top',fill='x', anchor="nw")
        self.condition_fields = ConditionFields(right_panel)
        self.condition_fields.pack(side='top', anchor="w", expand='no')
        
        #Data Processing
        tk.Label(right_panel, pady = SECTION_PADY).pack(side='top',fill='x', anchor="nw")
        tk.Label(right_panel, text="Data Processing:", font = HEADING_LABEL_FONT).pack(side='top',anchor="w")
        self.background_filename_field = Pmw.EntryField(right_panel,
                                                        labelpos='w',
                                                        label_text="Background Filename:",
                                                        label_font = FIELD_LABEL_FONT,
                                                        #entry_width=20,
                                                        entry_state = 'readonly',
                                                        )
        self.background_filename_field.pack(side='top', fill='x',anchor="nw", expand='no')
        
        # Events text display
        tk.Label(right_panel, pady = SECTION_PADY).pack(side='top',fill='x', anchor="nw")
        tk.Label(right_panel, text="Events Monitoring:", font = HEADING_LABEL_FONT).pack(side='top',anchor="w")
        self.text_display  = TextDisplayBox(right_panel,text_height=15, buffer_size = TEXT_BUFFER_SIZE)
        self.text_display.pack(side='left',fill='both',expand='yes')
        #finish building the right panel
        right_panel.pack(fill='both', expand='yes',side='right', padx = 10)
        #-----------------------------------------------------------------------
        self._load_settings()
        
    def launch(self):
        #run the GUI handling loop
        IgnoreKeyboardInterrupt()
        self.flush_event_queues()
        #get metadata from devices to update the fields
        self.condition_monitor_button.invoke()
        md = self.app.query_metadata()
        self._update_optics_fields(md)
        self._update_tracking_fields(md)
        self.flush_event_queues()
        #reveal the main window
        self.win.deiconify()
        self.win.mainloop()
        NoticeKeyboardInterrupt()
        
    def flush_event_queues(self):
        for handle in self.app.USED_CONTROLLERS:
            controller = self.app.load_controller(handle)
            #read out all pending events
            while not controller.event_queue.empty():
                event, info = controller.event_queue.get()
                self.print_event(event,info)
    
    def busy(self):
        self.disable_control_buttons()
        self.win.config(cursor="watch")
        
    def not_busy(self):
        self.enable_control_buttons()
        self.win.config(cursor="")
        
    def busy_dialog(self, msg):
        self.busy()
        self.wait_msg_window = tk.Toplevel(self.win)
        tk.Label(self.wait_msg_window,text=msg, font=HEADING_LABEL_FONT).pack(fill="both",expand="yes", padx=1,pady=1)
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
    
    def end_busy_dialog(self):
        self.not_busy()
        self.app.print_comment("busy dialog finished")
        try:
            self.wait_msg_window.destroy()
        except AttributeError: #ignore case when the window doesn't exist
            return
        
    def disable_control_buttons(self):
        self.change_capture_settings_button.configure(state="disabled")
        self.capture_continually_button.configure(state="disabled")
        #self.capture_stop_button.configure(state="disabled")
        self.capture_once_button.configure(state="disabled")
        self.capture_on_adjust_button.configure(state="disabled")
        self.filter_select_button.configure(state="disabled")
        self.band_adjustL_button.configure(state="disabled")
        self.band_adjustR_button.configure(state="disabled")
        self.focus_adjust_goto_center_button.configure(state="disabled")
        self.focus_adjustL_button.configure(state="disabled")
        self.focus_adjustR_button.configure(state="disabled")
        self.tracking_seek_home_button.config(state='disabled')
        self.tracking_goto_store_button.config(state='disabled')
        self.tracking_goto_zenith_button.config(state='disabled')
        self.tracking_goto_sun_button.config(state='disabled')
        self.tracking_goto_coords_button.config(state='disabled')
        
    def enable_control_buttons(self):
        self.change_capture_settings_button.configure(state="normal")
        if not self._capture_mode == "on_adjust":
            self.capture_continually_button.configure(state="normal")
        #self.capture_stop_button.configure(state="normal")
        self.capture_once_button.configure(state="normal")
        self.capture_on_adjust_button.configure(state="normal")
        self.filter_select_button.configure(state="normal")
        self.band_adjustL_button.configure(state="normal")
        self.band_adjustR_button.configure(state="normal")
        self.focus_adjust_goto_center_button.configure(state="normal")
        self.focus_adjustL_button.configure(state="normal")
        self.focus_adjustR_button.configure(state="normal")
        self.tracking_seek_home_button.config(state='normal')
        if self._tracking_initialized:
            self.tracking_goto_store_button.config(state='normal')
            self.tracking_goto_zenith_button.config(state='normal')
            self.tracking_goto_sun_button.config(state='normal')
            self.tracking_goto_coords_button.config(state='normal')

    def change_capture_settings(self):
        choice = self.capture_settings_dialog.activate()
        if choice == "OK":
            self.app.print_comment("changing capture settings...")
            image_capture = self.app.load_controller('image_capture')
            temp = float(self.capture_settings_dialog.form['CCD_temp_setpoint'])
            image_capture.set_CCD_temperature_setpoint(temp)
            #read out all pending events
            while not image_capture.event_queue.empty():
                event, info = image_capture.event_queue.get()
                self.print_event(event,info)

    def capture_once(self, delay = 0.0):
        #disable all the buttons, except the stop button
        self.capture_once_button.config(bg='green', relief='sunken')
        self.disable_control_buttons()
        self.capture_stop_button.config(state='normal')
        #get parameters
        frametype         = self.capture_settings_dialog.frametype_var.get()
        exposure_time     = int(self.capture_settings_dialog.form['exposure_time'])
        rbi_num_flushes   = int(self.capture_settings_dialog.form['rbi_num_flushes'])
        rbi_exposure_time = int(self.capture_settings_dialog.form['rbi_exposure_time'])
        repeat_delay      = int(self.capture_settings_dialog.form['repeat_delay'])
        temp = float(self.capture_settings_dialog.form['CCD_temp_setpoint'])
        self.app.print_comment("Capturing image:")
        #acquire image and process into rudimentary spectrum
        self.app.print_comment("\texposing for %d milliseconds..." % (exposure_time,))
        self.app.acquire_image(frametype         = frametype,
                               exposure_time     = exposure_time,
                               rbi_num_flushes   = rbi_num_flushes,
                               rbi_exposure_time = rbi_exposure_time,
                               delay = delay,
                               CCD_temp_setpoint = temp,
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
            elif event == "IMAGE_CAPTURE_LOOP_SLEEPING":
                time_left = info['time_left']
                self.capture_time_left_field.setvalue("%d" % round(time_left))
        if image_capture.thread_isAlive(): 
            #reschedule loop
            self.win.after(LOOP_DELAY,self._wait_on_capture_loop)
        else:
            #finish up
            #md = self.app.last_capture_metadata.copy()
            md = self.app.query_metadata()
            self._update_optics_fields(md)
            self.capture_time_left_field.setvalue("")
            #self.not_busy()
            #re-enable all the buttons, except the stop button
            self.enable_control_buttons()
            self.capture_once_button.config(bg='light gray', relief='raised')
            self.capture_stop_button.config(state='disabled')
            self.app.print_comment("capture completed")
            self.app.compute_raw_spectrum()
            S = self.app.get_raw_spectrum()
            I = self.app.get_last_image()
            B = self.app.get_background_spectrum()
            self._update_raw_spectrum_plot(S=S,B=B)
            self._update_processed_spectrum_plot(S=S,B=B)
            self._update_image(I)
            self.replot_raw_spectrum_button.config(state='normal') #data can now be replotted
            self.export_raw_spectrum_button.config(state='normal') #data can now be exported
            self.save_image_button.config(state='normal')      #data can now be exported
    
    def capture_on_adjust(self):
        if self._capture_mode == "on_adjust": #toggle it off
            self.capture_on_adjust_button.config(bg='light gray', relief="raised")
            #re-enable all the buttons, except the stop button
            self.capture_once_button.config(state='normal')
            self.capture_on_adjust_button.config(state='normal')
            self.capture_continually_button.config(state='normal')
            self.capture_stop_button.config(state='disabled')
            self._capture_mode = None
        else: #toggle it on
            self.capture_on_adjust_button.config(bg='green', relief="sunken")
            #disable some of the capture mode buttons
            #self.capture_once_button.config(state='disabled')
            self.capture_continually_button.config(state='disabled', bg='light gray', relief="raised")
            self.capture_stop_button.config(state='disabled')
            self._capture_mode = "on_adjust"
     
    def capture_continually(self):
        #disable all the buttons, except the stop button
        self.capture_once_button.config(state='disabled')
        self.change_capture_settings_button.config(state='disabled')
        self.capture_on_adjust_button.config(state='disabled')
        self.capture_continually_button.config(state='disabled', bg='green', relief="sunken")
        self.capture_stop_button.config(state='normal')
        self.tracking_seek_home_button.config(state='disabled')
        self.tracking_goto_zenith_button.config(state='disabled')
        self.tracking_goto_sun_button.config(state='disabled')
        self.tracking_goto_coords_button.config(state='disabled')
        self._capture_mode = "continual"
        #get parameters
        frametype         = self.capture_settings_dialog.frametype_var.get()
        exposure_time     = float(self.capture_settings_dialog.form['exposure_time'])
        rbi_num_flushes   =   int(self.capture_settings_dialog.form['rbi_num_flushes'])
        rbi_exposure_time = float(self.capture_settings_dialog.form['rbi_exposure_time'])
        delay             = float(self.capture_settings_dialog.form['repeat_delay'])
        #set up the image capture controller in loop mode
        image_capture = self.app.load_controller('image_capture')
        image_capture.set_configuration(frametype         = frametype,
                                        num_captures      = None, #will cause infinite loop
                                        exposure_time     = exposure_time,
                                        rbi_num_flushes   = rbi_num_flushes,
                                        rbi_exposure_time = rbi_exposure_time,
                                        delay             = delay,
                                       )
        #refresh the metdata
        self.app.query_metadata()
        self.app.print_comment("Starting image capture loop with repeat delay %d seconds." % (delay,))
        image_capture.start() #should not block
        #schedule loop
        self._capture_continually_loop()
        

    def _capture_continually_loop(self):
        image_capture = self.app.load_controller('image_capture')
        #read out all pending events
        while not image_capture.event_queue.empty():
            event, info = image_capture.event_queue.get()
            self.print_event(event,info)
            if   event == "FILTER_SWITCHER_STARTED":
                #filter is changing like in the 'opaque' frametype
                self._update_filter_status(None)
            elif event == "FILTER_SWITCHER_COMPLETED":
               md = self.app.query_filter_status()
               self._update_filter_status(md)
            elif event == "IMAGE_CAPTURE_LOOP_SLEEPING":
                time_left = info['time_left']
                self.capture_time_left_field.setvalue("%d" % round(time_left))
            elif event == "IMAGE_CAPTURE_EXPOSURE_COMPLETED":
                #grab the image, comput the spectrum, then update them
                I = info['image_array']
                S = self.app.compute_raw_spectrum(I)
                B = self.app.get_background_spectrum()
                self._update_raw_spectrum_plot(S=S,B=B)
                self._update_processed_spectrum_plot(S=S,B=B)
                self._update_image(I)
                self.replot_raw_spectrum_button.config(state='normal') #data can now be replotted
                self.save_image_button.config(state='normal')      #data can now be exported
        #reschedule loop
        if image_capture.thread_isAlive():  #wait for the capture to finish, important!
            self._capture_after_id = self.win.after(LOOP_DELAY,self._capture_continually_loop)
        else:
            #finish up
            md = self.app.query_metadata()
            self.app.last_capture_metadata = md
            self.capture_time_left_field.setvalue("")
            self._update_optics_fields(md)
            #enable all the buttons, except the stop button
            self.capture_once_button.config(state='normal')
            self.change_capture_settings_button.config(state='normal')
            self.capture_on_adjust_button.config(state='normal')
            self.capture_continually_button.config(state='normal', bg='light gray', relief = 'raised')
            self.tracking_seek_home_button.config(state='normal')
            self.tracking_goto_zenith_button.config(state='normal')
            self.tracking_goto_sun_button.config(state='normal')
            self.tracking_goto_coords_button.config(state='normal')
            #data can now be exported
            self.export_raw_spectrum_button.config(state='normal')
            #do not reschedule loop

    def capture_stop(self):
        self.capture_stop_button.config(state='disabled')
        image_capture = self.app.load_controller('image_capture')
        #force it to stop right now instead of finishing sleep
        image_capture.abort()
        if not self._capture_after_id is None:
            #cancel the next scheduled loop time
            self.win.after_cancel(self._capture_after_id)
            #then enter the loop one more time to clean up
            self._capture_continually_loop()
        self._capture_mode = None
    
    def filter_select(self):
        self.app.print_comment("Selecting filter:")
        #self._update_optics_fields() #FIXME does this need to be done?
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
        msg = "Please wait while the band is switched to '%s'\n and the filter is switched to position %d..." % (new_band,pos)
        self.busy_dialog(msg)
        #get the current settings
        band_switcher = self.app.config.load_controller('band_switcher')
        curr_band = band_switcher.band
        #change band state if specified
        if (new_band != '(unknown)') and (curr_band != new_band):
            #change the band
            self.optics_fields['band'].setvalue("(changing)")
            self.app.print_comment("changing band from '%s' to '%s'... (thread)" % (curr_band,new_band))
            self.app.select_band(new_band, blocking = False) #threaded!
        else:
            self.app.print_comment("not changing band")
        #change the filter position
        self.optics_fields['filter_pos'].setvalue("(changing)")
        self.optics_fields['filter_B'].setvalue("(changing)")
        self.optics_fields['filter_A'].setvalue("(changing)")
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
            self._update_optics_fields(md)
            self.end_busy_dialog()
            self.filter_select_dialog.deactivate()
            
    def band_adjust(self, step_direction):
        curr_band = self.optics_fields['band'].getvalue()
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
            self._update_optics_fields(md)
            self.band_adjust_position_field.configure(entry_fg = "black")
            self.not_busy()
            self.app.print_comment("finished")
            if self._capture_mode == "on_adjust":
                #check to see if a capture is already running
                image_capture = self.app.load_controller('image_capture')
                if not image_capture.thread_isAlive():
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
    
    def center_focus(self):
        self.app.print_comment("Centering the focus.")
        self.app.center_focus(blocking = False)
        msg = "Please wait while the focuser is centered..."
        self.busy_dialog(msg)
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
            self._update_optics_fields(md)
            self.focus_adjust_position_field.configure(entry_fg = "black")
            self.end_busy_dialog()
            self.app.print_comment("finished")
            if self._capture_mode == "on_adjust":
                #check to see if a capture is already running
                image_capture = self.app.load_controller('image_capture')
                if not image_capture.thread_isAlive():
                    self.capture_once()
                
    def tracking_goto(self, mode):
        solar_tracker = self.app.load_controller('solar_tracker')
        #start the movement
        if mode == 'home':
            self._tracking_busy()
            if not solar_tracker.is_initialized:
                msg = "Warning: Check that the Weather Cover is open before proceeding.\nOtherwise, instrument may be damaged."
                dlg = Pmw.MessageDialog(parent = self.win,
                                        message_text = msg,
                                        buttons = ('Proceed', 'Cancel'),
                                        defaultbutton = 'Cancel',
                                        iconpos = 'n',
                                        icon_bitmap = 'warning',
                                        title = "Initialize Tracking Controls",
                                        )
                choice = dlg.activate()
                dlg.deactivate()
                if choice == 'Proceed':
                    self.app.print_comment("Initializing the tracking controls")
                    solar_tracker.initialize() #this blocks
                    self._tracking_initialized = True
                    self._wait_on_tracking_goto_loop(mode)
                    return
                elif choice == 'Cancel':
                    self.app.print_comment("Cancelling the track control initialization.")
                    self._wait_on_tracking_goto_loop(mode)
                    return
            else:
                solar_tracker.seek_home() #this blocks
                self._wait_on_tracking_goto_loop(mode)
                return
        elif mode == 'store':
            self._tracking_busy()
            #go to zenith first, so az swing isn't wide
            solar_tracker.goto_zenith(blocking = False)
            self._wait_on_tracking_goto_loop(mode='store_az')
            return
        elif mode == 'zenith':
            self._tracking_busy()
            solar_tracker.goto_zenith(blocking = False)
            self._wait_on_tracking_goto_loop(mode)
            return
        elif mode == 'sun':
            #pre select the delay and capture mode if in "run on adjust" mode
            if self._capture_mode == "on_adjust":
                self.tracking_goto_sun_dialog.delay_then_capture_button.select()
            self.tracking_goto_sun_dialog.withdraw()
            action = self.tracking_goto_sun_dialog.activate()
            self.tracking_goto_sun_dialog.deactivate()
            if action == 'OK':
                self._tracking_busy()
                self._tracking_start_time = time.time()
                try:
                    solar_tracker.goto_sun(blocking = False)
                except ValueError, exc:
                    msg = "The 'go to sun' tracking request could not be completed, because of the following error: %s" % exc
                    dlg = Pmw.MessageDialog(parent = self.win,
                                            message_text = msg,
                                            buttons = ('OK',),
                                            title = "Tracking Error",
                                            )
                    choice = dlg.activate()
                    dlg.deactivate()
                    mode = None #prevents post handling in waiting loop
                self._wait_on_tracking_goto_loop(mode)
                return
        elif mode == 'coords':
            dlg = TrackingGotoCoordsDialog(self.win)
            dlg.withdraw()
            tracking_mirror_positioner = self.app.load_controller('tracking_mirror_positioner')
            az_CW_limit  = float(tracking_mirror_positioner.configuration['az_CW_limit'])
            az_CCW_limit = float(tracking_mirror_positioner.configuration['az_CCW_limit'])
            el_CW_limit  = float(tracking_mirror_positioner.configuration['el_CW_limit'])
            el_CCW_limit = float(tracking_mirror_positioner.configuration['el_CCW_limit'])
            dlg.set_limits(az_CW_limit  = az_CW_limit,
                           az_CCW_limit = az_CCW_limit,
                           el_CW_limit  = el_CW_limit,
                           el_CCW_limit = el_CCW_limit,
                          )
            dlg.az_field.setvalue(tracking_mirror_positioner.az_pos)
            dlg.el_field.setvalue(tracking_mirror_positioner.el_pos)
            action = dlg.activate()
            dlg.deactivate()
            if action == 'OK':
                az_target = float(dlg.az_field.getvalue())
                el_target = float(dlg.el_field.getvalue())
                self._tracking_busy()
                solar_tracker.goto_coords(az_target = az_target,
                                          el_target = el_target,
                                          blocking = False)
                self._wait_on_tracking_goto_loop(mode)
                return
        
    def _tracking_busy(self):
        #throw up a busy message
        msg = "Please wait while tracking mirror is moved..."
        self.busy_dialog(msg)
        self.tracking_fields['azimuth'].configure(entry_fg = "dark gray")
        self.tracking_fields['elevation'].configure(entry_fg = "dark gray")
        
    def _wait_on_tracking_goto_loop(self, mode):
        #check the controller states
        solar_tracker = self.app.load_controller('solar_tracker')
        tracking_mirror_positioner  = self.app.load_controller('tracking_mirror_positioner')
        #read out all pending events
        while not tracking_mirror_positioner.event_queue.empty():
            event, info = tracking_mirror_positioner.event_queue.get()
            self.print_event(event,info)
            if event == 'TRACKING_MIRROR_POSITIONER_UPDATE':
                az_pos = info['az_pos']
                el_pos = info['el_pos']
                self.tracking_fields['azimuth'].setvalue(az_pos)
                self.tracking_fields['elevation'].setvalue(el_pos)
        #check thread state
        if tracking_mirror_positioner.thread_isAlive():
            #reschedule loop
            self.win.after(LOOP_DELAY,lambda: self._wait_on_tracking_goto_loop(mode))
        else: #position has been reached
            md = self.app.query_metadata()
            self._update_tracking_fields(md)
            self.tracking_fields['azimuth'].configure(entry_fg = "black")
            self.tracking_fields['elevation'].configure(entry_fg = "black")
            if mode == 'home':
                self.end_busy_dialog()
                return
            elif mode == 'store_az':
                az_store = float(tracking_mirror_positioner.configuration['az_store'])
                solar_tracker.goto_coords(az_target = az_store,
                                          blocking = False)
                self._wait_on_tracking_goto_loop(mode = 'store_el')
                return
            elif mode == 'store_el':
                el_store = float(tracking_mirror_positioner.configuration['el_store'])
                solar_tracker.goto_coords(el_target = el_store,
                                          blocking = False)
                self._wait_on_tracking_goto_loop(mode = 'store_end')
                return
            elif mode == 'store_end':
                self.end_busy_dialog()
                return 
            elif mode == 'zenith' or mode == "coords":
                self.end_busy_dialog()
                if self._capture_mode == "on_adjust":
                    #check to see if a capture is already running
                    image_capture = self.app.load_controller('image_capture')
                    if not image_capture.thread_isAlive():
                        self.capture_once()
                    return
            elif mode == 'sun':
                self.end_busy_dialog()
                cap = self.tracking_goto_sun_dialog.delay_then_capture_variable.get()
                if cap:
                    dt = time.time() - self._tracking_start_time
                    seconds_ahead = float(self.tracking_goto_sun_dialog.seconds_ahead_field.getvalue())
                    time_left = seconds_ahead - dt
                    self.capture_once(delay=time_left)
                
    def _update_tracking_fields(self, md):
        azimuth = md.get('azimuth')
        if not azimuth is None:
            self.tracking_fields['azimuth'].setvalue(azimuth)
        elevation = md.get('elevation')
        if not elevation is None:
            self.tracking_fields['elevation'].setvalue(elevation)
                
    def replot_raw_spectrum(self):
        self.raw_spectrum_plot_template._has_been_plotted = False
        S = self.app.get_raw_spectrum()
        B = self.app.get_background_spectrum()
        self._update_raw_spectrum_plot(S=S,B=B)

    def export_raw_spectrum(self):
        self.app.print_comment("Exporting raw spectrum...")
        dt_now = datetime.datetime.utcnow()
        dt_now_str = dt_now.strftime("%Y-%m-%d-%H_%M_%S")
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
            self.app.export_raw_spectrum(filename)
        self.app.print_comment("finished")
        
        
    def import_background_spectrum(self):
        self.app.print_comment("Importing Background Spectrum...")
        fdlg = LoadFileDialog(self.win,title="Import Background Spectrum Data")
        userdata_path = self.app.config['paths']['data_dir']    

        filename = fdlg.go(dir_or_file = userdata_path, 
                           pattern="*.csv", 
                           key = None
                          )
        if filename:
            self.app.import_background_spectrum(filename)
            path, fn = os.path.split(filename)
            self.background_filename_field.setvalue(fn)
            self.replot_raw_spectrum()
            self.replot_processed_spectrum()
            self.replot_processed_spectrum_button.config(state='normal')       #data can now be replotted
            self.export_processed_spectrum_button.config(state='normal') #data can now be exported
            self.app.print_comment("finished")
        else:
            self.app.print_comment("cancelled")
            
    def replot_processed_spectrum(self):
        self.processed_spectrum_plot_template._has_been_plotted = False
        S = self.app.get_raw_spectrum()
        B = self.app.get_background_spectrum()
        self._update_processed_spectrum_plot(S=S,B=B)
    
    def export_processed_spectrum(self):
        self.app.print_comment("Exporting proccesed spectrum...")
        dt_now = datetime.datetime.utcnow()
        dt_now_str = dt_now.strftime("%Y-%m-%d-%H_%M_%S")
        #get some metadata for title
        frametype = self.app.last_capture_metadata['frametype']
        exptime   = int(self.app.last_capture_metadata['exposure_time'])
        default_filename = "%s_proc_spectrum-%s_exptime=%dms.csv" % (dt_now_str,frametype,exptime) 
        fdlg = SaveFileDialog(self.win,title="Save Processed Spectrum Data")
        userdata_path = self.app.config['paths']['data_dir']    

        filename = fdlg.go(dir_or_file = userdata_path, 
                           pattern="*.csv", 
                           default=default_filename, 
                           key = None
                          )
        if filename:
            self.app.export_processed_spectrum(filename)
        self.app.print_comment("finished")
        
    def save_image(self):
        self.app.print_comment("saving image...")
        dt_now = datetime.datetime.utcnow()
        dt_now_str = dt_now.strftime("%Y-%m-%d-%H_%M_%S")
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
            
    def export_conditions(self):
        self.app.print_comment("Exporting conditions data...")
        dt_now = datetime.datetime.utcnow()
        dt_now_str = dt_now.strftime("%Y-%m-%d-%H_%M_%S")
        #get some metadata for title
        default_filename = "%s_conditions.csv" % (dt_now_str,) 
        fdlg = SaveFileDialog(self.win,title="Save Conditions Data")
        userdata_path = self.app.config['paths']['data_dir']    

        filename = fdlg.go(dir_or_file = userdata_path, 
                           pattern="*.csv", 
                           default=default_filename, 
                           key = None
                          )
        if filename:
            self.app.export_conditions(filename)
            self.app.print_comment("finished.")
        else:
            self.app.print_comment("cancelled.")
            
    def clear_conditions_data(self):
        self.app.print_comment("Clearing conditions data...")
        msg = "Warning: the current conditions data will be erased."
        dlg = Pmw.MessageDialog(parent = self.win,
                                message_text = msg,
                                buttons = ('OK','Cancel'),
                                defaultbutton = 'OK',
                                title = "Clear Condition Data",
                                )
        choice = dlg.activate()
        if choice == 'OK':
            self.app.clear_conditions_data()
            #now update the plot
            self._update_conditions_plot()
            return
        else:
            return
    
    def _update_raw_spectrum_plot(self, S = None, B = None):
        if (S is None and B is None):
            return #do nothing
        figure        = self.raw_spectrum_figure_widget.get_figure()
        plot_template = self.raw_spectrum_plot_template
        title = "Raw Spectrum"
        self.raw_spectrum_plot_template.configure(title=title)
        if (not plot_template.has_been_plotted()): 
            self.app.print_comment("Replotting the Raw Spectrum.")
            figure.clear()
            Xs = []
            Ys = []
            styles = []
            labels = []
            #raw spectrum
            if S is None:
                S = np.zeros_like(B)
                Xs.append(np.arange(len(S)))
                Ys.append(S)
                styles.append(SPECTRUM_PLOT_STYLE)
                labels.append("None")
            else:
                #get some metadata for label formatting
                frametype = self.app.metadata['frametype']
                exptime   = int(self.app.metadata['exposure_time'])
                label     = "raw-%s, exptime = %d ms" % (frametype, exptime)
                Xs.append(np.arange(len(S)))
                Ys.append(S)
                styles.append(SPECTRUM_PLOT_STYLE)
                labels.append(label)
            #background
            if not B is None:
                Xs.append(np.arange(len(B)))
                Ys.append(B)
                styles.append(SPECTRUM_BACKGROUND_PLOT_STYLE)
                label = "background"
                labels.append(label)
            plot_template.plot(Xs, Ys, styles = styles, labels = labels, figure = figure)
            self.raw_spectrum_figure_widget.update()
        else:
            #get the plot line from the figure FIXME is there an easier way?
            axis = figure.axes[0]
            line0 = axis.lines[0]
            line0.set_ydata(S)
            #get some metadata for label formatting
            frametype = self.app.metadata['frametype']
            exptime   = int(self.app.metadata['exposure_time'])
            label     = "raw-%s, exptime = %d ms" % (frametype, exptime)
            line0.set_label(label)
            try:
                line1 = axis.lines[1]
                line1.set_label("background")
            except IndexError:
                pass
            axis.legend()
            self.app.print_comment("Updating Raw Spectrum data: %s" % label)
            #figure.axes[0].set_title(title)
            self.raw_spectrum_figure_widget.update()
            
    def _update_processed_spectrum_plot(self, S, B):
        if not (S is None or B is None):
            figure        = self.processed_spectrum_figure_widget.get_figure()        
            plot_template = self.processed_spectrum_plot_template
            title = "Processed Spectrum"
            self.raw_spectrum_plot_template.configure(title=title)
            self.app.print_comment("Replotting the Processed Spectrum.")
            figure.clear()
            C = S - B
            X = np.arange(len(C))
            Xs = [X]
            Ys = [C]
            plot_template.plot(Xs, Ys, figure = figure)
            self.processed_spectrum_figure_widget.update()
#            else:
#                self.app.print_comment("Updating processed Spectrum data.")
#                #get the plot line from the figure FIXME is there an easier way?
#                line = figure.axes[0].lines[0]
#                line.set_ydata(S)
#                #get some metadata for label formatting
#                frametype = self.app.metadata['frametype']
#                exptime   = int(self.app.metadata['exposure_time'])
#                label     = "raw-%s, exptime = %d ms" % (frametype, exptime)
#                line.set_label(label)
#                figure.axes[0].set_title(title)
#                self.processed_spectrum_figure_widget.update()
            
    def _update_image(self, I):
        if I is None:
            return
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
            self.optics_fields['filter_pos'].setvalue("(changing)")
            self.optics_fields['filter_B'].setvalue("(changing)")
            self.optics_fields['filter_A'].setvalue("(changing)")
        else:
            self.optics_fields['filter_pos'].setvalue(str(md['filt_pos']))
            B = md['filt_B_num']
            A = md['filt_A_num']
            B_type = md['filt_B_type']
            A_type = md['filt_A_type']
            B_label = "%d, \"%s\"" % (B,B_type)
            A_label = "%d, \"%s\"" % (A,A_type)
            self.optics_fields['filter_B'].setvalue(B_label)
            self.optics_fields['filter_A'].setvalue(A_label)
            self.filter_select_dialog.varB.set(B)
            self.filter_select_dialog.varA.set(A)
        
        
    def _update_optics_fields(self, md):
        self._update_filter_status(md)
        flatfield_state = md['flatfield_state']
        self.optics_fields['flatfield'].setvalue(str(flatfield_state))
        band = md['band']
        self.optics_fields['band'].setvalue(band)
        if band in ['O2A','H2O']:
            self.filter_select_dialog.select_band(band)
        band_adjust_pos = md['band_adjust_pos']
        if band_adjust_pos is None:
            band_adjust_pos = "(unknown)"
        self.band_adjust_position_field.setvalue(str(band_adjust_pos))
        focuser_pos = md['focuser_pos']
        self.focus_adjust_position_field.setvalue(str(focuser_pos))
        
    def condition_monitor_mode_toggle(self):
        condition_monitor = self.app.load_controller('condition_monitor')
        #cancel the next scheduled loop
        if not self._condition_monitor_after_id is None:
            self.win.after_cancel(self._condition_monitor_after_id)
        #toggle the mode
        if self._condition_monitor_mode:  #is on, turn off
            self.condition_monitor_button.config(bg='light gray', relief="raised")
            self.monitor_interval_field.component('entry').config(state='normal')
            self._condition_monitor_mode = False
            self.app.print_comment("Shutting down Condition Monitoring.")
            condition_monitor.shutdown()
            
        else:                             #is off, turn on
            self.condition_monitor_button.config(bg='green', relief="sunken")
            self.monitor_interval_field.component('entry').config(state='readonly') #dissalow entries
            self._condition_monitor_mode = True
            self.app.print_comment("Initializing Condition Monitoring.")
            condition_monitor.initialize()
            self._update_conditions_fields_loop()
    
    def _update_conditions_fields_loop(self):
        if self._condition_monitor_mode:
            condition_monitor = self.app.load_controller('condition_monitor')
            interval = int(self.monitor_interval_field.getvalue())
            sample = condition_monitor.acquire_sample()
            self.app.conditions_sample_times.append(time.time())
            dt_now = datetime.datetime.utcnow()
            dt_now_str = dt_now.strftime("%Y-%m-%d-%H:%M:%S")
            #read out all pending events
            while not condition_monitor.event_queue.empty():
                event, info = condition_monitor.event_queue.get()
                self.print_event(event,info)
            #update all the widgets
            self.condition_fields.sample_datetime_field.setvalue(dt_now_str)
            if not sample is None: #could fail on mutex lockout
                for key, widget in self.condition_fields.fields.items():
                    val = sample[key]
                    data_list = self.app.conditions_Ydata.get(key,[])
                    data_list.append(val)
                    self.app.conditions_Ydata[key] = data_list
                    val_str = "%0.2f" % val
                    widget.setvalue(val_str)
            #now update the plot
            self._update_conditions_plot()
            self.app.export_conditions(CONDITIONS_BACKUP_FILENAME) #write a backup
            self.export_conditions_button.config(state='normal') #data can now be exported
            #reschedule loop
            interval_ms = interval*1000  #milliseconds
            self._condition_monitor_after_id = self.win.after(interval_ms, self._update_conditions_fields_loop)
        else:
            return
    
    def _update_conditions_plot(self):
        figure        = self.temperature_figure_widget.get_figure()        
        plot_template = self.temperature_plot_template
        #get some metadata for plot formatting
        #title     = "Raw Spectrum (%s, %d ms)"
        #self.raw_spectrum_plot_template.configure(title=title)
        self.app.print_comment("Replotting the temperature graph.")
        figure.clear()
        labels = []
        Xs = []
        Ys = []
        X = []
        if self.app.conditions_sample_times:
            X = array(self.app.conditions_sample_times)
            X -= X[0] #make relative to start
            X /= 60.0 #convert to minutes
        for key, widget in self.condition_fields.fields.items():
            if key.endswith('_temp'):
                labels.append(key[:-len('_temp')]) #peel off the '_temp'
                Y = self.app.conditions_Ydata.get(key,[])
                Xs.append(X)
                Ys.append(Y)
        plot_template.plot(Xs, Ys, labels=labels, figure=figure)
        self.temperature_figure_widget.update()

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
        
    def abort(self):
        #abort all active controllers
        self.app.abort_controllers()
        #cache the GUI settings FIXME - is this necessary?
        self._cache_settings()
        self.win.destroy()
            
    def _close(self):
        self.app.print_comment("\tApplication Close requested.")
        #check if any controllers are still alive
        running_controllers = []
        for handle in self.app.USED_CONTROLLERS:
            self.app.print_comment("\tChecking status of controller '%s'..." % handle)
            controller = self.app.load_controller(handle)
            if controller.thread_isAlive():
                self.app.print_comment("\tRUNNING")
                running_controllers.append(handle)
            else:
                self.app.print_comment("\tSTOPPED")
        if running_controllers:
            msg = "Warning: the following controllers are still running: %r\nAre you sure you want to abort?" % running_controllers
            dlg = Pmw.MessageDialog(parent = self.win,
                                    message_text = msg,
                                    buttons = ('Cancel','Abort'),
                                    defaultbutton = 'Cancel',
                                    title = "Running Controllers Warning",
                                    )
            choice = dlg.activate()
            if choice == 'Abort':
                self.abort()
        else:
            #cache the GUI settings FIXME - is this necessary?
            self._cache_settings()
            self.win.destroy()
