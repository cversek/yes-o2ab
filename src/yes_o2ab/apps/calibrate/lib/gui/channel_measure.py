###############################################################################
import time,Queue

from Tkinter import *
from FileDialog import SaveFileDialog
import Pmw

from automat.core.plotting.tk_embedded_plots        import EmbeddedFigure
from pyEIS.core.plotting.eis_plots                  import ImpedanceThreeViewPlot
from pyEIS.core.data_processing.impedance_dataset   import ImpedanceDataSet
from pyEIS.core.events.eis_event_parser             import EISEventParser

###############################################################################
CHANNEL_MEASURE_FIGSIZE = (9,7)
WAIT_DELAY    = 100 #milliseconds
DEFAULT_POLLING_INTERVAL = 20 #seconds
    
###############################################################################    
class ChannelMeasure(Toplevel):
    def __init__(self, channel_configurator, application):
        self.channel_configurator = channel_configurator
        self.app     = application
        #configure the event parser
        self.event_parser = EISEventParser()
        self.figure_widget = None
        #signal that the window is open
        self.is_open = False
        self.widgets_made = False

    def make_widgets(self):
        #build the GUI components
        Toplevel.__init__(self)
        self.withdraw() #hide in the background
        #handle closing the dialog window
        self.wm_title("Channel %d - Measurement" % self.channel_configurator.channel)

        left_frame = Frame(self)
        
        button_bar = Frame(left_frame)
        button_pack_opts = {'side':'top','fill':'x', 'expand':'yes', 'anchor':'nw'}
        self.start_button  = Button(button_bar,text="Start",command=self.start_measurement)
        self.start_button.pack(**button_pack_opts)
        button_bar.pack(side='top', fill='x', expand='no', anchor='nw')

        self.mode_selection = Pmw.RadioSelect(left_frame,
                                              label_text = 'Mode Settings',
                                              buttontype = 'checkbutton',
                                              labelpos   = 'n',
                                              orient     = 'vertical',
                                             )
        self.mode_selection.add('monitor-temperature', text = 'Monitor Temp.?')
        self.mode_selection.setvalue(['monitor-temperature'])        
        self.mode_selection.pack(side='top',fill='x',expand='yes', anchor='nw', pady=10)

        
        left_frame.pack(side='left', fill='both', padx=10)
         
               
        if self.figure_widget is None:
            #attach and pack widgets
            #create an tk embedded figure
            self.figure_widget = EmbeddedFigure(self, figsize=CHANNEL_MEASURE_FIGSIZE)
            self.figure_widget.pack(side='right',fill='both', expand='yes')

    def launch(self):
        if not self.widgets_made:
            self.make_widgets() #make widgets right before poping up

        self.is_open = True     
        #let the X button cleanly close the window
        self.protocol("WM_DELETE_WINDOW", self._close)
        #initialize the impedance plot
        self.plot_template = ImpedanceThreeViewPlot()
        self._update_plot() #get an empty Impedance 3-view plot
        #make window show up
        self.deiconify()
        self.up = True

    def timer_measurement(self):
        from automat.core.hwcontrol.controllers.callbacks import NonThreadedCallbackBase
        class EISTimerCallback(NonThreadedCallbackBase):
            def run(self2):
                self.start_measurement()
                
                        

    
    def start_measurement(self):
        #switch the X button to abort the measurement
        self.protocol("WM_DELETE_WINDOW", self.abort)
        self.polling_interval     = DEFAULT_POLLING_INTERVAL   
        #the hardware control will run as a separate thread  
        self.modes = []#self.mode_selection.getvalue()      
