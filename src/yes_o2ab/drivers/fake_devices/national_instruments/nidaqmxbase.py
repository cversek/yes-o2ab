##############################################################################
import platform, ctypes
from ctypes import CFUNCTYPE, POINTER, c_char_p, c_bool, c_void_p

##############################################################################
# module level constants
DEBUG = True
ERROR_BUFFER_SIZE = 1000
DEFAULT_LINUX_LIB_PATH   = "/usr/local/natinst/nidaqmxbase/lib/libnidaqmxbase.so.3.5.0"
DEFAULT_WINDOWS_LIB_PATH = ""

###############################################################################
# Setup some typedefs and constants
# to correspond with values in
# /usr/local/natinst/nidaqmxbase/include/NIDAQmxBase.h

#def typedef(ctype, type_name):
#    return type(type_name, (ctype,), dict(ctype.__dict__))

def typedef(ctype, type_name):
    return ctype


# NI-DAQBasemx typedefs
int8       = typedef(ctypes.c_byte,      'int8')
uInt8      = typedef(ctypes.c_ubyte,     'uInt8')
int16      = typedef(ctypes.c_short,     'int16')
uInt16     = typedef(ctypes.c_ushort,    'uInt16')
int32      = typedef(ctypes.c_long,      'int32')
uInt32     = typedef(ctypes.c_ulong,     'uInt32')
uInt64     = typedef(ctypes.c_ulonglong, 'uInt64')
float64    = typedef(ctypes.c_double,    'float64')
bool32     = typedef(uInt32,             'bool32')
#TaskHandle = typedef(POINTER(uInt32),    'TaskHandle')  #NOTE: in original DAQmx, this is not a pointer!
TaskHandle = c_void_p

# NI-DAQBasemx constants
DAQmx_Val_Cfg_Default       = int32(-1)
DAQmx_Val_Volts             = 10348
DAQmx_Val_Rising            = 10280
DAQmx_Val_FiniteSamps       = 10178
DAQmx_Val_GroupByChannel    = 0
DAQmx_Val_ChanForAllLines   = 1
DAQmx_Val_RSE               = 10083
DAQmx_Val_Volts             = 10348
DAQmx_Val_ContSamps         = 10123
DAQmx_Val_GroupByScanNumber = 1

# module helper functions
def check_error_int32(result, func, arguments):
    #must be integer error code    
    assert func.restype is int32
    if DEBUG:
        print "result = %d" % result     
    if result < 0:
        msg = []
        #request error info from the library            
        buf = ctypes.create_string_buffer('\000' * ERROR_BUFFER_SIZE)
        libnidaqmxbase.DAQmxBaseGetErrorString(err,ctypes.byref(buf),ERROR_BUFFER_SIZE)
        msg.append("NIDAQmxBase call failed with error %d: %s"%(result,repr(buf.value)))
        #add info from the python function call
        msg.append("\tthe specified argtypes: %s" % func.argtypes) 
        msg.append("\twas called with arguments: %s" % arguments)      
        msg = '\n'.join(msg)            
        raise RuntimeError(msg)

# NI-DAQBasemx Function Declarations
class CFUNC_Prototype:
    def __init__(self, name, doc_header = None, restype = int32, errcheck = check_error_int32, argtypes = None, argnames = None, defaults = None, direction_flags = None):
        self.name       = name
        self.doc_header = doc_header        
        self.restype  = restype
        self.errcheck = errcheck
        if argtypes is None:
            argtypes = []
        else:
            assert len(argtypes) == len(argnames)
        self.argtypes = argtypes
        if argnames is None:
            argnames = []
        else:
            assert len(argnames) == len(argtypes)
        self.argnames = argnames
        if defaults is None:
            defaults = []
        else:
            assert len(defaults) == len(argtypes)
        self.defaults = defaults
        if direction_flags is None:
            direction_flags = []
        else:
            assert len(direction_flags) == len(argtypes)
        self.direction_flags = direction_flags
        self.is_finalized = False
    def add_arg(self, argtype, argname = None, default = None, direction_flag = 1):
        self.argtypes.append(argtype)
        self.argnames.append(argname)
        self.defaults.append(default)
        self.direction_flags.append(direction_flag)
    def finalize(self):
        self._make_doc()
        self.prototype  = CFUNCTYPE(self.restype, *self.argtypes)
        self.paramflags = zip(self.direction_flags,self.argnames,self.defaults)
        self.is_finalized = True
    def bind(self, library):
        if not self.is_finalized:
            self.finalize()
        func = self.prototype((self.name, library), tuple(self.paramflags))
        #copy attributes to the function object        
        func.__doc__  = self.__doc__
        func.argnames = self.argnames
        func.defaults = self.defaults
        func.direction_flags = self.direction_flags        
        func.errcheck = self.errcheck
        #load the function into the library namespace
        lib_ns = library.__dict__
        lib_ns[self.name] = func
        return func
    def _make_doc(self):
        doc = []
        if not self.doc_header is None:
            doc.append(self.doc_header)
            doc.append("")
        doc.append("Arguments:")
        for argtype, argname, default in zip(self.argtypes, self.argnames, self.defaults):
            if argname is None:
                argname = "NoName"
                doc.append("-    %s\t%s" % (argtype,argname))
            else:            
                doc.append("-    %s\t%s = %s" % (argtype,argname,default))
        self.__doc__ = "\n".join(doc) 
        
