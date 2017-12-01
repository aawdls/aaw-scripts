#!/dls_sw/prod/tools/RHEL6-x86_64/defaults/bin/dls-python
from pkg_resources import require
require('cothread') #http://cothread.readthedocs.io/en/latest/catools.html
from cothread.catools import *
from cothread import Sleep
#from pcoSim import *
import datetime, time, csv, sys, os, logging, subprocess

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

class ExcaliburTriggerTest():
    """Sets up and runs a repeatable test of acquiring images from Excalibur with external trigger
    """
    
    def configure_detector(self):
        """Configure the Excalibur IOC"""
        
        logging.info("Configuring detector")
        
        # Make sure we're disarmed
        caput(self.pv["acquire"],             0, wait=False, timeout=5)
        # Configure acquisition
        caput(self.pv["exposure_time"],       self.parameters["exposureTime"],      wait=True, timeout=5)
        caput(self.pv["acquire_period"],      self.parameters["acquirePeriod"],     wait=True, timeout=5)
        caput(self.pv["num_images"],          self.parameters["numImagesPerFile"],  wait=True, timeout=5)
        IMAGE_MODE_MULTIPLE = 1
        caput(self.pv["image_mode"],          IMAGE_MODE_MULTIPLE,          wait=True, timeout=5)
        TRIGGER_EXTERNAL = 1
        caput(self.pv["trigger_mode"],        TRIGGER_EXTERNAL,          wait=True, timeout=5)
        # Reset array counter
        caput(self.pv["array_counter"],             0, wait=True, timeout=5)
        # Set number of frames to capture in HDF5
        caput(self.pv["num_capture"],               self.parameters["numImagesPerFile"], wait=True, timeout=5)
        
        logging.info("Done configuring detector")
        
    def arm_detector(self):
        """Arm the detector"""
        logging.info("Arming detector")
        caput(self.pv["capture"],             1, wait=False, timeout=5)
        caput(self.pv["acquire"],             1, wait=False, timeout=5)
        logging.info("Detector armed")
        
        
    def configure_zebra(self):
        """Configure the Zebra IOC"""
        logging.info("Configure Zebra")
        
        CONFIG_FILE_PATH = "/home/tdq39642/git/aaw-scripts/zebra-config-files/BL13J-EA-ZEBRA-02_config.zeb"
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
        self.configure_detector()
        self.configure_zebra()

        self.run_vds_gen()

        self.arm_detector()
        # TODO: Instead of doing a software delay here, probs better to have first
        # set the gate start param to the desired delay, then arm the Zebra at (as near as) 
        # the same time as the detector
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
            
    def detector_still_armed(self):
        """Return True if Detector is armed"""
        detector_armed = caget(self.pv["acquire"], datatype=DBR_LONG)
        hdf_armed = caget(self.pv["capture_rbv"], datatype=DBR_LONG)

        if (detector_armed == 1):
            logging.debug("Detector is still armed")
            retval= True
        elif (hdf_armed == 1):
            logging.debug("HDF writer is still armed")
            retval = True
        else:
            logging.debug("Detector is no longer armed")
            retval = False
        return retval
        
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
            
            
            
            while self.detector_still_armed():
                Sleep(1)
                time_we_have_waited = time.time() - when_we_started_waiting
                if time_we_have_waited > how_patient_we_are:
                    logging.info("Detector is still armed after %d s so abort." % time_we_have_waited)
                        
                    logging.info("Disarming detector myself")
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

    def run_vds_gen(self):
        """Run dls-vds-gen.py to create a virtual dataset"""
        # Arguments for VDS command
        vds_params={}
        vds_params["wd"] = str(caget(self.pv["data_dir"], datatype=DBR_CHAR_STR))
        vds_params["file_number"] = int(caget(self.pv["file_number"], datatype=DBR_LONG))
        vds_params["num_images"] = self.parameters["numImagesPerFile"]

        # Substitute the arguments
        command = "dls-vds-gen.py %(wd)s -f "
        for fem in xrange(1,7):
            command = command + "excalibur-%d" % (fem)
            command = command + "--%(file_number)d.hdf "

        command = command + "--source_node /entry/instrument/detector/data "
        command = command + "--target_node /entry/instrument/detector/data "
        command = command + "-s 0 -m 121 --shape %(num_images)d 259 2069 -o excalibur_%(file_number)d_vds.h5 -l 1 "
        command = command + "--empty"

        command = command % (vds_params)

        # Execute the command
        logging.info(command)
        subprocess.call(command.split(" "))
    
    def __init__(self, testParams, logging_path):
        """
        Set up a test; wait for user input to run
        """
        
        # Set up logging
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
        logging_filename = os.path.join(logging_path, 'excalibur_%s.log' % timestamp)
        logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', filename=logging_filename, level=logging.INFO)
        # Write also to stdout
        logging.getLogger().addHandler(logging.StreamHandler())
        logging.info("Start log for Excalibur trigger test")
        
        self.parameters = testParams
        
        logging.info("Parameters:")
        for key, value in self.parameters.items():
            try:
                logging.info("%s: %s" % (key, value))
            except:
                pass
        
        # Handy variables
        self.pv = self.parameters["pvNames"]

        logging.info("Finished constructor")
        

if __name__ == "__main__":
    
    # Define test parameters
    testParamsJ13 = {
        "numImagesPerFile":   10000,
        "numFiles":           140,
        "exposureTime":       0.01,
        "acquirePeriod":      0.01,
        "excaliburPrefix":    "BL13J-EA-EXCBR-01:CONFIG",
        "camPrefix":          ":ACQUIRE",
        "hdfPrefix":          ":HDF5",
        "zebraPrefix":        "BL13J-EA-ZEBRA-02"}

    testParams = testParamsJ13
    
    # Define PV names
    cam_prefix = testParams["excaliburPrefix"] + testParams["camPrefix"]
    hdf_prefix = testParams["excaliburPrefix"] + testParams["hdfPrefix"]
    zebra_prefix = testParams["zebraPrefix"]
    
    testParams["pvNames"] = {
        # Excalibur
        "acquire"           : cam_prefix + ":Acquire",
        "exposure_time"     : cam_prefix + ":AcquireTime",
        "acquire_period"    : cam_prefix + ":AcquirePeriod",
        "image_mode"        : cam_prefix + ":ImageMode",
        "num_images"        : cam_prefix + ":NumImages",
        "trigger_mode"      : cam_prefix + ":TriggerMode",
        "array_counter"     : cam_prefix + ":ArrayCounter",
        "array_counter_rbv" : cam_prefix + ":ArrayCounter_RBV",
        "num_capture"       : hdf_prefix + ":NumCapture",
        "capture"           : hdf_prefix + ":Capture",
        "capture_rbv"       : hdf_prefix + ":Capture_RBV",
        "data_dir"          : hdf_prefix + ":FilePath_RBV",
        "file_number"       : hdf_prefix + ":FileNumber_RBV",
        
        # Zebra
        "config_file_path"  : zebra_prefix + ":CONFIG_FILE",
        "config_file_load"  : zebra_prefix + ":CONFIG_READ.PROC",
        "zebra_arm"         : zebra_prefix + ":PC_ARM",
        "zebra_arm_rbv"     : zebra_prefix + ":PC_ARM_OUT",
        }

    logging_path = "/home/tdq39642/git/aaw-scripts/excalibur-ext-trig-tests/logs"
    
    # Create test object
    t = ExcaliburTriggerTest(testParams, logging_path)

    t.runTests()
        
    logging.info("Tests finished")
