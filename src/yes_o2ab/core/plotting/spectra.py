"""
spectra.py

"""
from matplotlib.font_manager import FontProperties
from automat.core.plotting.plots import MultiPlot

TITLE  = 'Raw Spectrum'
XLABEL = r'Horizontal Pixel'
YLABEL = r'Binned Intensity'
STYLES = ['r-','g-','b-','c-','y-','m-','k-','r--','g--','b--','c--','y--','m--','k--']
YTICKS_POWERLIMITS = (-2,3)

###############################################################################
class RawSpectrumPlot(MultiPlot):
    """ A chart for displaying spectra
    """
    def __init__(self,
                 title      = TITLE,
                 xlabel     = XLABEL,
                 ylabel     = YLABEL,
                 styles     = STYLES,
                 yticks_powerlimits = YTICKS_POWERLIMITS,
                 **kwargs
                 ):
        MultiPlot.__init__(self,
                           title  = title,
                           xlabel = xlabel,
                           ylabel = ylabel,
                           styles = styles,
                           yticks_powerlimits = yticks_powerlimits,
                           **kwargs
                          )