###############################################################################
#/******************************************************************************
# *** NI-DAQBasemx Function Declarations ***************************************
# ******************************************************************************/

#/******************************************************/
#/***         Task Configuration/Control             ***/
#/******************************************************/

# int32 DllExport __CFUNC   DAQmxBaseLoadTask            (const char taskName[], TaskHandle *taskHandle);
_proto01 = CFUNC_Prototype("DAQmxBaseLoadTask")
_proto01.add_arg(c_char_p, "taskName")
_proto01.add_arg(POINTER(TaskHandle), "taskHandle")
_proto01.finalize()
# int32 DllExport __CFUNC   DAQmxBaseCreateTask          (const char taskName[], TaskHandle *taskHandle);
_proto02 = CFUNC_Prototype("DAQmxBaseCreateTask")
_proto02.add_arg(c_char_p, "taskName")
_proto02.add_arg(TaskHandle, "taskHandle")
_proto02.finalize()
# int32 DllExport __CFUNC   DAQmxBaseStartTask           (TaskHandle taskHandle);
_proto03 = CFUNC_Prototype("DAQmxBaseStartTask")
_proto03.add_arg(TaskHandle, "taskHandle")
_proto03.finalize()
# int32 DllExport __CFUNC   DAQmxBaseStopTask            (TaskHandle taskHandle);
_proto04 = CFUNC_Prototype("DAQmxBaseStopTask")
_proto04.add_arg(TaskHandle, "taskHandle")
_proto04.finalize()
# int32 DllExport __CFUNC   DAQmxBaseClearTask           (TaskHandle taskHandle);
_proto05 = CFUNC_Prototype("DAQmxBaseClearTask")
_proto05.add_arg(TaskHandle, "taskHandle")
_proto05.finalize()
# int32 DllExport __CFUNC   DAQmxBaseIsTaskDone          (TaskHandle taskHandle, bool32 *isTaskDone);
_proto06 = CFUNC_Prototype("DAQmxBaseIsTaskDone")
_proto06.add_arg(TaskHandle, "taskHandle")
_proto06.add_arg(POINTER(bool32), "isTaskDone")
_proto06.finalize()

#/******************************************************/
#/***        Channel Configuration/Creation          ***/
#/******************************************************/

