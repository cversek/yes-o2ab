###############################################################################
#Dependencies
#standard python

#Automat framework provided
from automat.core.hwcontrol.devices.device import StubDevice
#3rd party hardware vendor, install from Internet
from novas.compat import topo_planet, equ2hor, make_object, make_on_surface, make_cat_entry
from novas.compat.eph_manager import ephem_open
#local imports
from julian_clock import JulianClock 
###############################################################################

HEIGHT_DEFAULT      = 0       #meters
TEMPERATURE_DEFAULT = 20      #degrees C
PRESSURE_DEFAULT    = 1010.0  #milibar        
###############################################################################
class Interface(StubDevice):
    def __init__(self, 
                 latitude, 
                 longitude, 
                 height = HEIGHT_DEFAULT, 
                 ephem_filepath = None,
                 deltat_preds_filepath = None
                ):
        ephem_open(ephem_filepath)  #locate the ephemeris data, needed for subsequent NOVAS calls
        dummy_star = make_cat_entry('DUMMY', 'xxx', 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0) 
        self._sun = make_object(0, 10, 'Sun', dummy_star) #type 0, number 10 denotes the Sun
        self._latitude  = latitude 
        self._longitude = longitude
        self._height    = height
        self._temperature = TEMPERATURE_DEFAULT
        self._pressure  = PRESSURE_DEFAULT
        self._update_geo_loc()
        self._julian_clock = JulianClock(deltat_preds_filepath)
        
    def identify(self):
        idn = "Solar Epheremis @ lat. %0.2f, lon. %0.2f, height %0.1f" % (self._latitude,
                                                                          self._longitude,
                                                                          self._height)
        return idn
        
    def set_temperature(self, temperature):
        self._temperature = temperature
        self._update_geo_loc()
    
    def set_pressure(self, pressure):
        self._pressure = pressure
        self._update_geo_loc()
        
    
    def update(self):
        jd = self._julian_clock.now()
        el, az = self._compute_local_coords(jd)
        return (jd, el, az)
    
    def predict(self, seconds, jd = None):
        if jd is None:
            jd = self._julian_clock.now()
        jd_future = self._julian_clock.seconds_ahead(seconds,jd)
        el_future, az_future = self._compute_local_coords(jd_future)
        return (jd_future, el_future, az_future) 
        
    def _update_geo_loc(self):
        self._geo_loc = make_on_surface(self._latitude, 
                                        self._longitude, 
                                        self._height, 
                                        self._temperature,
                                        self._pressure
                                        )
    
    def _compute_local_coords(self, jd):
        delta_t = jd.tt_minus_ut
        jd_tt  = jd.as_tt()
        jd_ut1 = jd.as_ut1()
        rat, dect, dist = topo_planet(jd_tt, delta_t, ss_body=self._sun, position=self._geo_loc)
        (zd, az), (rar, decr) = equ2hor(jd_ut1, delta_t, 
                                        xp=0.0, 
                                        yp=0.0, 
                                        location = self._geo_loc, 
                                        ra = rat, 
                                        dec = dect, 
                                        ref_option = 2
                                       )
        el = 90 - zd
        return (el,az)
        
#------------------------------------------------------------------------------
# INTERFACE CONFIGURATOR         
def get_interface(latitude, longitude, height = None, **kwargs):
    latitude  = float(latitude)
    longitude = float(longitude)
    if height is None:
        height = HEIGHT_DEFAULT
    else:
        height    = float(height)
    return Interface(latitude,longitude,height, **kwargs)
    
################################################################################
# TEST CODE
################################################################################
if __name__ == '__main__':
    lat = 41.8239
    lon = -71.4133
    ephm = SolarEphemeris(lat,lon, ephem_filepath="./DE405.bin")
