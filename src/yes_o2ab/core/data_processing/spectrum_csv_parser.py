# encoding: utf-8
"""
spectrum_csv_parser.py

"""
import os, datetime, re, StringIO
import numpy
import yaml

OrderedDict = None
try:
    from collections import OrderedDict
except ImportError:
    from yes_o2ab.support.odict import OrderedDict
#local

###############################################################################
# Module Constants
from common_defs import SPECTRUM_DATA_FIELD_NAMES, SPECTRUM_METADATA_CONVERTERS

METADATA_REGEX     = re.compile(r'<METADATA>((?!<[/]?METADATA>).*)<[/]METADATA>', flags = re.S)
COMMENT_LINE_REGEX = re.compile(r'^\s*[#].*$')


###############################################################################
def load(filename):
    """creates an object specification from information loaded from the file"""
    data, metadata = parsefile(filename)
    spec = {}
    spec['metadata'] = metadata
    spec['data']     = data
    return spec

###############################################################################
def parsefile(filename):
    "open the file strip out the metadata and format the data into numpy array"
    #slurp up the entire file
    f = open(filename)
    header = []
    body   = []
    for line in f:
        if COMMENT_LINE_REGEX.match(line):
            line = line.strip()
            line = line.lstrip('#')
            header.append(line)
        else:
            body.append(line)
    header = '\n'.join(header)
    body   = '\n'.join(body)
    #strip out the Metadata quickly using YAML parser
    m = METADATA_REGEX.match(header)
    metadata_text = m.group(1)
    metadata_dict = yaml.load(metadata_text)
    #now convert the metadata to an OrderedDict and handle special conversions
    metadata = OrderedDict()
    for key, conv in SPECTRUM_METADATA_CONVERTERS.items():
        metadata[key] = conv(metadata_dict[key])
    #feed the body to numpy's CSV loader as a StringIO file-like object
    D = numpy.loadtxt(StringIO.StringIO(body), delimiter=',', dtype = 'int32').transpose()
    data = {}
    for name, col in zip(SPECTRUM_DATA_FIELD_NAMES,D):
        data[name] = col
    #convert to numpy array
    return (data, metadata)

###############################################################################
# Test Code:
###############################################################################
if __name__ == '__main__':
    pass