#        if 'monitor-temperature' in self.modes:
#            #start the temperature polling loop
#            self.app.start_temperature_polling_loop(polling_interval = self.polling_interval) 
#            #wait for the first polling event before starting measurement          
#            self.waitfor_event('POLL', self.start_measurement_loop)
#        else:
        self.start_measurement_loop()
              
    def start_measurement_loop(self):
        self.disable()
        #start with a fresh event parser
        self.event_parser = EISEventParser()
        self._update_plot() #zero out the plot
        #start the measurement waiting loop
        self.impedance_measurement_loop()
        config  = self.channel_configurator.get_config()
        channel = self.channel_configurator.channel 
        self.app.start_single_measurement(config, channel = channel)  

        
    def waitfor_event(self, wait_event_type, callback = lambda: None):
        """wait in a loop until the an event of type 'event_type' is received"""
        try:
            event = self.app.event_queue.get(block=False)
            #print out the event YAML style
            self.app.print_event(event)
            #feed events to the parser
            self.event_parser.feed(event)
            #process the events  to update plot
            event_type, content = event
            if event_type == wait_event_type:
                callback()
                return #exit this loop          
        except Queue.Empty:
            pass
        #reschedule this loop
        self.after(WAIT_DELAY,self.waitfor_event, wait_event_type, callback)
    
    def impedance_measurement_loop(self):
        """Try getting an event from the queue, if available; handle it; then
           reschedule after WAIT_DELAY milliseconds
        """
        try:
            event = self.app.event_queue.get(block=False)
            #print out the event YAML style
            self.app.print_event(event)
            #feed events to the parser
            self.event_parser.feed(event)
            #process the events  to update plot
            event_type, content = event
            if   event_type == 'IMPEDANCE_SWEEP_ABORTED':
                return #quit the event loop
            elif event_type == 'IMPEDANCE_SWEEP_COMPLETED':
                #finished with the measurement, so stop
                self.stop()
                return #quit the event loop
            elif event_type == 'IMPEDANCE_MEASUREMENT':
                self._update_plot()
            #self.text_display.print_text(buff)
        except Queue.Empty:
            pass
        #reschedule this loop
        self.after(WAIT_DELAY,self.impedance_measurement_loop) 
    
    def abort(self, event = None):
        #stop the hardware thread
        self.app.abort_single_measurement()
        if 'monitor-temperature' in self.modes:
            self.app.stop_temperature_polling_loop()
        self.is_active = False
        self._close()
        #reenable the controls
        self.enable()
            
    def stop(self, event = None):
        #stop the hardware thread
        if 'monitor-temperature' in self.modes:
            self.app.stop_temperature_polling_loop()
        #disable the X button for the window
        self.protocol("WM_DELETE_WINDOW", lambda: None)
        d = Pmw.MessageDialog(parent       = self, 
                              message_text ="Measurement Finished\nSave the data?",
                              buttons      = ('Save','Discard'),
                              )
        resp = d.activate()
        #reenable the controls
        self.enable()
        #switch the X button to close the window
        self.protocol("WM_DELETE_WINDOW", self._close)
        #save the data
        if resp == 'Save':
            self.save_data()
        
    def save_data(self):
        ID        = self.event_parser.curr_sweep_impedance_dataset
        owner     = ID.get_metadata('owner')
        chan      = ID.get_metadata('channel')
        samp_name = ID.get_metadata('sample_name')
        default_filename = "%s_CH%s_%s.z" % (owner, chan, samp_name)
        fdlg = SaveFileDialog(self,title="Save Impedance Data")
        data_dir = self.app.config['paths']['data_dir']
        filename = fdlg.go(dir_or_file = data_dir, 
                           pattern="*.z", 
                           default=default_filename, 
                           key = None
                          )
        if filename:
            f = open(filename,'w')
            f.write(ID.to_zplot())
            f.close()
    
    def disable(self):
        "disable all controls"
        self.start_button.config(state='disabled')

    def enable(self):
        "reenable all controls"
        self.start_button.config(state='normal')

    def _update_plot(self):
        ID     = self.event_parser.curr_sweep_impedance_dataset
        figure = self.figure_widget.get_figure()        
        figure.clear()
        self.plot_template.plot(Xs=[[ID['Z_re']],[ID['frequency']],[ID['frequency']]],
                                Ys=[[ID['Z_im']],[ID['Z_mag']],[ID['Z_pha']]],
                                figure = figure
                               )
        self.figure_widget.update() 
    
    def destroy(self):
        self.figure_widget.destroy()
        Toplevel.destroy(self)    
        
    def _close(self, event=None):
        self.withdraw()
        self.up = False
        self.is_open = False
        
