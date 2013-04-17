import time
try:
    #first try new style >= 0.12 interactive shell
    from IPython.frontend.terminal.embed import InteractiveShellEmbed as IPYTHON_SHELL
except ImportError:
    #substitue old-style interactive shell
    from IPython.Shell import IPShellMatplotlib as IPYTHON_SHELL

from automat.core.threads.interruptible_thread import InterruptibleThread
from automat.core.hwcontrol.config.configuration import Configuration
import yes_o2ab.pkg_info

__BANNER  = ['*'*80,
             '* YES O2AB Shell',
             '*     author: cwv@yesinc.com',
             '*'*80]
__BANNER  = '\n'.join(__BANNER)

DEFAULT_SEARCHPATHS = ['.', yes_o2ab.pkg_info.platform['config_filedir']]
DEFAULT_INTERFACE_MODE = 'interactive'

class Application:
    def __init__(self, commands = None):
        #self.searchpaths = searchpaths
        self.config = None
        self.user_ns  = {}
        if commands is None:
            commands = {}
        self.commands = commands
        
    def load(self):
        self._load_config()
        self._load_all_devices()
        self._load_all_controllers()
        
    def _load_config(self):
        #cfg_service = ConfiguratorService(searchpaths=self.searchpaths)
        #self.config = cfg_service.request_config_dialog()
        config_filepath = yes_o2ab.pkg_info.platform['config_filepath'] 
        self.config  = Configuration(config_filepath)
        
    def _load_all_devices(self):
        for name in self.config['devices'].keys():
            print "Loading device '%s'..." % name,
            try:
                device = self.config.load_device(name)
                print "success."
            except Exception, exc:
                print "failed loading device '%s' with exception: %s" % (name, exc)

    def _load_all_controllers(self):
        try:
            controllers_dict = self.config['controllers']
            for name in controllers_dict.keys():
                print "Loading controller '%s'..." % name,
                try:
                    controller = self.config.load_controller(name)
                    print "success."
                except Exception, exc:
                    print "failed loading controller '%s' with exception: %s" % (name, exc)
        except KeyError:
            pass


    def start_shell(self, msg = ""):
        status_msg = []
        status_msg.append(msg)
        
        #load convenient modules
        self.user_ns['time'] = time
        
        #find the available devices
        items = self.config._device_cache.items()
        items.sort()
        status_msg.append("Available devices:")
        for name, device in items:
            status_msg.append("\t%s" % name)
            #add device name to the user name space
            self.user_ns[name] = device
        
        #find the available controllers
        items = self.config._controller_cache.items()
        items.sort()
        status_msg.append("Available controllers:")
        for name, controller in items:
            status_msg.append("\t%s" % name)
            #add controller name to the user name space
            self.user_ns[name] = controller  
        
        #add all the special commands to the namespace
        self.user_ns.update(self.commands) 

        #complete the status message
        status_msg.append('')
        status_msg.append("-- Hit Ctrl-D to exit. --")
        status_msg = '\n'.join(status_msg) 
        #start the shell
        ipshell = None
        try:
            ipshell = IPYTHON_SHELL(user_ns = self.user_ns, banner1 = status_msg) #FIXME change made for ipython >= 0.13
            ipshell.mainloop() #FIXME change made for ipython >= 0.13
        except TypeError: #FIXME support older versions
            ipshell = IPYTHON_SHELL(user_ns = self.user_ns)
            ipshell.mainloop(banner = status_msg)
            
################################################################################
# Commands definition
import Queue, threading, locale
    
from automat.core.hwcontrol.controllers.controller import Controller, AbortInterrupt, NullController
################################################################################
# Utility functions
class Scheduler(InterruptibleThread):
    def __init__(self):
        self.func_queue   = Queue.Queue()
        self.output = []
        InterruptibleThread.__init__(self)
    def put_func(self,func,*args,**kwargs):
        def closed_func():
            return func(*args,**kwargs)
        self.func_queue.put(closed_func)
    def put_wait(self,wait_time):
        def closed_func():
            self.sleep(wait_time)
        self.func_queue.put(closed_func)
    def run(self):
        while not self.func_queue.empty():
            self.abort_breakout_point()
            closed_func = self.func_queue.get()
            result = closed_func()
            self.output.append(result)
            


def schedule_repeat(func,args_list = [],wait_time = 0.0, wait_first = True):
    if wait_first:
        time.sleep(wait_time)    
    for args in args_list:
        func(*args)
        time.sleep(wait_time)


def loop_controller(controller, event_queue = None, blocking = True):
    if event_queue is None:    
        event_queue = Queue.Queue()
    controller.thread_init(event_queue = event_queue)
    controller.initialize_devices()       
    def loop_func():
        try:
            controller.start()
            while controller.thread_isAlive() or not event_queue.empty():
                try:
                    event = event_queue.get(timeout=0.1)                
                    event_type, info = event
                    print "---\n%s:" % event_type
                    for key, val in info.items():
                            print "\t%s: %s" % (key,val)  
                except Queue.Empty:
                    pass
                except KeyboardInterrupt:
                    print " ### aborting controller... ###"
                    controller.abort()
        finally:
            controller.shutdown()

    if blocking:
        loop_func()
    else:
        thread = threading.Thread(target=loop_func)
        thread.start()

def app_launch(event_queue = None):
    global __user_ns
    if event_queue is None:    
        event_queue = Queue.Queue()
    app = None
    if not LaunchApplication is None:
        app = LaunchApplication(event_queue = event_queue)
        __user_ns['app'] = app
    return app

__commands = {}
__commands['Scheduler']       = Scheduler
__commands['schedule_repeat'] = schedule_repeat
__commands['loop_controller'] = loop_controller
__commands['app_launch']      = app_launch 

###############################################################################
# Main
def main():
    app = Application(commands=__commands)
    app.load()
    app.start_shell(msg = __BANNER)

