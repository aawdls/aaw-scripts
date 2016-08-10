# Simulated PCO camera IOC - very simple
import threading
import time

def debugPrint(message):
    debugPrefix = "[simulator] "
    print debugPrefix, message

debugPrint("## Running with Simulator ##")

# Dummy cothread variables
DBR_CHAR_STR = 0

# Other variables
listOfThreads = []
busy = False

class PcoSimulator():
    
    def caput(self, pvName, newValue, **kwargs):
        """Dummy caput function"""
        debugPrint("caput: {0} = {1}".format(pvName, newValue))
    
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
        
    def __init__(self):
        self.busy = False
        

pcoSimulator = PcoSimulator()

# Dummy caputs
def caput(*args, **kwargs):
    """Dummy caput function"""
    pcoSimulator.caput(*args, **kwargs)
    
def startAcquiring( acquireTime, numAcquisitions):
    pcoSimulator.startAcquiring( acquireTime, numAcquisitions)
    