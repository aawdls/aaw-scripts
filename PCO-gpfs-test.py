#!/dls_sw/prod/tools/RHEL6-x86_64/defaults/bin/dls-python
from pkg_resources import require
require('cothread') #http://cothread.readthedocs.io/en/latest/catools.html
from cothread.catools import *
import datetime
import time



class pcoHdfTest():
    
    # Test paramters
    numImages       = 1000
    numAcquisitions = 1000
    exposureTime    = 0.005
    acquirePeriod   = 0.006
    visit           = "cm14467-3"
    filePath        = "G:/i13/data/2016/{0}/tmp".format(visit)
    fileName        = "filetest"
    pvPrefix        = "BL13I-EA-DET-02"
    camPrefix       = ":CAM"
    hdfPrefix       = ":HDF5"
    
    def setupIoc(self):
        """
        Set up the IOC with parameters for the test
        """

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

    def __init__(self):
        """
        Set up a test; wait for user input to run
        """
        setupIoc()
        
#get the value (loop until the counter is 'done')
#count = caget("BL12I-EA-DET-01:SCALER.S18", datatype=DBR_LONG )

if __name__ == "__main__":
    
    t = pcoHdfTest()