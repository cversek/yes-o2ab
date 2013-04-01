"""
spectra.py

"""
from matplotlib.font_manager import FontProperties
from automat.core.plotting.plots import MultiPlot

###############################################################################
class RawSpectrumPlot(MultiPlot):
    """ A chart for displaying spectra
    """
    def __init__(self,
                 title      = 'Raw Spectrum',
                 xlabel     = r'Horizontal Pixel',
                 ylabel     = r'Binned Intensity',
                 styles     = ['r-','g-','b-','c-','y-','m-','k-','r--','g--','b--','c--','y--','m--','k--'],
                 **kwargs
                 ):
        MultiPlot.__init__(self,
                           title  = title,
                           xlabel = xlabel,
                           ylabel = ylabel,
                           styles = styles,
                           **kwargs
                          )
