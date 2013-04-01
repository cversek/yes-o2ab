###############################################################################
#Constants     
###############################################################################

from yes_o2ab.apps.lib.errors import handleCrash
@handleCrash
def main():
    ###########################################################################
    import sys
    #application local
    #from lib.gui.gui                 import GUI
    from lib.application.application import Application
    from lib.application.errors      import DeviceError
    ###########################################################################
    #parse commandline options    
    from optparse import OptionParser
    OP = OptionParser()
    OP.add_option("--skip-test", dest="skip_test",default=False, action = 'store_true', 
                    help="skip over device tests")
    OP.add_option("--detach", dest="detach", default=False, action = 'store_true', 
                    help="skip over device tests")
    OP.add_option("--ignore-device-errors", dest="ignore_device_errors", default=False, action = 'store_true', 
                    help="ignore initial device errors")             
    opts, args = OP.parse_args()
      
    #initialize the control application
    app = Application(skip_test = opts.skip_test,
                      ignore_device_errors = opts.ignore_device_errors,
                     )
    if opts.detach:
        #detach the process from its controlling terminal
        from automat.system_tools.daemonize import detach 
        app.print_comment("Process Detached.")
        app.print_comment("You may now close the terminal window...")   
        detach()
#    #start the graphical interface
#    gui = GUI(app)
#    #give the app the ability to print to the GUI's textbox
#    app.setup_textbox_printer(gui.print_to_text_display)
#    #launch the app
#    gui.launch()
    app.main()
    
      
if __name__ == "__main__":
    main()
