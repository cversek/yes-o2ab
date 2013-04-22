#!/usr/bin/python
"""   
desc:  Setup script for 'yes_o2ab' package.
auth:  Craig Wm. Versek (cwv@yesinc.com)
date:  12/28/2012
notes: install with "python setup.py install"
"""
import platform, os, shutil

PACKAGE_METADATA = {
    'name'         : 'yes_o2ab',
    'version'      : 'dev',
    'author'       : "Craig Versek",
    'author_email' : "cwv@yesinc.com",
}
    
PACKAGE_SOURCE_DIR = 'src'
MAIN_PACKAGE_DIR   = 'yes_o2ab'
MAIN_PACKAGE_PATH  = os.path.abspath(os.sep.join((PACKAGE_SOURCE_DIR,MAIN_PACKAGE_DIR)))


#dependencies
INSTALL_REQUIRES = [
                    'automat',
                    'configobj',
                    'numpy >= 1.1.0',
                    'matplotlib >= 0.98',
                    #'pyyaml',
                    #'pmw',
                    #'pyserial',
                    ]

#scripts and plugins
ENTRY_POINTS =  { 'gui_scripts':     [
                                      'yes_o2ab_calibrate = yes_o2ab.apps.calibrate.main:main',
                                      'yes_o2ab_tempmonitor = yes_o2ab.apps.tempmonitor.main:main',
                                     ],
                 'console_scripts': [
                                      'yes_o2ab_shell  = yes_o2ab.apps.shell.shell:main',
                                      'yes_o2ab_launch = yes_o2ab.apps.launch.launch:main',
                                     ],
                }  


DEFAULT_CONFIG_FILENAME          = 'testing.cfg'
EXAMPLE_CONFIG_FILENAME          = 'EXAMPLE_basic.cfg'
LINUX_AUTOMAT_CONFIG_DIR         = '/etc/Automat'
LINUX_YES_O2AB_CONFIG_DIR        = '/etc/Automat/yes_o2ab'
LINUX_YES_O2AB_CALIBRATION_DIR   = '/etc/Automat/yes_o2ab/calibration'
EXAMPLE_CALIBRATION_FILENAME     = 'EXAMPLE_channel_temperature.yaml'

 
def setup_platform_config():
    print "\nSetting up the configuration file:"
    
    #gather platform specific data
    platform_data = {}   
    system = platform.system()
    config_filedir               = None
    default_config_filepath      = None
    example_calibration_filepath = None 
    print "detected system: %s" % system
    if system == 'Linux' or system == 'Darwin':
        if not os.path.isdir(LINUX_AUTOMAT_CONFIG_DIR):
            os.mkdir(LINUX_AUTOMAT_CONFIG_DIR)
        config_filedir = LINUX_YES_O2AB_CONFIG_DIR
        if not os.path.isdir(config_filedir):
            os.mkdir(config_filedir)
        default_config_filepath = os.sep.join((config_filedir, DEFAULT_CONFIG_FILENAME))
        if not os.path.isdir(LINUX_YES_O2AB_CALIBRATION_DIR):
            os.mkdir(LINUX_YES_O2AB_CALIBRATION_DIR)
        example_calibration_filepath = os.sep.join((LINUX_YES_O2AB_CALIBRATION_DIR, EXAMPLE_CALIBRATION_FILENAME))
    elif system == 'Windows':
        from win32com.shell import shellcon, shell
        appdata_path =  shell.SHGetFolderPath(0, shellcon.CSIDL_APPDATA, 0, 0)
        default_config_filepath = os.sep.join((appdata_path, DEFAULT_CONFIG_FILENAME))
    
    #if the configuration file does NOT exist, than copy the example file to that location
    if not os.path.isfile(default_config_filepath):
        print "copying the example config file to '%s', please change these settings to match your system" % default_config_filepath
        shutil.copy(EXAMPLE_CONFIG_FILENAME,default_config_filepath)
    else:
        print "settings file already exists at '%s'; not overwriting; check the documention to see if additional settings are required" % default_config_filepath
    raw_input("press 'Enter' to continue...")
    #if the example calibration file does NOT exist, than copy the example file to that location
    
    if not os.path.isfile(example_calibration_filepath):
        print "copying the example calibration file to '%s', please change these settings to match your system" % example_calibration_filepath
        shutil.copy(EXAMPLE_CALIBRATION_FILENAME,example_calibration_filepath)
    else:
        print "calibration file already exists at '%s'; not overwriting; check the documention to see if additional settings are required" % example_calibration_filepath
    raw_input("press 'Enter' to continue...")

    #autogenerate the package information file
    platform_data['system']                  = system
    platform_data['config_filedir']          = config_filedir
    platform_data['config_filepath'] = default_config_filepath
    pkg_info_filename   = os.sep.join((MAIN_PACKAGE_PATH,'pkg_info.py'))
    pkg_info_file       = open(pkg_info_filename,'w')
    pkg_info_file.write("metadata = %r\n" % PACKAGE_METADATA)
    pkg_info_file.write("platform = %r"   % platform_data)
    pkg_info_file.close()

if __name__ == "__main__":
    from ez_setup   import use_setuptools
    use_setuptools()    
    from setuptools import setup, find_packages    
    setup_platform_config()
    setup(package_dir      = {'':PACKAGE_SOURCE_DIR},
          packages         = find_packages(PACKAGE_SOURCE_DIR),
          
          #non-code files
          package_data     =   {'': ['*.yaml','*.yml', '*.csv']},

          #install_requires = INSTALL_REQUIRES,
          entry_points     = ENTRY_POINTS,  
          **PACKAGE_METADATA
         )
     

