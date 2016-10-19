#!/dls_sw/prod/tools/RHEL6-x86_64/defaults/bin/dls-python
from pkg_resources import require
require('cothread') #http://cothread.readthedocs.io/en/latest/catools.html
#require('dls_environment')
from cothread.catools import *
from cothread import Sleep
#from dls_environment.options import OptionParser
#from optparse import OptionGroup
import datetime, time, csv, sys, os

class iocRegressionTest():
    """
    Read an archiver ".grp" file or a list of PVs.
    With the existing version of the ioc, cagets each PV and writes its value into a file
    Then when the IOC has been updated, cagets each PV again and compares it with the file
    """
    
    def __init__(self, pvListPath, valueFilePath):
        
        self.pvListPath = pvListPath
        self.valueFilePath = valueFilePath
    
    def readPvList(self):
        
        self.pvListFile = open(self.pvListPath, "r")
        rows = csv.reader(self.pvListFile, delimiter=" ")
        
        print "List of PVs to read:"
        self.pvList = []
        for row in rows:
            self.pvList.append(row[0])
            print row[0]
        
    def writeValueFile(self):
        
        self.valueFile =  open(self.valueFilePath, "w")
        writer = csv.writer(self.valueFile, delimiter=' ')
        
        print "\nGetting PV values and writing a file..."
        
        for pv in self.pvList:
            try:
                val = caget(pv,timeout=0.5)
            except:
                writer.writerow([pv, "___Timed out___"])
                print "Couldn't caget PV", pv, "!"
            else:
                try:
                    f = float(val)
                    valStr = "{:.1E}".format(f)
                except:
                    valStr = str(val)
                
                writer.writerow([pv, valStr])

    """  
    def compareValueFile(self):
        
        self.valueFile =  open(self.valueFilePath, "w")
        rows = csv.reader(self.valueFile, delimiter=" ")
        print "Comparing values"
        for row in rows:
            pv = row[0]
            try:
                val = caget(pv)
                writer.writerow([pv, val])
            except:
                writer.writerow([pv, "___Timed out___"])
                print ("Couldn't caget PV", pv)
    """
        
        
if __name__=="__main__":
    
    usage = "Save a list of PV values which can be diffed before and after IOC update:\nioc-regression-test.py <PV list file> <output value file>"
    #\nCompare current values with those form a file:\nioc-regression-test.py --compare <comparioson value file>"
    
    if (len(sys.argv) == 3):
        
        a = iocRegressionTest(sys.argv[1], sys.argv[2])
        a.readPvList()
        a.writeValueFile()
    
#    elif (sys.argv[1] == "--compare" && len(sys.argv) == 3):
#        
#        a = iocRegressionTest(sys.argv[2], sys.argv[3])
#        a.compareValueFile()
        
    else: 
    
        print usage
        sys.exit()
    

        