# int32 DllExport __CFUNC   DAQmxBaseCreateAIVoltageChan          (TaskHandle taskHandle, const char physicalChannel[], const char nameToAssignToChannel[], int32 terminalConfig, float64 minVal, float64 maxVal, int32 units, const char customScaleName[]);
_proto07 = CFUNC_Prototype("DAQmxBaseCreateAIVoltageChan")
_proto07.add_arg(TaskHandle, "taskHandle")
_proto07.add_arg(c_char_p  , "physicalChannel")
_proto07.add_arg(c_char_p  , "nameToAssignToChannel")
_proto07.add_arg(int32     , "terminalConfig")
_proto07.add_arg(float64   , "minVal")
_proto07.add_arg(float64   , "maxVal")
_proto07.add_arg(int32     , "units")
_proto07.add_arg(c_char_p  , "customScaleName")
_proto07.finalize()
# int32 DllExport __CFUNC   DAQmxBaseCreateAIThrmcplChan          (TaskHandle taskHandle, const char physicalChannel[], const char nameToAssignToChannel[], float64 minVal, float64 maxVal, int32 units, int32 thermocoupleType, int32 cjcSource, float64 cjcVal, const char cjcChannel[]);
_proto08 = CFUNC_Prototype("DAQmxBaseCreateAIThrmcplChan")
_proto08.add_arg(TaskHandle, "taskHandle")
_proto08.add_arg(c_char_p  , "physicalChannel")
_proto08.add_arg(c_char_p  , "nameToAssignToChannel")
_proto08.add_arg(float64   , "minVal")
_proto08.add_arg(float64   , "maxVal")
_proto08.add_arg(int32     , "units")
_proto08.add_arg(int32     , "thermocoupleType")
_proto08.add_arg(int32     , "cjcSource")
_proto08.add_arg(float64   , "cjcVal")
_proto08.add_arg(c_char_p  , "cjcChannel")
_proto08.finalize()
# int32 DllExport __CFUNC   DAQmxBaseCreateAOVoltageChan          (TaskHandle taskHandle, const char physicalChannel[], const char nameToAssignToChannel[], float64 minVal, float64 maxVal, int32 units, const char customScaleName[]);
_proto09 = CFUNC_Prototype("DAQmxBaseCreateAOVoltageChan")
_proto09.add_arg(TaskHandle, "taskHandle")
_proto09.add_arg(c_char_p  , "lines")
_proto09.add_arg(c_char_p  , "nameToAssignToLines")
_proto09.add_arg(int32     , "lineGrouping")
_proto09.finalize()
# int32 DllExport __CFUNC   DAQmxBaseCreateDIChan                 (TaskHandle taskHandle, const char lines[], const char nameToAssignToLines[], int32 lineGrouping);
_proto10 = CFUNC_Prototype("DAQmxBaseCreateDIChan")
_proto10.add_arg(TaskHandle, "taskHandle")
_proto10.add_arg(c_char_p  , "physicalChannel")
_proto10.add_arg(c_char_p  , "nameToAssignToChannel")
_proto10.add_arg(float64   , "minVal")
_proto10.add_arg(float64   , "maxVal")
_proto10.add_arg(int32     , "units")
_proto10.add_arg(c_char_p  , "customScaleName")
_proto10.finalize()
# int32 DllExport __CFUNC   DAQmxBaseCreateDOChan                 (TaskHandle taskHandle, const char lines[], const char nameToAssignToLines[], int32 lineGrouping);
_proto11 = CFUNC_Prototype("DAQmxBaseCreateDOChan")
_proto11.add_arg(TaskHandle, "taskHandle")
_proto11.add_arg(c_char_p  , "physicalChannel")
_proto11.add_arg(c_char_p  , "nameToAssignToChannel")
_proto11.add_arg(float64   , "minVal")
_proto11.add_arg(float64   , "maxVal")
_proto11.add_arg(int32     , "units")
_proto11.add_arg(c_char_p  , "customScaleName")
_proto11.finalize()
# int32 DllExport __CFUNC   DAQmxBaseCreateCIPeriodChan           (TaskHandle taskHandle, const char counter[], const char nameToAssignToChannel[], float64 minVal, float64 maxVal, int32 units, int32 edge, int32 measMethod, float64 measTime, uInt32 divisor, const char customScaleName[]);
_proto12 = CFUNC_Prototype("DAQmxBaseCreateCIPeriodChan")
_proto12.add_arg(TaskHandle, "taskHandle")
_proto12.add_arg(c_char_p  , "counter")
_proto12.add_arg(c_char_p  , "nameToAssignToChannel")
_proto12.add_arg(float64   , "minVal")
_proto12.add_arg(float64   , "maxVal")
_proto12.add_arg(int32     , "units")
_proto12.add_arg(int32     , "edge")
_proto12.add_arg(int32     , "measMethod")
_proto12.add_arg(uInt32    , "divisor")
_proto12.add_arg(c_char_p  , "customScaleName")
_proto12.finalize()
# int32 DllExport __CFUNC   DAQmxBaseCreateCICountEdgesChan       (TaskHandle taskHandle, const char counter[], const char nameToAssignToChannel[], int32 edge, uInt32 initialCount, int32 countDirection);
_proto13 = CFUNC_Prototype("DAQmxBaseCreateCICountEdgesChan")
_proto13.add_arg(TaskHandle, "taskHandle")
_proto13.add_arg(c_char_p  , "counter")
_proto13.add_arg(c_char_p  , "nameToAssignToChannel")
_proto13.add_arg(int32     , "edge")
_proto13.add_arg(uInt32    , "initialCount")
_proto13.add_arg(int32     , "countDirection")
_proto13.finalize()
# int32 DllExport __CFUNC   DAQmxBaseCreateCIPulseWidthChan       (TaskHandle taskHandle, const char counter[], const char nameToAssignToChannel[], float64 minVal, float64 maxVal, int32 units, int32 startingEdge, const char customScaleName[]);
_proto14 = CFUNC_Prototype("DAQmxBaseCreateCIPulseWidthChan")
_proto14.add_arg(TaskHandle, "taskHandle")
_proto14.add_arg(c_char_p  , "counter")
_proto14.add_arg(c_char_p  , "nameToAssignToChannel")
_proto14.add_arg(float64   , "minVal")
_proto14.add_arg(float64   , "maxVal")
_proto14.add_arg(int32     , "units")
_proto14.add_arg(int32     , "startingEdge")
_proto14.add_arg(c_char_p  , "customScaleName")
_proto14.finalize()
# int32 DllExport __CFUNC   DAQmxBaseCreateCILinEncoderChan       (TaskHandle taskHandle, const char counter[], const char nameToAssignToChannel[], int32 decodingType, bool32 ZidxEnable, float64 ZidxVal, int32 ZidxPhase, int32 units, float64 distPerPulse, float64 initialPos, const char customScaleName[]);
_proto15 = CFUNC_Prototype("DAQmxBaseCreateCILinEncoderChan")
_proto15.add_arg(TaskHandle, "taskHandle")
_proto15.add_arg(c_char_p  , "counter")
_proto15.add_arg(c_char_p  , "nameToAssignToChannel")
_proto15.add_arg(int32     , "decodingType")
_proto15.add_arg(bool32    , "ZidxEnable")
_proto15.add_arg(float64   , "ZidxVal")
_proto15.add_arg(int32     , "ZidxPhase")
_proto15.add_arg(int32     , "units")
_proto15.add_arg(float64   , "distPerPulse")
_proto15.add_arg(float64   , "initialPos")
_proto15.add_arg(c_char_p  , "customScaleName")
_proto15.finalize()
# int32 DllExport __CFUNC   DAQmxBaseCreateCIAngEncoderChan       (TaskHandle taskHandle, const char counter[], const char nameToAssignToChannel[], int32 decodingType, bool32 ZidxEnable, float64 ZidxVal, int32 ZidxPhase, int32 units, uInt32 pulsesPerRev, float64 initialAngle, const char customScaleName[]);
_proto16 = CFUNC_Prototype("DAQmxBaseCreateCIAngEncoderChan")
_proto16.add_arg(TaskHandle, "taskHandle")
_proto16.add_arg(c_char_p  , "counter")
_proto16.add_arg(c_char_p  , "nameToAssignToChannel")
_proto16.add_arg(int32     , "decodingType")
_proto16.add_arg(bool32    , "ZidxEnable")
_proto16.add_arg(float64   , "ZidxVal")
_proto16.add_arg(int32     , "ZidxPhase")
_proto16.add_arg(int32     , "units")
_proto16.add_arg(float64   , "distPerPulse")
_proto16.add_arg(float64   , "initialPos")
_proto16.add_arg(c_char_p  , "customScaleName")
_proto16.add_arg(uInt32    , "pulsesPerRev")
_proto16.add_arg(float64   , "initialAngle")
_proto16.add_arg(c_char_p  , "customScaleName")
_proto16.finalize()
# int32 DllExport __CFUNC   DAQmxBaseCreateCOPulseChanFreq        (TaskHandle taskHandle, const char counter[], const char nameToAssignToChannel[], int32 units, int32 idleState, float64 initialDelay, float64 freq, float64 dutyCycle);
_proto17 = CFUNC_Prototype("DAQmxBaseCreateCOPulseChanFreq")
_proto17.add_arg(TaskHandle, "taskHandle")
_proto17.add_arg(c_char_p  , "counter")
_proto17.add_arg(c_char_p  , "nameToAssignToChannel")
_proto17.add_arg(int32     , "units")
_proto17.add_arg(int32     , "idleState")
_proto17.add_arg(float64   , "initialDelay")
_proto17.add_arg(float64   , "freq")
_proto17.add_arg(float64   , "dutyCycle")
_proto17.finalize()
# int32 DllExport __CFUNC_C DAQmxBaseGetChanAttribute             (TaskHandle taskHandle, const char channel[], int32 attribute, void *value);
_proto18 = CFUNC_Prototype("DAQmxBaseGetChanAttribute")
_proto18.add_arg(TaskHandle, "taskHandle")
_proto18.add_arg(c_char_p  , "channel")
_proto18.add_arg(int32     , "attribute")
_proto18.add_arg(c_void_p  , "value")
_proto18.finalize()
# int32 DllExport __CFUNC_C DAQmxBaseSetChanAttribute             (TaskHandle taskHandle, const char channel[], int32 attribute, int32 value);
_proto19 = CFUNC_Prototype("DAQmxBaseSetChanAttribute")
_proto19.add_arg(TaskHandle, "taskHandle")
_proto19.add_arg(c_char_p  , "channel")
_proto19.add_arg(int32     , "attribute")
_proto19.add_arg(int32     , "value")
_proto19.finalize()

