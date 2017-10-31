#!/dls_sw/prod/tools/RHEL6-x86_64/defaults/bin/dls-python
from pkg_resources import require
require('cothread') #http://cothread.readthedocs.io/en/latest/catools.html
from cothread.catools import *
from cothread import Sleep
#from pcoSim import *
import datetime, time, csv, sys, os, logging

class Result():
    def __init__(self):
        self.nums_acquired = []
        self.nums_expected = []
        
    def add(self, number_acquired, number_requested):
        self.nums_acquired.append(number_acquired)
        self.nums_expected.append(number_requested)
        
    def print_out(self):
        i = 0
        logging.info("Test #\tAcquired\tRequested")
        for number_acquired, number_requested in zip(self.nums_acquired, self.nums_expected):
            logging.info("%d\t%d\t%d\t" % (i, number_acquired, number_requested ))
            i = i + 1

class MerlinTriggerTest():
    """Sets up and runs a repeatable test of acquiring images from Merlin with external trigger
    """
    
    def configure_merlin(self):
        """Configure the Merlin IOC"""
        
        logging.info("Configuring Merlin")
        
        # Make sure we're disarmed
        caput(self.pv["acquire"],             0, wait=False, timeout=5)
        # Configure acquisition
        caput(self.pv["exposure_time"],       self.parameters["exposureTime"],      wait=True, timeout=5)
        caput(self.pv["acquire_period"],      self.parameters["acquirePeriod"],     wait=True, timeout=5)
        caput(self.pv["num_images"],          self.parameters["numImagesPerFile"],  wait=True, timeout=5)
        IMAGE_MODE_MULTIPLE = 1
        caput(self.pv["image_mode"],          IMAGE_MODE_MULTIPLE,          wait=True, timeout=5)
        TRIGGER_START_RISING = 2
        caput(self.pv["trigger_mode"],        TRIGGER_START_RISING,          wait=True, timeout=5)
        # Reset array counter
        caput(self.pv["array_counter"],             0, wait=True, timeout=5)
        
        logging.info("Done configuring Merlin")
        
    def arm_merlin(self):
        """Arm the Merlin"""
        logging.info("Arming Merlin")
        caput(self.pv["acquire"],             1, wait=False, timeout=5)
        logging.info("Merlin armed")
        
        
    def configure_zebra(self):
        """Configure the Zebra IOC"""
        logging.info("Configure Zebra")
        
        CONFIG_FILE_PATH = "/home/tdq39642/git/aaw-scripts/zebra-config-files/BL13J-EA-ZEBRA-03_merlin_test.zeb"
        caput(self.pv["config_file_path"], CONFIG_FILE_PATH,          wait=True, timeout=5, datatype=DBR_CHAR_STR)
        
        caput(self.pv["config_file_load"], 1,          wait=True, timeout=5)
        
        
        logging.info("Done configuring Zebra")
        
    def start_zebra(self):
        """Arm the Zebra via Channel Access"""
        logging.info("Starting Zebra")
        caput(self.pv["zebra_arm"],             1, wait=False, timeout=5)
        logging.info("Zebra started")
        

    def start_one_acquisition(self, delay_s):
        """
        Start a single acquisition
        """
        logging.info("Preparing acqusition with delay %d s" % delay_s)
        self.configure_merlin()
        self.configure_zebra()
        self.arm_merlin()
        logging.info("Sleep for %d s" % delay_s)
        Sleep(delay_s)
        self.start_zebra()
        
        
    def zebra_armed(self):
        """
        Returns true if acquisition is in progress or file is open
        """
       
        zebra_armed = caget(self.pv["zebra_arm_rbv"], datatype=DBR_LONG)

        if (zebra_armed == 1):
            logging.debug("zebra is still armed")
            return True
        else:
            logging.debug("zebra is no longer armed")
            return False
            
    def merlin_still_armed(self):
        """Return True if Merlin is acquiring"""
        merlin_armed = caget(self.pv["acquire"], datatype=DBR_LONG)
        if (merlin_armed == 1):
            logging.debug("merlin is still armed")
            return True
        else:
            logging.debug("merlin is no longer armed")
            return False
        
    def getStats(self):
        """
        Grab the diagnostics we need 
        """
        logging.info("getStats called")
        
    def runTests(self):
        """
        Run the tests in a loop
        """
        
        self.results = Result()
        for test_index in range(0, self.parameters["numFiles"]):
            logging.info("Run test %d" % test_index)
            
            # Start acquisition
            self.start_one_acquisition(5)
            
            # Give it at least 10 seconds to get going
            Sleep(10)
            
            # Wait until zebra has sent all triggers
            while self.zebra_armed():
                logging.debug("Sleeping 1s")
                Sleep(1)
                
            # Give Merlin time to complete
            when_we_started_waiting = time.time()
            how_patient_we_are = 5 #seconds
            
            
            
            while self.merlin_still_armed():
                Sleep(1)
                time_we_have_waited = time.time() - when_we_started_waiting
                if time_we_have_waited > how_patient_we_are:
                    logging.info("Merlin is still armed after %d s so abort." % time_we_have_waited)
                        
                    logging.info("Disarming Merlin myself")
                    caput(self.pv["acquire"],             0, wait=False, timeout=5)
                    break
            
            # Take a note of how many frames we got versus how many we wanted.
            number_arrays_collected = caget(self.pv["array_counter_rbv"], datatype=DBR_LONG)
            number_arrays_requested = self.parameters["numImagesPerFile"]
            logging.info("Acquired %d, requested %d" % (number_arrays_collected, number_arrays_requested))
            
            # Mismatch
            if (number_arrays_collected != number_arrays_requested):
                logging.warning("Number of arrays collected does not match number requested.")
            
            # Record the results
            self.results.add(number_arrays_collected, number_arrays_requested)
            
        # Print the results
        self.results.print_out() 
    
    def __init__(self, testParams, logging_path):
        """
        Set up a test; wait for user input to run
        """
        
        # Set up logging
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
        logging_filename = os.path.join(logging_path, 'merlin_%s.log' % timestamp)
        logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', filename=logging_filename, level=logging.INFO)
        # Write also to stdout
        logging.getLogger().addHandler(logging.StreamHandler())
        logging.info("Start log for Merlin trigger test")
        
        self.parameters = testParams
        
        logging.info("Parameters:")
        for key, value in self.parameters.items():
            try:
                logging.info("%s: %s" % (key, value))
            except:
                pass
        
        # Handy variables
        self.pv = self.parameters["pvNames"]
        """
        self.camPrefix = self.parameters["camPrefix"]
        self.hdfPrefix = self.parameters["hdfPrefix"]
        self.fileNames = []
        self.hdfQueue = []
        
        # Key PV names
        self.pvNames = self.parameters["pvNames"]
        self.pvsToRecord = self.pvNames["performance"] + [self.pvNames["filenameRbv"], self.pvNames["numCapturedRbv"], self.pvNames["writeTime"], self.pvNames["writeSpeed"], self.pvNames["writeStatus"], self.pvNames["writeMessage"], self.pvNames["droppedHdf"]]
        """
        logging.info("Finished constructor")
        

