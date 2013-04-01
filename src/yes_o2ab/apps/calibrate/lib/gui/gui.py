###############################################################################
#Standard Python provided
import os, time, datetime, signal, socket, shelve
from Tkinter import *
#3rd party packages
import Pmw
from numpy import arange, savetxt
from FileDialog import SaveFileDialog
#Automat framework provided
from automat.core.gui.text_widgets           import TextDisplayBox
from automat.core.gui.pmw_custom.entry_form  import EntryForm
from automat.core.plotting.tk_embedded_plots import EmbeddedFigure
#yes_o2ab framework provided
from yes_o2ab.core.plotting.spectra          import RawSpectrumPlot
#application local
from settings_dialog import SettingsDialog
###############################################################################
# Module Constants
WINDOW_TITLE      = "YES O2AB Calibrate"
WAIT_DELAY        = 100 #milliseconds
TEXT_BUFFER_SIZE  = 10*2**20 #ten megabytes
SPECTRAL_FIGSIZE  = (10,5) #inches

DEFAULT_EXPOSURE_TIME = 10 #milliseconds
DEFAULT_RUN_INTERVAL  = 10 #seconds

CONFIRMATION_TEXT_DISPLAY_TEXT_HEIGHT = 40
CONFIRMATION_TEXT_DISPLAY_TEXT_WIDTH  = 80

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
    d = Dialog.Dialog(title=title, text = message_text, bitmap=bitmap, default=default, strings=buttons)
    return buttons[d.num]
      
###############################################################################
class GUI:
    def __init__(self, application):
        self.app = application
        #signal that experiment is running
        self.experiment_mode = False
        self.app.print_comment("Starting GUI interface:")
        self.app.print_comment("please wait while the application loads...")
        #build the GUI interface as a seperate window
        win = Tk()
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
        left_panel = Frame(win)
        #button on top
        self.run_continually_button  = Button(left_panel,text='Run Continually',command = self.run_continually)
        self.run_continually_button.pack(side='top',fill='x', anchor="nw")
        self.stop_button = Button(left_panel,text='Stop',command = self.stop, state='disabled')
        self.stop_button.pack(side='top',fill='x', anchor="nw")
        self.run_once_button = Button(left_panel,text='Run Once',command = self.run_once)
        self.run_once_button.pack(side='top',fill='x', anchor="nw")
        #buttons on bottom in reverse order
        self.export_button = Button(left_panel,text='Export Data',command = self.export_data, state='disabled')
        self.export_button.pack(side='bottom',fill='x', anchor="sw")
        self.change_settings_button = Button(left_panel,text='Change Settings',command = self.change_settings)
        self.change_settings_button.pack(side='bottom',fill='x', anchor="sw")
        left_panel.pack(fill='y',expand='no',side='left', padx = 10)
        #build the middle panel
        right_panel = Frame(win)
        self.text_display  = TextDisplayBox(right_panel,text_height=15, buffer_size = TEXT_BUFFER_SIZE)
        #create an tk embedded figure for spectral display
        self.spectral_plot_template = RawSpectrumPlot()
        self.spectral_figure_widget = EmbeddedFigure(right_panel, figsize=SPECTRAL_FIGSIZE)
        self.spectral_figure_widget.pack(side='left',fill='both', expand='yes')
        self.text_display.pack(side='left',fill='both',expand='yes')
        right_panel.pack(fill='both', expand='yes',side='right')
        #build the confirmation dialog
        self.settings_dialog = SettingsDialog(self.win)
        self.settings_dialog.withdraw()
        self._load_settings()
        #run modes
        self._is_running = False
       
    def launch(self):
        #run the GUI handling loop
        IgnoreKeyboardInterrupt()
        self.win.deiconify()
        self.win.mainloop()
        NoticeKeyboardInterrupt()

    def change_settings(self):
        self.settings_dialog.activate()
     
    def run_continually(self):
        #cache the GUI settings FIXME - is this necessary?
        self._cache_settings()
        #disable all the buttons, except the stop button
        self.run_once_button.config(state='disabled')
        self.run_continually_button.config(state='disabled')
        self.stop_button.config(state='normal')
        self._is_running = True
        self._run_continually_loop()

    def _run_continually_loop(self):
        if self._is_running:
            self.run_once()
            run_interval = int(1000*float(self.settings_dialog.form['run_interval'])) #convert to milliseconds
            #reschedule loop            
            self.win.after(run_interval,self._run_continually_loop)
        else:
            #enable all the buttons, except the stop button
            self.run_once_button.config(state='normal')
            self.run_continually_button.config(state='normal')
            self.stop_button.config(state='disabled')
            #do not reschedule loop
            

    def run_once(self):
        exptime = int(self.settings_dialog.form['exposure_time'])
        S = self.app.acquire_spectrum(exptime)
        #S = arange(1000)    
        self._update_plot(S)
        self.export_button.config(state='normal') #data can now be exported

    def stop(self):
        self._is_running = False

    def export_data(self):
        self.app.print_comment("exporting data...")
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
            S = self.app.last_spectrum
            savetxt(filename, S, 
                    fmt='%.18e',
                    delimiter=","
                   )
       
    def _update_plot(self, S):
        figure = self.spectral_figure_widget.get_figure()        
        figure.clear()
        Xs = [arange(len(S))]
        Ys = [S]
        self.spectral_plot_template.plot(Xs, Ys,
                                         figure = figure
                                        )
        self.spectral_figure_widget.update() 
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
            self.settings_dialog.form['run_interval']  = settings.get('run_interval', DEFAULT_RUN_INTERVAL)
            settings.close() 
        else:
            self.app.print_comment("failed to find settings file '%s'" % SETTINGS_FILEPATH)
                  
    def _cache_settings(self):
        self.app.print_comment("caching to settings file '%s'" % SETTINGS_FILEPATH)
        settings = shelve.open(SETTINGS_FILEPATH)
        settings['exposure_time'] = self.settings_dialog.form['exposure_time']
        settings['run_interval']  = self.settings_dialog.form['run_interval']
        settings.close()
        
            
    def _close(self):
        #cache the GUI settings FIXME - is this necessary?
        self._cache_settings()
        self.win.destroy()
