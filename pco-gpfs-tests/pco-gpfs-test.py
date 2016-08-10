#!/dls_sw/prod/tools/RHEL6-x86_64/defaults/bin/dls-python
from pkg_resources import require
require('cothread') #http://cothread.readthedocs.io/en/latest/catools.html
from cothread.catools import *
import datetime
import time



class pcoHdfTest()
"""Sets up and runs a repeatable test of writing files from a PCO camera IOC.
"""
    
    def setupIoc(self):
        """
        Set up the IOC with parameters for the test
        """
        
        # Handy local variables
        pvPrefix = self.parameters["pvPrefix"]
        camPrefix = self.parameters["camPrefix"]
        hdfPrefix = self.parameters["hdfPrefix"]
        
        # Set up the IOC
        # Configure CAM plugin
        caput(pvPrefix + camPrefix + ":AcquireTime",        exposureTime,      wait=True, timeout=5)
        caput(pvPrefix + camPrefix + ":AcquirePeriod",      acquirePeriod,      wait=True, timeout=5)
        caput(pvPrefix + camPrefix + ":PIX_RATE",           1,          wait=True, timeout=5)
        caput(pvPrefix + camPrefix + ":NumImages",          numImages,  wait=True, timeout=5)
        caput(pvPrefix + camPrefix + ":ImageMode",          1,          wait=True, timeout=5) # Multiple

        # Configure HDF plugin
        caput(pvPrefix + hdfPrefix + ":FilePath",          filePath,    wait=True, timeout=5, datatype=DBR_CHAR_STR)
        caput(pvPrefix + hdfPrefix + ":FileName",          fileName,    wait=True, timeout=5, datatype=DBR_CHAR_STR)
        caput(pvPrefix + hdfPrefix + ":BlockingCallbacks",  0,          wait=True, timeout=5)
        caput(pvPrefix + hdfPrefix + ":EnableCallbacks",   1,           wait=True, timeout=5)
        caput(pvPrefix + hdfPrefix + ":FileWriteMode",     2,           wait=True, timeout=5)
        caput(pvPrefix + hdfPrefix + ":LazyOpen",          1,           wait=True, timeout=5)
        caput(pvPrefix + hdfPrefix + ":AutoIncrement",     1,           wait=True, timeout=5)
        caput(pvPrefix + hdfPrefix + ":NumCapture",        numImages,   wait=True, timeout=5)

    def startOneAcquisition(self):
        """
        Start a single file acquisition
        """
        caput(pvPrefix + camPrefix + ":Acquire",        1,      wait=True, timeout=5)
        
    def inProgress(self):
        """
        Returns true if acquisition is in progress or file is open
        """
        
    def getStats(self):
        """
        Grab the diagnostics we need 
        """
        # Write time, write speed, dropped frames, successful frames, total faults, write errors
        
    def runTests(self):
        """
        Run the tests in a loop
        """
        for (testIndex in range(0, parameters["numFiles"])):
            
            # Start the acquisition
            self.startOneAcquisition()
            
            # Wait for it to complete
            while (self.inProgress()):
                time.sleep(1)
                # Drop out if we think it's stuck
                if (self.timedOut()):
                    break
            
            # Check for problems
            if (self.problem()):
                # Handle error
                # If recoverable, recover, and continue with the next acquisition
                break
                
            # Get diagnostics for this acquisition
            self.getStats()

    def __init__(self, testParams):
        """
        Set up a test; wait for user input to run
        """
        self.parameters = testParams
        self.setupIoc()
        
#get the value (loop until the counter is 'done')
#count = caget("BL12I-EA-DET-01:SCALER.S18", datatype=DBR_LONG )

if __name__ == "__main__":
    
    # Define test parameters
    testParams = {
        numImagesPerFile:   1000,
        numFiles:           1000,
        exposureTime:       0.005,
        acquirePeriod:      0.006,
        filePath:           "G:/i13/data/2016/cm14467-3/tmp",
        fileName:           "filetest",
        pvPrefix:           "BL13I-EA-DET-02",
        camPrefix:          ":CAM",
        hdfPrefix:          ":HDF5" }
    
    # Begin the test
    t = pcoHdfTest(testParams)