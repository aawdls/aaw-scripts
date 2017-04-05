#!/dls_sw/prod/tools/RHEL6-x86_64/defaults/bin/dls-python
from pkg_resources import require
require('cothread') #http://cothread.readthedocs.io/en/latest/catools.html
from cothread.catools import *
from cothread import Sleep
#from pcoSim import *
import datetime, time, csv, sys, os, numpy

class pcoVariableExposureTest():
    """Sets up and runs a test of varying the exposure from a PCO detector during single file write.
    """
    def debugPrint(self, message):
        """Print debug output"""
        debugPrefix = "[pco test] "
        print debugPrefix, message
        
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        return
        
    def setupIoc(self):
        """
        Set up the IOC with parameters for the test
        """
        
        self.debugPrint("Configure camera IOC...")
        
        # Set up the IOC
        # Configure CAM plugin
        self.debugPrint("(1/2) configure CAM plugin")
        caput(self.pvPrefix + self.camPrefix + ":AcquireTime",        self.parameters["exposureTime"],      wait=True, timeout=5)
        caput(self.pvPrefix + self.camPrefix + ":AcquirePeriod",      self.parameters["acquirePeriod"],      wait=True, timeout=5)
        caput(self.pvPrefix + self.camPrefix + ":PIX_RATE",           1,          wait=True, timeout=5)
        caput(self.pvPrefix + self.camPrefix + ":NumImages",          self.parameters["numImagesPerFile"],  wait=True, timeout=5)
        caput(self.pvPrefix + self.camPrefix + ":ImageMode",          1,          wait=True, timeout=5) # Multiple
        caput(self.pvPrefix + self.camPrefix + ":TriggerMode",        0,          wait=True, timeout=5) # Multiple

        # Configure HDF plugin
        self.debugPrint("(2/2) configure HDF plugin")
        caput(self.pvPrefix + self.hdfPrefix + ":FilePath",          self.parameters["filePath"],    wait=True, timeout=5, datatype=DBR_CHAR_STR)
        caput(self.pvPrefix + self.hdfPrefix + ":FileName",          self.parameters["fileName"],    wait=True, timeout=5, datatype=DBR_CHAR_STR)
        caput(self.pvPrefix + self.hdfPrefix + ":BlockingCallbacks",  0,          wait=True, timeout=5)
        caput(self.pvPrefix + self.hdfPrefix + ":EnableCallbacks",   1,           wait=True, timeout=5)
        caput(self.pvPrefix + self.hdfPrefix + ":FileWriteMode",     2,           wait=True, timeout=5)
        caput(self.pvPrefix + self.hdfPrefix + ":LazyOpen",          1,           wait=True, timeout=5)
        caput(self.pvPrefix + self.hdfPrefix + ":AutoIncrement",     1,           wait=True, timeout=5)
        caput(self.pvPrefix + self.hdfPrefix + ":NumCapture",        self.parameters["numImagesPerFile"],   wait=True, timeout=5)
        caput(self.pvPrefix + self.hdfPrefix + ":DroppedArrays",     0,           wait=True, timeout=5)

    def startCapture(self):
        self.debugPrint("Start file capture")
        startCapture = caget(self.pvNames["capture"], datatype=DBR_LONG)
        caput(self.pvNames["capture"],        1,      wait=False, timeout=0)
        
    def stopCapture(self):
        self.debugPrint("Stop file capture")
        startCapture = caget(self.pvNames["capture"], datatype=DBR_LONG)
        caput(self.pvNames["capture"],        0,      wait=False, timeout=0)
    
    def setExposure(self, exposureTime, acquirePeriod):
        self.debugPrint("Set exposure = " + str(exposureTime) + "s, acquire period = " + str(acquirePeriod) + "s")
        caput(self.pvPrefix + self.camPrefix + ":AcquireTime",        exposureTime,      wait=True, timeout=5)
        caput(self.pvPrefix + self.camPrefix + ":AcquirePeriod",      acquirePeriod,      wait=True, timeout=5)
    
    def startAcquire(self):
        """
        Start a single acquisition
        """
        startCapture = caget(self.pvNames["capture"], datatype=DBR_LONG)
        startAcquire = caget(self.pvNames["acquire"], datatype=DBR_LONG)   
        self.debugPrint("CAPTURE: " + str(startCapture) + ", ACQUIRE: " + str(startAcquire))
        
        self.debugPrint("Start acquisition")
        caput(self.pvNames["acquire"],        1,      wait=False, timeout=0)
        
        startCapture = caget(self.pvNames["capture"], datatype=DBR_LONG)
        startAcquire = caget(self.pvNames["acquire"], datatype=DBR_LONG)   
        self.debugPrint("CAPTURE: " + str(startCapture) + ", ACQUIRE: " + str(startAcquire))
        
    def stopAcquire(self):
        """
        Stop the acquisition
        """
        startCapture = caget(self.pvNames["capture"], datatype=DBR_LONG)
        startAcquire = caget(self.pvNames["acquire"], datatype=DBR_LONG)   
        self.debugPrint("CAPTURE: " + str(startCapture) + ", ACQUIRE: " + str(startAcquire))
        
        self.debugPrint("Stop acquisition")
        caput(self.pvNames["acquire"],        0,      wait=False, timeout=0)
        
        startCapture = caget(self.pvNames["capture"], datatype=DBR_LONG)
        startAcquire = caget(self.pvNames["acquire"], datatype=DBR_LONG)   
        self.debugPrint("CAPTURE: " + str(startCapture) + ", ACQUIRE: " + str(startAcquire))
        
    def inProgress(self):
        """
        Returns true if acquisition is in progress or file is open
        """
        
        # Read the Capture status from the HDF plugin
        #isCapturing = caget(self.pvNames["captureRbv"], datatype=DBR_LONG)
        #self.debugPrint("{0} = {1}".format( self.pvNames["captureRbv"], isCapturing))
        hdfQueue = caget(self.pvNames["hdfQueue"], datatype=DBR_LONG)
        camAcquiring = caget(self.pvNames["acquire"], datatype=DBR_LONG)
        if (hdfQueue == 0 and camAcquiring == 0):
            return False
        else:
            return True
            
    def __init__(self, testParams, testName):
        """
        Set up a test; wait for user input to run
        """
        self.parameters = testParams
        
        # Handy variables
        self.pvPrefix = self.parameters["pvPrefix"]
        self.camPrefix = self.parameters["camPrefix"]
        self.hdfPrefix = self.parameters["hdfPrefix"]
        self.fileNames = []
        self.hdfQueue = []
        
        # Key PV names
        self.pvNames = self.parameters["pvNames"]
        
