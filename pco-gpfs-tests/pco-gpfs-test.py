#!/dls_sw/prod/tools/RHEL6-x86_64/defaults/bin/dls-python
from pkg_resources import require
#require('cothread') #http://cothread.readthedocs.io/en/latest/catools.html
#from cothread.catools import *
from pcoSim import *
import datetime, time, csv, sys


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
        """Print debug output"""
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
        
        # Read the Capture status from the HDF plugin
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
            self.debugPrint("Starting acquisition {0} of {1} at {2}".format(testIndex+1, self.parameters["numFiles"], timestamp) )
            self.startOneAcquisition()
            
            # Wait for it to complete using a not very clever timer
            time.sleep(0.1)
            timerIncrement = 1 #second
            timer = 0
            timeOut = 600 # 10 minutes
            
            while (self.inProgress()):
                time.sleep(timerIncrement)
                
                # Keep track of roughly how long we've waited
                timer = timer + timerIncrement
                # Drop out if we think it's stuck
                if (timer > timeOut):
                    sys.exit(self.debugPrint("Exiting because test timed out"))
            
            # Get the numbers we want to record as results for this test and make a list
            results = [timestamp,testIndex,self.parameters["exposureTime"],self.parameters["acquirePeriod"],self.parameters["numImagesPerFile"]]
            # including the Performance PVs from the PCO 
            for pv in self.pvsToRecord:
                results.append(caget(pv, datatype=DBR_LONG))
            
            # Print the results to the console so you can see them if you're watching the tests go
            for key, value in zip(self.csvColumns, results):
                self.debugPrint("{0} = {1}".format(key, value))
            
            # Write results to a new row in the CSV file
            self.results.writerow(results)
            
            # Check for problems in the IOC
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
        self.pvsToRecord = self.pvNames["performance"] + [self.pvNames["filenmaeRbv"], self.pvNames["numCapturedRbv"], self.pvNames["writeTime"], self.pvNames["writeSpeed"], self.pvNames["writeStatus"], self.pvNames["writeMessage"], self.pvNames["droppedHdf"]]
        self.csvColumns = ["Timestamp","ID","Exposure time /s","Acquire period /s","Number of acquisitions"] + self.pvsToRecord
        # Open CSV file to store results
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
        outputFilename = "output/pco_test_results_{0}.csv".format(timestamp)
        try:
            self.csvfile = open(outputFilename, 'wb')
        except:
            self.debugPrint("Couldn't open file {0}".format(outputFilename))
            raise
        else:
            
            # Write header for CSV file
            self.results = csv.writer(self.csvfile, delimiter=',')
            self.results.writerow(["PCO Test Results {0}".format(timestamp)])
            
            self.results.writerow(self.csvColumns)
        
#get the value (loop until the counter is 'done')
#count = caget("BL12I-EA-DET-01:SCALER.S18", datatype=DBR_LONG )

if __name__ == "__main__":
    
    # Define test parameters
    testParams = {
        "numImagesPerFile":   1000,
        "numFiles":           5,
        "exposureTime":       0.005,
        "acquirePeriod":      0.005,
        "filePath":           "G:/i13/data/2016/cm14467-3/tmp",
        "fileName":           "filetest",
        "pvPrefix":           "TDQ39642-EA-TEST-02",
        "camPrefix":          ":CAM",
        "hdfPrefix":          ":HDF5" }
    
    # Define PV names
    testParams["pvNames"] = {
        "acquire"       : testParams["pvPrefix"] + testParams["camPrefix"] + ":Acquire",
        "captureRbv"    : testParams["pvPrefix"] + testParams["hdfPrefix"] + ":Capture_RBV",
        "numCapturedRbv": testParams["pvPrefix"] + testParams["hdfPrefix"] + ":NumCaptured_RBV",
        "filenmaeRbv"   : testParams["pvPrefix"] + testParams["hdfPrefix"] + ":FullFileName_RBV",
        "writeTime"     : testParams["pvPrefix"] + testParams["hdfPrefix"] + ":RunTime",
        "writeSpeed"    : testParams["pvPrefix"] + testParams["hdfPrefix"] + ":IOSpeed",
        "writeStatus"   : testParams["pvPrefix"] + testParams["hdfPrefix"] + ":WriteStatus",
        "writeMessage"  : testParams["pvPrefix"] + testParams["hdfPrefix"] + ":WriteMessage",
        "droppedHdf"    : testParams["pvPrefix"] + testParams["hdfPrefix"] + ":DroppedArrays_RBV",
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
        
        t.debugPrint("Tests finished")