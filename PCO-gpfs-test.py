#!/dls_sw/prod/tools/RHEL6-x86_64/defaults/bin/dls-python
from pkg_resources import require
require('cothread') #http://cothread.readthedocs.io/en/latest/catools.html
from cothread.catools import *
import datetime
import time

numImages = 10000
filePath = "G:/i13/data/2016/cm14467-3/tmp"
fileName = "filetest"

# Configure CAM
caput("BL13I-EA-DET-02:CAM:AcquireTime", 0.005, wait=True, timeout=5)
caput("BL13I-EA-DET-02:CAM:AcquirePeriod", 0.006, wait=True, timeout=5)
caput("BL13I-EA-DET-02:CAM:PIX_RATE", 1, wait=True, timeout=5)
caput("BL13I-EA-DET-02:CAM:NumImages", numImages, wait=True, timeout=5)
caput("BL13I-EA-DET-02:CAM:ImageMode", 1, wait=True, timeout=5)

# Configure HDF
caput("BL13I-EA-DET-02:HDF5:FilePath", filePath, wait=True, timeout=5, datatype=DBR_CHAR_STR)
caput("BL13I-EA-DET-02:HDF5:FileName", fileName, wait=True, timeout=5, datatype=DBR_CHAR_STR)
#caput("BL13I-EA-DET-02:HDF5:BlockingCallbacks", 1, wait=True, timeout=5)
caput("BL13I-EA-DET-02:HDF5:EnableCallbacks", 1, wait=True, timeout=5)
caput("BL13I-EA-DET-02:HDF5:FileWriteMode", 2, wait=True, timeout=5)
caput("BL13I-EA-DET-02:HDF5:LazyOpen", 1, wait=True, timeout=5)
caput("BL13I-EA-DET-02:HDF5:AutoIncrement", 1, wait=True, timeout=5)
caput("BL13I-EA-DET-02:HDF5:NumCapture", numImages, wait=True, timeout=5)

#get the value (loop until the counter is 'done')
#count = caget("BL12I-EA-DET-01:SCALER.S18", datatype=DBR_LONG )

