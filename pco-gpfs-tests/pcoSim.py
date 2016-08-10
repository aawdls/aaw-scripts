# Simulated PCO camera IOC - very simple
import threading
import time

def debugPrint(message):
    debugPrefix = "[simulator] "
    print debugPrefix, message

debugPrint("## Running with Simulator ##")

# Dummy cothread variables
DBR_CHAR_STR    = 0
DBR_LONG        = 1

# Other variables
listOfThreads = []
busy = False

class PcoSimulator():
    """Very simple simulator of a PCO camera IOC"""
    
    def caput(self, pvName, newValue, **kwargs):
        """Dummy caput function"""
        debugPrint("caput: {0} = {1}".format(pvName, newValue))
        
        # Specific actions:
        # Requested start of acquisition
        if (pvName == self.pvNames["acquire"] and newValue == 1):
            self.startAcquiring(self.parameters["acquirePeriod"], self.parameters["numImagesPerFile"])
            
    def caget(self, pvName, datatype=DBR_LONG):
        """ Dummy caget function """
        
        if (pvName == self.pvNames["captureRbv"]):
            # Return 1 while I'm pretending to acquire and write
            # otherwise return 0
            returnValue =  1 if (self.busy == True) else 0
        else:
            # Return zero if requested PV unknown
            returnValue = -1
            
        debugPrint("caget: {0} = {1}".format(pvName, returnValue))
        return returnValue
    
    def acquisitionThread(self, acquisitionTime, numAcquisitions):
        debugPrint("Started acquisition thread")
        self.busy = True
        for i in range(numAcquisitions):
            time.sleep(acquisitionTime)
        debugPrint("Acquisition thread finished")
        self.busy = False
        return
        
    def startAcquiring(self, acquireTime, numAcquisitions):
        t = threading.Thread(target=self.acquisitionThread, args=(acquireTime, numAcquisitions))
        listOfThreads.append(t)
        t.start()
        
    def isAcquiring(self):
        return self.busy
        
    def __init__(self, testParams):
        self.parameters = testParams
        # Handy variables
        self.pvPrefix = self.parameters["pvPrefix"]
        self.camPrefix = self.parameters["camPrefix"]
        self.hdfPrefix = self.parameters["hdfPrefix"]
        
        # Internal state
        self.busy = False
        self.writeSpeed = 0
        
        # Key PV names
        self.pvNames = self.parameters["pvNames"]

    