###############################################################################
#Dependencies
#standard python
import time
#Automat framework provided
from automat.core.hwcontrol.devices.instruments import Model
#yes_o2ab provided
from yes_o2ab.drivers.devices.DAQ.national_instruments import nidaqmxbase 
###############################################################################
#Module constants

## initialize variables
#taskHandle = TaskHandle(0)
#min = float64(-10.0)
#max = float64(10.0)
#timeout = float64(10.0)
#bufferSize = uInt32(10)
#pointsToRead = bufferSize
#pointsRead = uInt32()
#sampleRate = float64(10000.0)
#samplesPerChan = uInt64(2000)
#chan = ctypes.create_string_buffer('Dev1/ai0')
#clockSource = ctypes.create_string_buffer('OnboardClock')


#data = numpy.zeros((1000,),dtype=numpy.float64)


## Create Task and Voltage Channel and Configure Sample Clock
#def SetupTask():
#    CHK(nidaq.DAQmxCreateTask("",ctypes.byref(taskHandle)))
#    CHK(nidaq.DAQmxCreateAIVoltageChan(taskHandle,chan,"",DAQmx_Val_RSE,min,max,
#        DAQmx_Val_Volts,None))
#    CHK(nidaq.DAQmxCfgSampClkTiming(taskHandle,clockSource,sampleRate,
#        DAQmx_Val_Rising,DAQmx_Val_ContSamps,samplesPerChan))
#    CHK(nidaq.DAQmxCfgInputBuffer(taskHandle,200000))

##Start Task
#def StartTask():
#    CHK(nidaq.DAQmxStartTask (taskHandle))

##Read Samples
#def ReadSamples(points):
#    bufferSize = uInt32(points)
#    pointsToRead = bufferSize
#    data = numpy.zeros((points,),dtype=numpy.float64)
#    CHK(nidaq.DAQmxReadAnalogF64(taskHandle,pointsToRead,timeout,
#            DAQmx_Val_GroupByScanNumber,data.ctypes.data,
#            uInt32(2*bufferSize.value),ctypes.byref(pointsRead),None))

#    print "Acquired %d pointx(s)"%(pointsRead.value)

#    return data

#def StopAndClearTask():
#    if taskHandle.value != 0:
#        nidaq.DAQmxStopTask(taskHandle)
#        nidaq.DAQmxClearTask(taskHandle)


###############################################################################
class Interface(Model):
    def __init__(self,**kwargs):
        self._cdll = nidaqmxbase.load_dll()
    def identify(self):
        pass
    def shutdown(self):
        #do nothing        
        pass
      

#------------------------------------------------------------------------------
# INTERFACE CONFIGURATOR         
def get_interface(**kwargs):
    return Interface(**kwargs)    
###############################################################################
# TEST CODE
###############################################################################
if __name__ == "__main__":
    usb_daq = Interface()

