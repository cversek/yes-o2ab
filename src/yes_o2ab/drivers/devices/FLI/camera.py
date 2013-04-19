###############################################################################
#Dependencies
#standard python
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
        self._driver.set_image_area(ul_x,ul_y,lr_x,lr_y)
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
        self._driver.set_exposure(exptime = exptime, frametype = frametype)
        self._driver.set_bitdepth(bitdepth)
        img = self._driver.take_photo()
        #cache the image
        self.last_image = img       
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
        return self._driver.read_CCD_temperature()
    
    def get_CH_temp(self):
        "gets the Camera cooler's Hot-side temperature in degrees Celcius"
        return self._driver.read_base_temperature()
        
    def get_CC_power(self):
        "gets the Camera cooler's power in watts"
        return self._driver.get_cooler_power()
           
    #--------------------------------------------------------------------------
      

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
    camera = get_interface(serial_number='ML0133911')
