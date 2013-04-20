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
class SpectrumDataSet(DataSet):
    def __init__(self, S, metadata = None):
        X = np.arange(len(S))
        fields  = [X,S]
        names   = ['pixel_column','intensity']
        if metadata is None:
            metadata = OrderedDict()
        DataSet.__init__(self, fields, names=names, metadata=metadata)
