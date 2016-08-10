#!/dls_sw/prod/tools/RHEL6-x86_64/defaults/bin/dls-python
from pkg_resources import require
#require('cothread') #http://cothread.readthedocs.io/en/latest/catools.html
#from cothread.catools import *
from pcoSim import *
import datetime
import time
import csv


class pcoHdfTest():
    """Sets up and runs a repeatable test of writing files from a PCO camera IOC.
    """
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        if (self.csvfile):
            self.csvfile.close()
        return
    
    def debugPrint(self, message):
        debugPrefix = "[pco test] "
        print debugPrefix, message
    
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

    def startOneAcquisition(self):
        """
        Start a single file acquisition
        """
        
        self.debugPrint("Start acquisition")
        caput(self.pvNames["acquire"],        1,      wait=True, timeout=5)
        
    def inProgress(self):
        """
        Returns true if acquisition is in progress or file is open
        """
        
        if (caget(self.pvNames["captureRbv"], datatype=DBR_LONG) == 1):
            return True
        else:
            return False
        
        
    def getStats(self):
        """
        Grab the diagnostics we need 
        """
        # Write time, write speed, dropped frames, successful frames, total faults, write errors
        
    def runTests(self):
        """
        Run the tests in a loop
        """
        for testIndex in range(0, self.parameters["numFiles"]):
            
            # Start the acquisition
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
            debugPrint("Starting acquisition {0} of {1} at {2}".format(testIndex+1, self.parameters["numFiles"], timestamp) )
            self.startOneAcquisition()
            
            # Wait for it to complete
            time.sleep(0.1)
            while (self.inProgress()):
                time.sleep(1)
                # Drop out if we think it's stuck
                #if (self.timedOut()):
                    #break
            
            self.results.writerow([timestamp,testIndex,self.parameters["acquirePeriod"],self.parameters["acquirePeriod"],self.parameters["numImagesPerFile"]])
            
            # Check for problems
            #if (self.problem()):
                # Handle error
                # If recoverable, recover, and continue with the next acquisition
                #break
                
            # Get diagnostics for this acquisition
            self.getStats()

    def __init__(self, testParams):
        """
        Set up a test; wait for user input to run
        """
        self.parameters = testParams
        
        # Handy variables
        self.pvPrefix = self.parameters["pvPrefix"]
        self.camPrefix = self.parameters["camPrefix"]
        self.hdfPrefix = self.parameters["hdfPrefix"]
        
        # Key PV names
        self.pvNames = self.parameters["pvNames"]

        # Open CSV file to store results
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
        outputFilename = "output/pco_test_results_{0}.csv".format(timestamp)
        try:
            self.csvfile = open(outputFilename, 'wb')
        except:
            debugPrint("Couldn't open file {0}".format(outputFilename))
            raise
        else:
            self.results = csv.writer(self.csvfile, delimiter=',')
            self.results.writerow(["PCO Test Results {0}".format(timestamp)])
            self.results.writerow(["Timestamp","ID","Acquire period /s","Exposure time /s","Number of acquisitions"])
        
#get the value (loop until the counter is 'done')
#count = caget("BL12I-EA-DET-01:SCALER.S18", datatype=DBR_LONG )

if __name__ == "__main__":
    
    # Define test parameters
    testParams = {
        "numImagesPerFile":   100,
        "numFiles":           5,
        "exposureTime":       0.005,
        "acquirePeriod":      0.006,
        "filePath":           "G:/i13/data/2016/cm14467-3/tmp",
        "fileName":           "filetest",
        "pvPrefix":           "TDQ39642-EA-TEST-02",
        "camPrefix":          ":CAM",
        "hdfPrefix":          ":HDF5" }
    
    # Define PV names
    testParams["pvNames"] = {
        "acquire"      : testParams["pvPrefix"] + testParams["camPrefix"] + ":Acquire",
        "captureRbv"   : testParams["pvPrefix"] + testParams["hdfPrefix"] + ":Capture_RBV",
        "writeSpeed"   : testParams["pvPrefix"] + testParams["hdfPrefix"] + ":IOSpeed",
        "writeStatus"  : testParams["pvPrefix"] + testParams["hdfPrefix"] + ":WriteStatus",
        "writeMessage" : testParams["pvPrefix"] + testParams["hdfPrefix"]+ ":WriteMessage"}

    # Create simulator object with these parameters
    pcoSimulator = PcoSimulator(testParams)
    
    def caput(*args, **kwargs):
        """Wrapper for simulator's caput to make it look like the real thing"""
        return pcoSimulator.caput(*args, **kwargs)
        
    def caget(*args, **kwargs):
        """Wrapper for simulator's caput to make it look like the real thing"""
        return pcoSimulator.caget(*args, **kwargs)
        
    # Create test object
    with pcoHdfTest(testParams) as t:
    
        # Configure the camera IOC
        t.setupIoc()
        
        # Wait for user to confirm start
        throwAway = raw_input("Ready to run tests. Hit return to start:")
        
        # Begin tests
        t.runTests()

    debugPrint("Tests finished")