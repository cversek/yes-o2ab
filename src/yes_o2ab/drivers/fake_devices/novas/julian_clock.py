################################################################################
#Dependencies
#standard python
import time, datetime, glob
import warnings
from copy import copy
#3rd party hardware vendor, install from Internet
import pytz
from scipy import interpolate, polyfit, polyval
import numpy
from novas.compat import julian_date
################################################################################
SECONDS_PER_DAY = 60*60*24
DEFAULT_DELTAT_PREDS_FILEPATH = "deltat.preds.2012-Q4"
################################################################################
class JulianClock(object):
    def __init__(self, deltat_preds_filepath = None):
        if deltat_preds_filepath is None:
            deltat_preds_filepath = DEFAULT_DELTAT_PREDS_FILEPATH
        self._deltat_data = numpy.loadtxt(deltat_preds_filepath)
        year_float    = self._deltat_data[:,0]
        tt_minus_ut   = self._deltat_data[:,1]
        ut1_minus_utc = self._deltat_data[:,2]
        self._year_float_max = year_float.max()
        #interpolate and extrapolate table
        self._tt_minus_ut_interp   = interpolate.splrep(year_float,tt_minus_ut,k=3)   #cubic interpolation of real predictions
        self._tt_minus_ut_extrap   = polyfit(year_float,tt_minus_ut,1)                #linear extrapolation
        self._ut1_minus_utc_interp = interpolate.splrep(year_float,ut1_minus_utc,k=3)
        self._ut1_minus_utc_extrap = None
        
    def convert_from_datetime(self, dt):
        tt_minus_ut, ut1_minus_utc = self._predict_delta_t(dt)
        jd = JulianDate.from_datetime(dt, tt_minus_ut, ut1_minus_utc)
        return jd
        
    def now(self):
        dt = datetime.datetime.utcnow()
        dt = pytz.utc.localize(dt)
        return self.convert_from_datetime(dt)
        
    def seconds_ahead(self, seconds, jd=None):
        if jd is None:
            jd = self.now()
        dt = jd.to_datetime()
        td = datetime.timedelta(seconds=seconds)
        dt_ahead = dt + td
        return self.convert_from_datetime(dt_ahead)
        
    def _predict_delta_t(self, dt):
        dt = dt.astimezone(pytz.utc)
        day_of_year = int(dt.strftime("%j"))
        approx_year_float = dt.year + day_of_year/365.25
        if approx_year_float > self._year_float_max:
            warnings.warn("""deltat data is out of date for requested value at year=%0.02f, 
                             extrapolating TT - UT,
                             setting UT1 - UTC = 0""" % approx_year_float)          
            tt_minus_ut   = polyval(self._tt_minus_ut_extrap,approx_year_float)
            ut1_minus_utc = 0
        else:
            tt_minus_ut   = interpolate.splev(approx_year_float,self._tt_minus_ut_interp)
            ut1_minus_utc = interpolate.splev(approx_year_float,self._ut1_minus_utc_interp)
        return (tt_minus_ut, ut1_minus_utc)
#-------------------------------------------------------------------------------
class JulianDate(object):
    def __init__(self, year, month, day, 
                 hour=0, 
                 minute=0, 
                 second=0, 
                 microsecond=0,
                 tt_minus_ut=0,
                 ut1_minus_utc=0,
                 ):
        """The time must be specified in UTC timezone, otherwise use the 
           'from_datetime' classmethod with a timezone aware datetime object.
        """
        dt = datetime.datetime(year,month,day,hour,minute,second,microsecond)
        dt = pytz.utc.localize(dt)
        self._datetime = dt
        self.tt_minus_ut   = tt_minus_ut
        self.ut1_minus_utc = ut1_minus_utc
        
         
    def as_utc(self):
        dt = self._datetime.astimezone(pytz.utc)
        hour_float = dt.hour + dt.minute/60.0 + (dt.second + dt.microsecond*1e-6)/3600.0
        jd_utc = julian_date(dt.year,dt.month,dt.day,hour_float)
        return jd_utc
    
    def as_ut1(self):
        jd_utc = self.as_utc()
        jd_ut1  = jd_utc + (self.ut1_minus_utc)/SECONDS_PER_DAY
        return jd_ut1
        
    def as_tt(self):
        jd_utc = self.as_utc()
        jd_tt  = jd_utc + (self.tt_minus_ut + self.ut1_minus_utc)/SECONDS_PER_DAY
        return jd_tt
        
    def to_datetime(self):
        return self._datetime
        
    def __repr__(self):
        dt = self._datetime.astimezone(pytz.utc)
        rep = "JulianDate(%d, %d, %d, %d, %d, %d, %d, tt_minus_ut=%0.3f, ut1_minus_utc=%0.3f)" % (
                 dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, dt.microsecond,
                 self.tt_minus_ut, self.ut1_minus_utc
               )
        return rep
    
        
    @classmethod
    def from_datetime(cls, dt, tt_minus_ut, ut1_minus_utc):
        if dt.tzinfo is None:
            raise ValueError, "cannot accept naive datetime object"
        dt = dt.astimezone(pytz.utc)
        return cls(year   = dt.year,
                   month  = dt.month, 
                   day    = dt.day, 
                   hour   = dt.hour, 
                   minute = dt.minute, 
                   second = dt.second, 
                   microsecond = dt.microsecond,
                   tt_minus_ut = tt_minus_ut,
                   ut1_minus_utc = ut1_minus_utc,
                   )            

################################################################################
# TEST CODE
################################################################################
if __name__ == "__main__":
    JC = JulianClock()
    for i in range(10):
        jd = JC.now()
        print "The time is now:"
        print "jd:", jd
        print "jd.as_utc(): %0.30f days" % jd.as_utc()
        print "jd.as_ut1(): %0.30f days" % jd.as_ut1()
        print "jd.as_tt():  %0.30f days" % jd.as_tt()
        time.sleep(1)
        



