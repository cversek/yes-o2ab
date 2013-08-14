#Standard Python
try:
    from collections import OrderedDict
except ImportError:
    from yes_o2ab.support.odict import OrderedDict
#local
from converters import TimeStamp_conv, DateTime_conv, safe_int_conv, safe_float_conv

SPECTRUM_DATA_FIELD_NAMES = ['pixel_column','raw_intensity', 'background_intensity','corrected_intensity']

SPECTRUM_METADATA_CONVERTERS = OrderedDict([
    ('timestamp'             , TimeStamp_conv ),
    ('frametype'             , str            ),
    ('exposure_time'         , safe_int_conv  ),
    ('rbi_num_flushes'       , safe_int_conv  ),
    ('rbi_exposure_time'     , safe_int_conv  ),
    ('flatfield_state'       , str            ),
    ('band'                  , str            ),
    ('filt_pos'              , safe_int_conv  ),
    ('filt_B_num'            , safe_int_conv  ),
    ('filt_A_num'            , safe_int_conv  ),
    ('filt_B_type'           , str            ),
    ('filt_A_type'           , str            ),
    ('band_adjust_pos'       , safe_int_conv  ),
    ('focuser_pos'           , safe_int_conv  ),
    ('CC_temp'               , safe_float_conv),
    ('CH_temp'               , safe_float_conv),
    ('CC_power'              , safe_float_conv),
    ('SA_press'              , safe_float_conv),
    ('SA_temp'               , safe_float_conv),
    ('SA_humid'              , safe_float_conv),
    ('FW_temp'               , safe_float_conv),
    ('OT_temp'               , safe_float_conv),
    ('FB_temp'               , safe_float_conv),
    ('GR_temp'               , safe_float_conv),
    ('MB_temp'               , safe_float_conv),
    ('EB_temp'               , safe_float_conv),
    ('RA_temp'               , safe_float_conv),
    ('OA_temp'               , safe_float_conv),
    ('windspeed'             , safe_float_conv),
])
