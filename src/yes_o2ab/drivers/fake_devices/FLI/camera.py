###############################################################################
#Dependencies
#standard python
OrderedDict = None
try:
    from collections import OrderedDict
except ImportError:
    from yes_o2ab.support.odict import OrderedDict
#Automat framework provided
from automat.core.hwcontrol.devices.instruments import Model
#other in-house packages
from FLI import USBCamera
#3rd party hardware vendor, install from Internet
import scipy
#package local
from device import FLIDevice
###############################################################################


###############################################################################
class Interface(FLIDevice):
    _driver_class = USBCamera
    def __init__(self, serial_number):
        FLIDevice.__init__(self, serial_number=serial_number)

    def set_image_area(self, ul_x, ul_y, lr_x, lr_y):
        """ Set the image area:
                ul_x - upper-left horizontal coordinate
                ul_y - upper-left vertical coordinate
                lr_x - lower-right horizontal coordinate
                lr_y - lower-right vertical coordinate
        """
        self.initialize()
        ## FIXME FAKE cannot do this
        #self._driver.set_image_area(ul_x,ul_y,lr_x,lr_y)
    #--------------------------------------------------------------------------
    # Implementation of the Camera Interface
    #--------------------------------------------------------------------------
    def take_photo(self, 
                   exptime, 
                   frametype = "normal",        
                   bitdepth  = "16bit",
                  ):
        """ Acquire an image with parameters:
                exptime   - length of exposure in milliseconds
                frametype - 'normal' or 'dark', default = 'normal'
                bitdepth  - '8bit' or '16bit', default = '16bit'
        """
        self.initialize()
        #self._driver.set_exposure(exptime = exptime, frametype = frametype)
        #self._driver.set_bitdepth(bitdepth)
        #img = self._driver.take_photo() #this call will block
        #cache the image
        self.last_image = self.fetch_image()
        return img
    
    def start_exposure(self, 
                   exptime, 
                   frametype = "normal",
                   bitdepth  = "16bit",
                  ):
        """ Start an exposure and return immediately.
            Use the method  'get_timeleft' to check the exposure progress 
            until it returns 0, then use method 'fetch_image' to fetch the image
            data as a numpy array.
            Exposure parameters:
                exptime   - length of exposure in milliseconds
                frametype - 'normal'     - open shutter exposure
                            'dark'       - exposure with shutter closed
                            'rbi_flush'  - flood CCD with internal light
                            default = 'normal'
                bitdepth  - '8bit' or '16bit', default = '16bit'
        """
        self.initialize()
#        self._driver.set_exposure(exptime = exptime, frametype = frametype)
#        self._driver.set_bitdepth(bitdepth)
#        self._driver.start_exposure()
    
    def get_exposure_timeleft(self):
        """ Returns the time left on the exposure in milliseconds.
        """
        return 0 #self._driver.get_exposure_timeleft()
        
    def fetch_image(self):
        """ Fetch the image data for the last exposure.
            Returns a numpy.ndarray object.
        """
        import os
        from scipy.misc import imread
        this_path = os.path.dirname(__file__)
        img_path = os.sep.join((this_path,"FAKE_solar_spectrumBW.gif"))
        img = imread(img_path)
        return img

    def show_image(self):
        """ displays the last taken image with pylab.imshow
        """
        scipy.misc.imshow(self.last_image)
    
    def save_image(self, filename):
        scipy.misc.imsave(filename, self.last_image)
   
    #--------------------------------------------------------------------------
    # Query Functions
    #--------------------------------------------------------------------------
    def get_CC_temp(self):
        "gets the Camera cooler's Cold-side (also CCD) temperature in degrees Celcius"
        return 0.0
    
    def get_CH_temp(self):
        "gets the Camera cooler's Hot-side temperature in degrees Celcius"
        return 0.0
        
    def get_CC_power(self):
        "gets the Camera cooler's power in watts"
        return 0.0
    
    def get_info(self):
        return OrderedDict()
        
    #--------------------------------------------------------------------------
    # Command Functions
    #--------------------------------------------------------------------------
    def set_CCD_temperature_setpoint(self, temp):
        "gets the Camera cooler's Cold-side (also CCD) temperature in degrees Celcius"
        pass
        #self._driver.set_temperature(temp)
      

#------------------------------------------------------------------------------
# INTERFACE CONFIGURATOR         
def get_interface(serial_number, **kwargs):
    obj = Interface(serial_number=serial_number)
    image_area = kwargs.pop('image_area', None)
    if not image_area is None:
        ul_x,ul_y,lr_x,lr_y = map(int,image_area)
        obj.set_image_area(ul_x,ul_y,lr_x,lr_y)
    return obj
    
###############################################################################
# TEST CODE
###############################################################################
if __name__ == "__main__":
    pass