#/******************************************************/
#/***                    Timing                      ***/
#/******************************************************/

#// (Analog/Counter Timing)
# int32 DllExport __CFUNC   DAQmxBaseCfgSampClkTiming          (TaskHandle taskHandle, const char source[], float64 rate, int32 activeEdge, int32 sampleMode, uInt64 sampsPerChan);
_proto20 = CFUNC_Prototype("DAQmxBaseCfgSampClkTiming")
_proto20.add_arg(TaskHandle, "taskHandle")
_proto20.add_arg(c_char_p  , "source")
_proto20.add_arg(float64   , "rate")
_proto20.add_arg(int32     , "activeEdge")
_proto20.add_arg(int32     , "sampleMode")
_proto20.add_arg(uInt64    , "sampsPerChan")
_proto20.finalize()
#// (Counter Timing)
# int32 DllExport __CFUNC   DAQmxBaseCfgImplicitTiming         (TaskHandle taskHandle, int32 sampleMode, uInt64 sampsPerChan);
_proto21 = CFUNC_Prototype("DAQmxBaseCfgImplicitTiming")
_proto21.add_arg(TaskHandle, "taskHandle")
_proto21.add_arg(int32     , "sampleMode")
_proto21.add_arg(uInt64    , "sampsPerChan")
_proto21.finalize()

