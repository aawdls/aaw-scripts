#!/dls_sw/prod/tools/RHEL6-x86_64/defaults/bin/dls-python
from pkg_resources import require
require('cothread') #http://cothread.readthedocs.io/en/latest/catools.html
from cothread.catools import *
from cothread import Sleep
#from pcoSim import *
import datetime, time, csv, sys, os, sched
from pco_gpfs_test import pcoHdfTest

if __name__=="__main__":
    
    # Define test parameters
    # I13, netApp
    testParamsI13N = {
        "numImagesPerFile":   30000,
        "numFiles":           1,
        "exposureTime":       0.005,
        "acquirePeriod":      0.0051,
        "filePath":           "D:\\i13\\data\\2016\\cm14467-4\\raw\\stress-test",
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
        "filePath":           "D:\\i12\\data\\2016\\cm14465-4\\raw\\stress-test",
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
        "filePath":           "T:\\i13\\data\\2016\\cm14467-4\\raw\\stress-test",
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
        "filePath":           "T:\\i12\\data\\2016\\cm14465-4\\raw\\stress-test",
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
        "filePath":           "T:\\i12\\data\\2016\\cm14465-4\\raw\\stress-test",
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

    #testParams = testParamsI12N
    #testParams = testParamsI13G
    #testParams = testParamsI12G
    
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
        
    # Print the time
    def elapsed_time():
        total_secs = (time.time() - begin)
        hours = int(round(total_secs / 60 / 60))
        mins_left_over = int(round((total_secs % (60 * 60)) / 60))
        secs_left_over = int(round((total_secs % 60)))
        
        return "{0}h {1}m {2}s".format(hours, mins_left_over, secs_left_over)
        
    # This function runs a test - we'll pass it to the scheduler
    def runATest ():

        # Create test object
        with pcoHdfTest(testParams, sys.argv[1]) as t:
        
            t.debugPrint("About to run test scheduled at "+elapsed_time())
            # Configure the camera IOC
            t.setupIoc()
            
            # Wait for user to confirm start
    #        throwAway = raw_input("Ready to run tests. Hit return to start:")
            
            # Begin tests
            t.runTests()
            
            #check the written files
            #t.checkFiles()
            
    #        t.debugPrint("Tests finished")
            t.debugPrint("Completed test at "+elapsed_time()+", waiting until it's time to start the next one.")

    #runATest()

    # Set up the scheduler
    begin = time.time()
        
    s = sched.scheduler(time.time, time.sleep)

    minute = 60
    half_hour = 30 * minute
    hour = 2 * half_hour
    test_duration = int(round(24 * hour))
    #test_duration = int(round(10 * minute))
    test_interval = int(round(half_hour))
    #test_interval = int(round(2 * minute))

    for delay in xrange (0, test_duration, test_interval):
        print "Schedule delay of", delay, "s"
        s.enter(delay, 1, runATest, ())

    #s.enter(5, 1, print_time, ())
    s.run()
    print time.time()
