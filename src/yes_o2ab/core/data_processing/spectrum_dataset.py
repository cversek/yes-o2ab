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
#local
import spectrum_csv_parser
###############################################################################
# Module Constants
from common_defs import SPECTRUM_DATA_FIELD_NAMES, SPECTRUM_METADATA_CONVERTERS

###############################################################################
class SpectrumDataSet(DataSet):
    def __init__(self,
                 raw_intensity,
                 background_intensity = None,
                 corrected_intensity  = None,
                 pixel_column         = None,
                 metadata = None
                ):
        S = np.array(raw_intensity)
        B = None
        if not background_intensity is None:
            B = np.array(background_intensity)
        else:
            B = np.zeros_like(S)
        C = None
        if not corrected_intensity is None:
            C = np.array(corrected_intensity)
        else:
            C = S - B
        X = None
        if not pixel_column is None:
            X = np.array(pixel_column)
        else:
            X = np.arange(len(S))
            
        fields  = [X,S,B,C]
        names   = SPECTRUM_DATA_FIELD_NAMES
        if metadata is None:
            metadata = OrderedDict()
        DataSet.__init__(self, fields, names=names, metadata=metadata)
    #--------------------------------------------------------------------------
    # CLASS METHODS
    @classmethod
    def load(cls, filename):
        base, ext = os.path.splitext(filename)
        if   ext == ".csv":
            return cls.from_csv(filename)
        elif ext == ".db":
            return cls.from_shelf(filename)
        elif ext == ".hd5":
            raise NotImplementedError("HDF5 formatting is not ready, please check back later!")
        else:
            raise ValueError("the filename extension '%s' was not recognized, it must end with: .csv, .db, or .hd5" % ext)
        
    @classmethod
    def from_dict(cls, spec):
        """Class factory function which builds a SpectrumDataSet obj from 
           a dictionary specification.
        """
        data = spec['data']
        obj = cls( raw_intensity        = data['raw_intensity'],            #required!
                   background_intensity = data.get('background_intensity'), #rest are optional
                   corrected_intensity  = data.get('corrected_intensity'),
                   pixel_column         = data.get('pixel_column'),
                 )
        return obj
        
    @classmethod
    def from_csv(cls, filename):
        """ Class factory function: load and parse a YES O2AB CSV 
            (comma seperated values, with metadata) format and construct
            a SpectrumDataSet object.
        """
        spec = spectrum_csv_parser.load(filename)
        return cls.from_dict(spec)