#/******************************************************/
#/***                  Triggering                    ***/
#/******************************************************/

# int32 DllExport __CFUNC   DAQmxBaseDisableStartTrig      (TaskHandle taskHandle);
_proto22 = CFUNC_Prototype("DAQmxBaseDisableStartTrig")
_proto22.add_arg(TaskHandle, "taskHandle")
_proto22.finalize()
# int32 DllExport __CFUNC   DAQmxBaseCfgDigEdgeStartTrig   (TaskHandle taskHandle, const char triggerSource[], int32 triggerEdge);
_proto23 = CFUNC_Prototype("DAQmxBaseCfgDigEdgeStartTrig")
_proto23.add_arg(TaskHandle, "taskHandle")
_proto23.add_arg(c_char_p  , "triggerSource")
_proto23.add_arg(int32     , "triggerEdge")
_proto23.finalize()
# int32 DllExport __CFUNC   DAQmxBaseCfgAnlgEdgeStartTrig  (TaskHandle taskHandle, const char triggerSource[], int32 triggerSlope, float64 triggerLevel);
_proto24 = CFUNC_Prototype("DAQmxBaseCfgAnlgEdgeStartTrig")
_proto24.add_arg(TaskHandle, "taskHandle")
_proto24.add_arg(c_char_p  , "triggerSource")
_proto24.add_arg(int32     , "triggerSlope")
_proto24.add_arg(float64   , "triggerLevel")
_proto24.finalize()
# int32 DllExport __CFUNC   DAQmxBaseDisableRefTrig        (TaskHandle taskHandle);
_proto25 = CFUNC_Prototype("DAQmxBaseDisableRefTrig")
_proto25.add_arg(TaskHandle, "taskHandle")
_proto25.finalize()
# int32 DllExport __CFUNC   DAQmxBaseCfgDigEdgeRefTrig     (TaskHandle taskHandle, const char triggerSource[], int32 triggerEdge, uInt32 pretriggerSamples);
_proto26 = CFUNC_Prototype("DAQmxBaseCfgDigEdgeRefTrig")
_proto26.add_arg(TaskHandle, "taskHandle")
_proto26.add_arg(c_char_p  , "triggerSource")
_proto26.add_arg(int32     , "triggerEdge")
_proto26.add_arg(uInt32    , "pretriggerSamples")
_proto26.finalize()
# int32 DllExport __CFUNC   DAQmxBaseCfgAnlgEdgeRefTrig    (TaskHandle taskHandle, const char triggerSource[], int32 triggerSlope, float64 triggerLevel, uInt32 pretriggerSamples);
_proto27 = CFUNC_Prototype("DAQmxBaseCfgAnlgEdgeRefTrig")
_proto27.add_arg(TaskHandle, "taskHandle")
_proto27.add_arg(c_char_p  , "triggerSource")
_proto27.add_arg(int32     , "triggerSlope")
_proto27.add_arg(float64   , "triggerLevel")
_proto27.add_arg(uInt32    , "pretriggerSamples")
_proto27.finalize()

#/******************************************************/
#/***                 Read Data                      ***/
#/******************************************************/