if __name__ == "__main__":
    
    # Define test parameters
    testParamsJ13 = {
        "numImagesPerFile":   500,
        "numFiles":           100,
        "exposureTime":       0.1,
        "acquirePeriod":      0.1,
        "merlinPrefix":       "BL13J-EA-DET-04",
        "camPrefix":          ":CAM",
        "hdfPrefix":          ":HDF5",
        "zebraPrefix":        "BL13J-EA-ZEBRA-03"}

    testParams = testParamsJ13
    
    # Define PV names
    cam_prefix = testParams["merlinPrefix"] + testParams["camPrefix"]
    zebra_prefix = testParams["zebraPrefix"]
    
    testParams["pvNames"] = {
        # Merlin
        "acquire"           : cam_prefix + ":Acquire",
        "exposure_time"     : cam_prefix + ":AcquireTime",
        "acquire_period"    : cam_prefix + ":AcquirePeriod",
        "image_mode"        : cam_prefix + ":ImageMode",
        "num_images"        : cam_prefix + ":NumImages",
        "trigger_mode"      : cam_prefix + ":TriggerMode",
        "array_counter"     : cam_prefix + ":ArrayCounter",
        "array_counter_rbv" : cam_prefix + ":ArrayCounter_RBV",
        
        # Zebra
        "config_file_path"  : zebra_prefix + ":CONFIG_FILE",
        "config_file_load"  : zebra_prefix + ":CONFIG_READ.PROC",
        "zebra_arm"         : zebra_prefix + ":PC_ARM",
        "zebra_arm_rbv"     : zebra_prefix + ":PC_ARM_OUT",
        }

    logging_path = "/home/tdq39642/git/aaw-scripts/merlin-ext-trig-tests/logs"
    
    # Create test object
    t = MerlinTriggerTest(testParams, logging_path)

    t.runTests()
        
    logging.info("Tests finished")
