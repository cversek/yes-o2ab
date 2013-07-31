###############################################################################
#Dependencies
#standard python
#Automat framework provided
from automat.core.hwcontrol.devices.device import Device
################################################################################


################################################################################
#class for thermistor object
class Interface(Device):
    def __init__(self, freq_counter, channel, MPH_per_Hz, s0_MPH):
        self.freq_counter = freq_counter
        self.channel      = channel
        self.MPH_per_Hz   = MPH_per_Hz
        self.s0_MPH       = s0_MPH
        
    def initialize(self):
        self.freq_counter.set_enabled(self.channel)

    def identify(self):
        freq_counter_idn = self.freq_counter.identify()
        idn = "NRG40 Anemometer Sensor, channel %d on %s" % (self.channel, freq_counter_idn)
        return idn

    def read(self):
        "reads the windspeed in MPH"
        freq = self.freq_counter.get_frequency(self.channel)
        s = self.MPH_per_Hz*freq + self.s0_MPH #apply calibration
        return s
        
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