# int32 DllExport __CFUNC   DAQmxBaseReadAnalogF64         (TaskHandle taskHandle, int32 numSampsPerChan, float64 timeout, bool32 fillMode, float64 readArray[], uInt32 arraySizeInSamps, int32 *sampsPerChanRead, bool32 *reserved);
_proto28 = CFUNC_Prototype("DAQmxBaseReadAnalogF64")
_proto28.add_arg(TaskHandle      , "taskHandle")
_proto28.add_arg(int32           , "numSampsPerChan")
_proto28.add_arg(float64         , "timeout")
_proto28.add_arg(bool32          , "fillMode")
_proto28.add_arg(POINTER(float64), "readArray")
_proto28.add_arg(uInt32          , "arraySizeInSamps")
_proto28.add_arg(POINTER(int32)  , "sampsPerChanRead")
_proto28.add_arg(POINTER(bool32) , "reserved")
_proto28.finalize()
# int32 DllExport __CFUNC   DAQmxBaseReadBinaryI16         (TaskHandle taskHandle, int32 numSampsPerChan, float64 timeout, bool32 fillMode, int16 readArray[], uInt32 arraySizeInSamps, int32 *sampsPerChanRead, bool32 *reserved);
_proto29 = CFUNC_Prototype("DAQmxBaseReadBinaryI16")
_proto29.add_arg(TaskHandle      , "taskHandle")
_proto29.add_arg(int32           , "numSampsPerChan")
_proto29.add_arg(float64         , "timeout")
_proto29.add_arg(bool32          , "fillMode")
_proto29.add_arg(POINTER(int16)  , "readArray")
_proto29.add_arg(uInt32          , "arraySizeInSamps")
_proto29.add_arg(POINTER(int32)  , "sampsPerChanRead")
_proto29.add_arg(POINTER(bool32) , "reserved")
_proto29.finalize()
# int32 DllExport __CFUNC   DAQmxBaseReadBinaryI32         (TaskHandle taskHandle, int32 numSampsPerChan, float64 timeout, bool32 fillMode, int32 readArray[], uInt32 arraySizeInSamps, int32 *sampsPerChanRead, bool32 *reserved);
_proto30 = CFUNC_Prototype("DAQmxBaseReadBinaryI32")
_proto30.add_arg(TaskHandle      , "taskHandle")
_proto30.add_arg(int32           , "numSampsPerChan")
_proto30.add_arg(float64         , "timeout")
_proto30.add_arg(bool32          , "fillMode")
_proto30.add_arg(POINTER(int32)  , "readArray")
_proto30.add_arg(uInt32          , "arraySizeInSamps")
_proto30.add_arg(POINTER(int32)  , "sampsPerChanRead")
_proto30.add_arg(POINTER(bool32) , "reserved")
_proto30.finalize()
# int32 DllExport __CFUNC   DAQmxBaseReadDigitalU8         (TaskHandle taskHandle, int32 numSampsPerChan, float64 timeout, bool32 fillMode, uInt8 readArray[], uInt32 arraySizeInSamps, int32 *sampsPerChanRead, bool32 *reserved);
_proto31 = CFUNC_Prototype("DAQmxBaseReadDigitalU8")
_proto31.add_arg(TaskHandle      , "taskHandle")
_proto31.add_arg(int32           , "numSampsPerChan")
_proto31.add_arg(float64         , "timeout")
_proto31.add_arg(bool32          , "fillMode")
_proto31.add_arg(POINTER(uInt8)  , "readArray")
_proto31.add_arg(uInt32          , "arraySizeInSamps")
_proto31.add_arg(POINTER(int32)  , "sampsPerChanRead")
_proto31.add_arg(POINTER(bool32) , "reserved")
_proto31.finalize()
# int32 DllExport __CFUNC   DAQmxBaseReadDigitalU32        (TaskHandle taskHandle, int32 numSampsPerChan, float64 timeout, bool32 fillMode, uInt32 readArray[], uInt32 arraySizeInSamps, int32 *sampsPerChanRead, bool32 *reserved);
_proto32 = CFUNC_Prototype("DAQmxBaseReadDigitalU32")
_proto32.add_arg(TaskHandle      , "taskHandle")
_proto32.add_arg(int32           , "numSampsPerChan")
_proto32.add_arg(float64         , "timeout")
_proto32.add_arg(bool32          , "fillMode")
_proto32.add_arg(POINTER(uInt32) , "readArray")
_proto32.add_arg(uInt32          , "arraySizeInSamps")
_proto32.add_arg(POINTER(int32)  , "sampsPerChanRead")
_proto32.add_arg(POINTER(bool32) , "reserved")
_proto32.finalize()
# int32 DllExport __CFUNC   DAQmxBaseReadDigitalScalarU32  (TaskHandle taskHandle, float64 timeout, uInt32 *value, bool32 *reserved);
_proto33 = CFUNC_Prototype("DAQmxBaseReadDigitalScalarU32")
_proto33.add_arg(TaskHandle      , "taskHandle")
_proto33.add_arg(float64         , "timeout")
_proto33.add_arg(POINTER(uInt32) , "value")
_proto33.add_arg(POINTER(bool32) , "reserved")
_proto33.finalize()
# int32 DllExport __CFUNC   DAQmxBaseReadCounterF64        (TaskHandle taskHandle, int32 numSampsPerChan, float64 timeout, float64 readArray[], uInt32 arraySizeInSamps, int32 *sampsPerChanRead, bool32 *reserved);
_proto34 = CFUNC_Prototype("DAQmxBaseReadCounterF64")
_proto34.add_arg(TaskHandle       , "taskHandle")
_proto34.add_arg(int32            , "numSampsPerChan")
_proto34.add_arg(float64          , "timeout")
_proto34.add_arg(POINTER(float64) , "readArray")
_proto34.add_arg(uInt32           , "arraySizeInSamps")
_proto34.add_arg(POINTER(int32)   , "sampsPerChanRead")
_proto34.add_arg(POINTER(bool32)  , "reserved")
_proto34.finalize()
# int32 DllExport __CFUNC   DAQmxBaseReadCounterU32        (TaskHandle taskHandle, int32 numSampsPerChan, float64 timeout, uInt32 readArray[], uInt32 arraySizeInSamps, int32 *sampsPerChanRead, bool32 *reserved);
_proto35 = CFUNC_Prototype("DAQmxBaseReadCounterU32")
_proto35.add_arg(TaskHandle      , "taskHandle")
_proto35.add_arg(int32           , "numSampsPerChan")
_proto35.add_arg(float64         , "timeout")
_proto35.add_arg(bool32          , "fillMode")
_proto35.add_arg(POINTER(uInt32) , "readArray")
_proto35.add_arg(uInt32          , "arraySizeInSamps")
_proto35.add_arg(POINTER(int32)  , "sampsPerChanRead")
_proto35.add_arg(POINTER(bool32) , "reserved")
_proto35.finalize()
# int32 DllExport __CFUNC   DAQmxBaseReadCounterScalarF64  (TaskHandle taskHandle, float64 timeout, float64 *value, bool32 *reserved);
_proto36 = CFUNC_Prototype("DAQmxBaseReadCounterScalarF64")
_proto36.add_arg(TaskHandle      , "taskHandle")
_proto36.add_arg(float64         , "timeout")
_proto36.add_arg(POINTER(float64), "value")
_proto36.add_arg(POINTER(bool32) , "reserved")
_proto36.finalize()
# int32 DllExport __CFUNC   DAQmxBaseReadCounterScalarU32  (TaskHandle taskHandle, float64 timeout, uInt32 *value, bool32 *reserved);
_proto37 = CFUNC_Prototype("DAQmxBaseReadCounterScalarU32")
_proto37.add_arg(TaskHandle      , "taskHandle")
_proto37.add_arg(float64         , "timeout")
_proto37.add_arg(POINTER(uInt32) , "value")
_proto37.add_arg(POINTER(bool32) , "reserved")
_proto37.finalize()
# int32 DllExport __CFUNC_C DAQmxBaseGetReadAttribute      (TaskHandle taskHandle, int32 attribute, void *value);
_proto38 = CFUNC_Prototype("DAQmxBaseGetReadAttribute")
_proto38.add_arg(TaskHandle      , "taskHandle")
_proto38.add_arg(int32           , "attribute")
_proto38.add_arg(c_void_p        , "value")
_proto38.finalize()

