"""
spectra.py

"""
from matplotlib.font_manager import FontProperties
from automat.core.plotting.plots import MultiPlot

###############################################################################
USE_LEGEND = True
class TemperaturePlot(MultiPlot):
    """ A chart for displaying spectra
    """
    def __init__(self,
                 title      = 'Thermal Monitoring',
                 xlabel     = r'Time (minutes)',
                 ylabel     = r'Temperature $^{\circ}$C',
                 styles     = ['r-','g-','b-','c-','y-','m-','k-','r--','g--','b--','c--','y--','m--','k--'],
                 use_legend = USE_LEGEND,
                 **kwargs
                 ):
        MultiPlot.__init__(self,
                           title  = title,
                           xlabel = xlabel,
                           ylabel = ylabel,
                           styles = styles,
                           use_legend = use_legend,
                           **kwargs
                          )
