###############################################################################
#Dependencies
#standard python
from warnings import warn
#Automat framework provided
from automat.core.hwcontrol.devices.device import Device
#3rd party hardware vendor, install from Internet
from Phidgets.PhidgetException import PhidgetException
################################################################################


################################################################################
#class for thermistor object
class Interface(Device):
    def __init__(self, 
                 freq_counter, 
                 channel,
                 MPH_per_Hz,
                 s0_MPH,
                 freq_low_limit  = 2.0,    #Hz
                 freq_high_limit = 120.0,  #Hz
                ):
        self.freq_counter = freq_counter
        self.channel      = channel
        self.MPH_per_Hz   = MPH_per_Hz
        self.s0_MPH       = s0_MPH
        self.freq_low_limit  = freq_low_limit
        self.freq_high_limit = freq_high_limit
        
    def initialize(self):
        self.freq_counter.set_enabled(self.channel)

    def identify(self):
        freq_counter_idn = self.freq_counter.identify()
        idn = "NRG40 Anemometer Sensor, channel %d on %s" % (self.channel, freq_counter_idn)
        return idn

    def read(self):
        "reads the windspeed in MPH"
        try:
            freq = self.freq_counter.get_frequency(self.channel)
            if freq <= self.freq_low_limit:
                return 0.0
            elif freq >= self.freq_high_limit:
                return float('nan')
            else:
                s = self.MPH_per_Hz*freq + self.s0_MPH #apply calibration
                return s
        except PhidgetException:
            warn("Phidget Frequency Counter value is in an unknown state, reporting value as 0.0")
            return 0.0
        
    def shutdown(self):
        self.freq_counter.shutdown()
#-------------------------------------------------------------------------------
# INTERFACE CONFIGURATOR         
def get_interface(**kwargs):
    freq_counter = kwargs.get('freq_counter')
    channel = int(kwargs.get('channel'))
    MPH_per_Hz  = float(kwargs.get('MPH_per_Hz',0.0))
    s0_MPH      = float(kwargs.get('s0_MPH',0.0))
    iface = Interface(
                      freq_counter,
                      channel, 
                      MPH_per_Hz,
                      s0_MPH
                     )
    return iface
################################################################################
# TEST CODE
################################################################################
if __name__ == "__main__":
    pass