#/******************************************************/
#/***                 Write Data                     ***/
#/******************************************************/

# int32 DllExport __CFUNC   DAQmxBaseWriteAnalogF64          (TaskHandle taskHandle, int32 numSampsPerChan, bool32 autoStart, float64 timeout, bool32 dataLayout, float64 writeArray[], int32 *sampsPerChanWritten, bool32 *reserved);
_proto39 = CFUNC_Prototype("DAQmxBaseWriteAnalogF64")
_proto39.add_arg(TaskHandle       , "taskHandle")
_proto39.add_arg(int32            , "numSampsPerChan")
_proto39.add_arg(bool32           , "autoStart")
_proto39.add_arg(float64          , "timeout")
_proto39.add_arg(bool32           , "dataLayout")
_proto39.add_arg(POINTER(float64) , "writeArray")
_proto39.add_arg(POINTER(int32)   , "sampsPerChanWritten")
_proto39.add_arg(POINTER(bool32)  , "reserved")
_proto39.finalize()
# int32 DllExport __CFUNC   DAQmxBaseWriteDigitalU8          (TaskHandle taskHandle, int32 numSampsPerChan, bool32 autoStart, float64 timeout, bool32 dataLayout, uInt8 writeArray[], int32 *sampsPerChanWritten, bool32 *reserved);
_proto40 = CFUNC_Prototype("DAQmxBaseWriteDigitalU8")
_proto40.add_arg(TaskHandle       , "taskHandle")
_proto40.add_arg(int32            , "numSampsPerChan")
_proto40.add_arg(bool32           , "autoStart")
_proto40.add_arg(float64          , "timeout")
_proto40.add_arg(bool32           , "dataLayout")
_proto40.add_arg(POINTER(uInt8)   , "writeArray")
_proto40.add_arg(POINTER(int32)   , "sampsPerChanWritten")
_proto40.add_arg(POINTER(bool32)  , "reserved")
_proto40.finalize()
# int32 DllExport __CFUNC   DAQmxBaseWriteDigitalU32         (TaskHandle taskHandle, int32 numSampsPerChan, bool32 autoStart, float64 timeout, bool32 dataLayout, uInt32 writeArray[], int32 *sampsPerChanWritten, bool32 *reserved);
_proto41 = CFUNC_Prototype("DAQmxBaseWriteDigitalU32")
_proto41.add_arg(TaskHandle       , "taskHandle")
_proto41.add_arg(int32            , "numSampsPerChan")
_proto41.add_arg(bool32           , "autoStart")
_proto41.add_arg(float64          , "timeout")
_proto41.add_arg(bool32           , "dataLayout")
_proto41.add_arg(POINTER(uInt32)  , "writeArray")
_proto41.add_arg(POINTER(int32)   , "sampsPerChanWritten")
_proto41.add_arg(POINTER(bool32)  , "reserved")
_proto41.finalize()
# int32 DllExport __CFUNC   DAQmxBaseWriteDigitalScalarU32   (TaskHandle taskHandle, bool32 autoStart, float64 timeout, uInt32 value, bool32 *reserved);
_proto42 = CFUNC_Prototype("DAQmxBaseWriteDigitalScalarU32")
_proto42.add_arg(TaskHandle       , "taskHandle")
_proto42.add_arg(bool32           , "autoStart")
_proto42.add_arg(float64          , "timeout")
_proto42.add_arg(uInt32           , "value")
_proto42.add_arg(POINTER(bool32)  , "reserved")
_proto42.finalize()
# int32 DllExport __CFUNC_C DAQmxBaseGetWriteAttribute       (TaskHandle taskHandle, int32 attribute, void *value);
_proto43 = CFUNC_Prototype("DAQmxBaseGetWriteAttribute")
_proto43.add_arg(TaskHandle       , "taskHandle")
_proto43.add_arg(int32            , "attribute")
_proto43.add_arg(c_void_p         , "value")
_proto43.finalize()
# int32 DllExport __CFUNC_C DAQmxBaseSetWriteAttribute       (TaskHandle taskHandle, int32 attribute, int32 value);
_proto44 = CFUNC_Prototype("DAQmxBaseSetWriteAttribute")
_proto44.add_arg(TaskHandle       , "taskHandle")
_proto44.add_arg(int32            , "attribute")
_proto44.add_arg(int32            , "value")
_proto44.finalize()