if __name__ == "__main__":
    
    # Define test parameters
    # I13, netApp
    testParamsI13N = {
        "numImagesPerFile":   30000,
        "numFiles":           1,
        "exposureTime":       0.005,
        "acquirePeriod":      0.0051,
        "filePath":           "D:\\i13\\data\\2017\\cm16786-1\\tmp\\stress-test",
        "fileName":           "filetest",
        "pvPrefix":           "BL13I-EA-DET-01",
        "camPrefix":          ":CAM",
        "hdfPrefix":          ":HDF5" }
    # I13, GPFS
    testParamsI13G = {
        "numImagesPerFile":   11400,
        "numFiles":           1,
        "exposureTime":       0.005,
        "acquirePeriod":      0.0051,
        "filePath":           "T:\\i13\\data\\2017\\cm16786-2\\tmp\\pco-variable-exposure-test",
        "fileName":           "filetest",
        "pvPrefix":           "BL13I-EA-DET-01",
        "camPrefix":          ":CAM",
        "hdfPrefix":          ":HDF5" }
 
    
    # Select parameters for different tests
#    if sys.argv[1] == "I13N":
#        testParams = testParamsI13N
#    elif sys.argv[1] == "I13G":
    testParams = testParamsI13G 
    
    # Define PV names
    testParams["pvNames"] = {
        "acquire"       : testParams["pvPrefix"] + testParams["camPrefix"] + ":Acquire", 
        "capture"       : testParams["pvPrefix"] + testParams["hdfPrefix"] + ":Capture",
        "captureRbv"    : testParams["pvPrefix"] + testParams["hdfPrefix"] + ":Capture_RBV",
        "numCapturedRbv": testParams["pvPrefix"] + testParams["hdfPrefix"] + ":NumCaptured_RBV",
        "filenameRbv"   : testParams["pvPrefix"] + testParams["hdfPrefix"] + ":FullFileName_RBV",
        "writeTime"     : testParams["pvPrefix"] + testParams["hdfPrefix"] + ":RunTime",
        "writeSpeed"    : testParams["pvPrefix"] + testParams["hdfPrefix"] + ":IOSpeed",
        "writeStatus"   : testParams["pvPrefix"] + testParams["hdfPrefix"] + ":WriteStatus",
        "writeMessage"  : testParams["pvPrefix"] + testParams["hdfPrefix"] + ":WriteMessage",
        "droppedHdf"    : testParams["pvPrefix"] + testParams["hdfPrefix"] + ":DroppedArrays_RBV",
        "hdfQueue"      : testParams["pvPrefix"] + testParams["hdfPrefix"] + ":QueueUse",
        "performance"  : [ testParams["pvPrefix"] + testParams["camPrefix"] + ":PERF:CNT:GOODFRAME_RBV",
                            testParams["pvPrefix"] + testParams["camPrefix"] + ":PERF:CNT:MISSING_RBV",
                            testParams["pvPrefix"] + testParams["camPrefix"] + ":PERF:CNT:OUTOFARRAYS_RBV",
                            testParams["pvPrefix"] + testParams["camPrefix"] + ":PERF:CNT:INVALID_RBV",
                            testParams["pvPrefix"] + testParams["camPrefix"] + ":PERF:CNT:FRAMESTATUS_RBV",
                            testParams["pvPrefix"] + testParams["camPrefix"] + ":PERF:CNT:WAITFAULT_RBV",
                            testParams["pvPrefix"] + testParams["camPrefix"] + ":PERF:CNT:DRIVERERROR_RBV",
                            testParams["pvPrefix"] + testParams["camPrefix"] + ":PERF:CNT:CAPTUREERROR_RBV",
                            testParams["pvPrefix"] + testParams["camPrefix"] + ":PERF:CNT:POLLGETFRAME_RBV",
                            testParams["pvPrefix"] + testParams["camPrefix"] + ":PERF:CNT:FAULT_RBV"
                        ]
        }
        
   # Create test object
    with pcoVariableExposureTest(testParams, "I13G") as t:
    
        # Configure the camera IOC
        t.setupIoc()
        
        # Wait for user to confirm start
        throwAway = raw_input("Ready to run tests. Hit return to start:")
        
        # Begin tests
        t.startCapture()
        
        Sleep (1)
        
        t.debugPrint("10s at 100fps = 1000 frames")
        t.setExposure(0.01, 0.01)
        t.startAcquire()
        Sleep(10)
        t.stopAcquire()
        
        t.debugPrint("50s at 40fps = 2000 frames")
        t.setExposure(0.025, 0.025)
        t.startAcquire()
        Sleep(50)
        t.stopAcquire()
        
        t.debugPrint("4 minutes at 20 fps = 240s * 20fps = 8400 frames")
        t.setExposure(0.05, 0.05)
        t.startAcquire()
        Sleep(240)
        t.stopAcquire()
        
        # Total: 11400 frames
        
        while (t.inProgress == True):
            t.debugPrint("Waiting for HDF queue to empty")
            Sleep(1)

        
        t.debugPrint("Tests finished")
