###############################################################################
#Standard Python
try:
    from collections import OrderedDict
except ImportError:
    from yes_o2ab.support.odict import OrderedDict
#3rd party
import numpy as np
#Automat framework provided
from automat.core.data_processing.datasets import DataSet
#yes_o2ab framework provided
###############################################################################
class ConditionsDataSet(DataSet):
    def __init__(self, t, Ys, metadata = None):
        fields  = [t] + Ys
        names   = ['timestamp',
                   'CC_temp',
                   'CH_temp',
                   'CC_power',
                   'SA_press_raw_voltage',
                   'SA_temp_raw_voltage',
                   'SA_humid_raw_voltage',
                   'FW_temp',
                   'OT_temp',
                   'FB_temp',
                   'GR_temp',
                   'MB_temp',
                   'EB_temp',
                   'RA_temp',
                   'OA_temp',
                   'windspeed',
                  ]
        if metadata is None:
            metadata = OrderedDict()
        DataSet.__init__(self, fields, names=names, metadata=metadata)