#/******************************************************/
#/***               Events & Signals                 ***/
#/******************************************************/
#// Terminology:  For hardware, "signals" comprise "clocks," "triggers," and (output) "events".
#// Software signals or events are not presently supported.

# int32 DllExport __CFUNC   DAQmxBaseExportSignal                (TaskHandle taskHandle, int32 signalID, const char outputTerminal[]);
_proto45 = CFUNC_Prototype("DAQmxBaseExportSignal")
_proto45.add_arg(TaskHandle       , "taskHandle")
_proto45.add_arg(int32            , "signalID")
_proto45.add_arg(c_char_p         , "outputTerminal")
_proto45.finalize()

#/******************************************************/
#/***             Buffer Configurations              ***/
#/******************************************************/

# int32 DllExport __CFUNC   DAQmxBaseCfgInputBuffer   (TaskHandle taskHandle, uInt32 numSampsPerChan);
_proto46 = CFUNC_Prototype("DAQmxBaseCfgInputBuffer")
_proto46.add_arg(TaskHandle       , "taskHandle")
_proto46.add_arg(uInt32           , "numSampsPerChan")
_proto46.finalize()

#/******************************************************/
#/***                Device Control                  ***/
#/******************************************************/

# int32 DllExport __CFUNC   DAQmxBaseResetDevice              (const char deviceName[]);
_proto47 = CFUNC_Prototype("DAQmxBaseResetDevice")
_proto47.add_arg(c_char_p         , "deviceName")
_proto47.finalize()

#/******************************************************/
#/***                 Error Handling                 ***/
#/******************************************************/

#int32 DllExport __CFUNC    DAQmxBaseGetExtendedErrorInfo (char errorString[], uInt32 bufferSize);
_proto48 = CFUNC_Prototype("DAQmxBaseGetExtendedErrorInfo")
_proto48.add_arg(c_char_p         , "errorString")
_proto48.add_arg(uInt32           , "bufferSize")
_proto48.finalize()

#------------------------------------------------------------------------------
# collect the prototypes defined above
LIB_FUNC_PROTOTYPES = [obj for name,obj in locals().items() if name.startswith("_proto")]
LIB_FUNC_PROTOTYPES.sort()
###############################################################################
# module level functions

def load_dll(lib_path = None, wrap = True):
    if lib_path is None:
        plat = platform.platform()
        if plat.startswith('Linux'):
            lib_path = DEFAULT_LINUX_LIB_PATH
        elif plat.startswith('Windows'):
            lib_path = DEFAULT_WINDOWS_LIB_PATH
    cdll = ctypes.CDLL(lib_path) # load the DLL driver
    if wrap:    
        #wrap function calls with error checker as save old names as __unwrapped_<func>
        for proto in LIB_FUNC_PROTOTYPES:
            func = proto.bind(cdll)
    return cdll
###############################################################################
# TEST CODE
###############################################################################
if __name__ == "__main__":
    from ctypes import *    
    cdll = load_dll(wrap = True)
    
