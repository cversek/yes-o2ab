import re

#register conversion functions for particular metadata keys
#ts is a str YEAR-MONTH-DAY-HOUR-MINUTE[-SECOND]
TIMESTAMP_SEP_REGEX = re.compile(r'[-:]|\s+')
def TimeStamp_conv(ts):
    "will convert a timestamp (epoch time) or datetime object/string into an epoch time float"
    try:
        return float(ts)
    except (ValueError, TypeError):
        segs = re.split(TIMESTAMP_SEP_REGEX,str(ts))
        #deal with old TimeStamp format
        segs = map(float,segs)
        dt = datetime.datetime(*segs) #inject tuple as arguments in order
        ts = time.mktime(dt.timetuple())
        return ts

def DateTime_conv(dt):
    "will convert timestamp or a datetime object/string into a datetime object"
    ts = TimeStamp_conv(dt)
    dt = datetime.datetime.fromtimestamp(ts)
    return dt


def safe_int_conv(num):
    try:
        return int(num)
    except ValueError:  #otherwise use the NaN object
        return 0

def safe_float_conv(num):
    try:
        return float(num)
    except ValueError:  #otherwise use the NaN object
        return float('nan')
