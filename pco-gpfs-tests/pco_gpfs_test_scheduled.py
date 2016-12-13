#!/dls_sw/prod/tools/RHEL6-x86_64/defaults/bin/dls-python
from pkg_resources import require
require('cothread') #http://cothread.readthedocs.io/en/latest/catools.html
from cothread.catools import *
from cothread import Sleep
#from pcoSim import *
import datetime, time, csv, sys, os, sched, math, numpy
from pco_gpfs_test import pcoHdfTest

"""
    Schedule a PCO GPFS/NetApp file writing test at a regular interval over a specified duration on I12 or I13.
    Requires pco_gpfs_test.py which supplies the GPFS test class.
    This script will remain running until the last scheduled test is completed.
    
    Usage: ./pco_gpfs_test_scheduled.py [I13N | I13G | I12N \ I12G]
    where N denotes write to NetApp, G denotes write to GPFS
    
    Modify the below variables test_duration and test_interval beforehand to set when the tests are run.
"""

if __name__=="__main__":
    
    # Define test parameters
    # I13, netApp
    testParamsI13N = {
        "numImagesPerFile":   30000,
        "numFiles":           1,
        "exposureTime":       0.005,
        "acquirePeriod":      0.0051,
        "filePath":           "D:\\i13\\data\\2016\\cm14467-4\\tmp\\stress-test",
        "fileName":           "filetest",
        "pvPrefix":           "BL13I-EA-DET-01",
        "camPrefix":          ":CAM",
        "hdfPrefix":          ":HDF5" }
    # I12, NetApp
    testParamsI12N = {
        "numImagesPerFile":   30000,
        "numFiles":           1,
        "exposureTime":       0.005,
        "acquirePeriod":      0.0051,
        "filePath":           "D:\\i12\\data\\2016\\cm14465-4\\tmp\\stress-test",
        "fileName":           "filetest",
        "pvPrefix":           "BL12I-EA-DET-02",
        "camPrefix":          ":CAM",
        "hdfPrefix":          ":HDF" }
    # I13, GPFS
    testParamsI13G = {
        "numImagesPerFile":   30000,
        "numFiles":           1,
        "exposureTime":       0.005,
        "acquirePeriod":      0.0051,
        "filePath":           "T:\\i13\\data\\2016\\cm14467-4\\tmp\\stress-test",
        "fileName":           "filetest",
        "pvPrefix":           "BL13I-EA-DET-01",
        "camPrefix":          ":CAM",
        "hdfPrefix":          ":HDF5" }
    # I12, GPFS
    testParamsI12G = {
        "numImagesPerFile":   30000,
        "numFiles":           1,
        "exposureTime":       0.005,
        "acquirePeriod":      0.0051,
        "filePath":           "T:\\i12\\data\\2016\\cm14465-4\\tmp\\stress-test",
        "fileName":           "filetest",
        "pvPrefix":           "BL12I-EA-DET-02",
        "camPrefix":          ":CAM",
        "hdfPrefix":          ":HDF" }
    # I12, GPFS
    testParamsI12G2 = {
        "numImagesPerFile":   30000,
        "numFiles":           1,
        "exposureTime":       0.005,
        "acquirePeriod":      0.0051,
        "filePath":           "T:\\i12\\data\\2016\\cm14465-4\\tmp\\stress-test",
        "fileName":           "filetest",
        "pvPrefix":           "BL12I-EA-DET-12",
        "camPrefix":          ":CAM",
        "hdfPrefix":          ":HDF" }
    
    # Select parameters for different tests
    if sys.argv[1] == "I13N":
        testParams = testParamsI13N
    elif sys.argv[1] == "I13G":
        testParams = testParamsI13G 
    elif sys.argv[1] == "I12N":
        testParams = testParamsI12N 
    elif sys.argv[1] == "I12G":
        testParams = testParamsI12G      
    elif sys.argv[1] == "I12G2":
        testParams = testParamsI12G2      

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
        
    # Format the elapsed time
    def elapsed_time():
        total_secs = (time.time() - begin)
        hours = int(math.floor(total_secs / 60 / 60))
        mins_left_over = int(math.floor((total_secs % (60 * 60)) / 60))
        secs_left_over = int(math.floor((total_secs % 60)))
        
        return "{0}h_{1}m_{2}s".format(hours, mins_left_over, secs_left_over)
        
    # This function runs a test - we'll pass it to the scheduler
    # to be executed at the right time
    def runATest ():
        
        # Create test object
        with pcoHdfTest(testParams, testName) as t:
        
            # Logging info
            startTime = elapsed_time()
            t.debugPrint("About to run test scheduled at "+startTime)
            
            # Configure the camera IOC
            t.setupIoc()
            
            # Begin this test
            t.runTests()
            
            # Prepare HDF queue data file
            hdfQueueData = {startTime: t.getHdfQueueUse()}
            
            # Create the file to store the hdf queue data
            hdfQueueFileName = "hdfQueue_{0}".format(startTime)
            hdfQueueFilePath = os.path.join(hdfQueueDir, hdfQueueFileName)
            hdfQueueFile = open(hdfQueueFilePath, "w")
            numpy.save(hdfQueueFile, hdfQueueData)
            hdfQueueFile.close()
            
            # Logging info
            t.debugPrint("Completed test at "+elapsed_time()+", waiting until it's time to start the next one.")

    # Prepare for test
    testName = sys.argv[1]
    
    # Set up the scheduler
    begin = time.time()
    s = sched.scheduler(time.time, time.sleep)

    # Define times
    minute = 60
    half_hour = 30 * minute
    hour = 2 * half_hour
    
    # Run tests over 24 hours
    test_duration = int(round(23 * hour))
    #test_duration = int(round(10 * minute))
    # Run a test every half hour
    test_interval = int(round(half_hour))
    #test_interval = int(round(2 * minute))

    # Prepare schedule of tests 
    for delay in xrange (0, test_duration, test_interval):
        print "Schedule delay of", delay, "s"
        s.enter(delay, 1, runATest, ())

    # Create a new directory to store queue fill status data
    begints = time.gmtime(begin)
    timestamp = time.strftime("%Y-%m-%d_%H%M%S", begints)
    hdfQueueDir = os.path.join("output", "hdf_queue_data_{0}_{1}".format(testName, timestamp))
    if not os.path.exists(hdfQueueDir):
        os.makedirs(hdfQueueDir)

    # Start the schedule
    s.run()
