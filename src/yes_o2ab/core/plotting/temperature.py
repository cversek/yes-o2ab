"""
spectra.py

"""
from matplotlib.font_manager import FontProperties
from automat.core.plotting.plots import MultiPlot

###############################################################################
class TemperaturePlot(MultiPlot):
    """ A chart for displaying spectra
    """
    def __init__(self,
                 title      = 'Thermal Monitoring',
                 xlabel     = r'Time (minutes)',
                 ylabel     = r'Temperature $^{\circ}$C',
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
