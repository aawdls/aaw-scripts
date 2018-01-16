'''
Created on 12 Nov 2014

@author: Darren Batey
'''
from time import sleep
import time
import scisoftpy as dnp
import scisoftpy.random as drd
import scisoftpy.plot as dpl
import scisoftpy.roi as droi
from i13j_utilities import send_email
from gda.data import NumTracker
i13jNumTracker = NumTracker('i13j')

avail_det = ['merlin','excalibur','xmap']
avail_stages = ['t1','t1_s','sample_lab','t1_theta']

hw_readout = 0.002


def stxmScan_HW(nX=5,nY=5,dX=2,dY=2,exp=1,detector="excalibur"):
    print 'stxmScan_HW'
    readout=hw_readout
    #XY scan
    nZ = 0
    dZ = 0
    mot = 0
    
    pv = set_pvs(detector)
    
    configure_zebra(pv,detector,exp,readout,nX*nY)
    configure_detector_STXM(detector,nX,nY,exp,pv)
    configure_scan(nX,nY,nZ,dX,dY,dZ,detector,exp,readout,mot)
    arm_detector(pv)
    
    proj_ok, hdfpath = trigger(pv,detector)
    return hdfpath
    
def pycho_collect(nX=5,nY=5,dX=2,dY=2,exp=1,detector="excalibur",sT=-90.0,nT=180.0,rT=180.0):
    if exp < 1:
        triggering = "hardware"
    else:
        triggering = "software"
        
    if triggering == "hardware":
        if nT == 1:
            ptychoScan_HW(nX,nY,dX,dY,exp,detector)
        else:
            ptychoTomoScan_HW(nX,nY,dX,dY,exp,detector,sT,nT,rT)
    elif triggering == "software":
        if nT ==1:
            ptychoScan_SW(nX,nY,dX,dY,exp)
        else:
            ptychoTomoScan_SW(nX,nY,dX,dY,exp,sT,nT,rT)
        
def ptychoScan_HW(nX=5,nY=5,dX=2,dY=2,exp=1,detector="excalibur"):
    hw_readout = 0.001
    readout=hw_readout
    #XY scan
    nZ = 0
    dZ = 0
    mot = 0
    
    xIn = t1_sx.getPosition()
    yIn = t1_sy.getPosition()
    zIn = t1_sz.getPosition()
    
    pv = set_pvs(detector)
    
    configure_detector(detector,nX,nY,exp,pv)
    arm_detector(pv, detector)
    
    configure_zebra(pv,detector,exp,readout,nX*nY)
    configure_scan(nX,nY,nZ,dX,dY,dZ,detector,exp,readout,mot)
    
    max_time = 5 * ((exp+readout+5e-3)*nX*nY)
    
    proj_ok, hdfpath = trigger(pv,detector,max_time)
    return proj_ok
    
def ptychoTomoScan_HW(nX=5,nY=5,dX=2,dY=2,exp=1,detector="excalibur",sT=-90.0,nT=180.0,rT=180.0):
    hw_readout = 0.001
    readout=hw_readout
    nZ = 0
    dZ = 0
    mot = 0

    # We will use the current position as starting position
    xIn = t1_sx.getPosition()
    yIn = t1_sy.getPosition()
    zIn = t1_sz.getPosition()

    # Prepare a log file
    _fname = ptychoTomoScan_HW.__name__
    log_path="/dls/i13-1/data/2018/cm19663-1/raw/"
    file_name = _fname + "_"
    timestr = time.strftime("%d_%m_%Y-%H%M%S")
    file_name += timestr
    file_name += ".log"
    file_path = os.path.join(log_path,file_name)
    logfh = open(file_path, 'w')
    print "Path to the log file %s" %(file_path)
    msg = "theta, scan, attempt"
    logfh.write(msg+"\n")
    logfh.flush()

    # Get list of PV names for this detector
    pv = set_pvs(detector)

    # Zero Exclaibur's array counters to aid spotting problems
    if detector == "excalibur":
        zero_excalibur_counters()

    # Initial configuration of detector, Zebra, Geobrick
    configure_detector(detector,nX,nY,exp,pv)
    configure_zebra(pv,detector,exp,readout,nX*nY)
    configure_scan(nX,nY,nZ,dX,dY,dZ,detector,exp,readout,mot)

    # Calculate list of Theta positions, with:
    # dT = Theta step
    # rT = Theta range
    # eT = end Theta
    # sT = start Theta
    dT = rT / (nT-1)
    eT = sT + (nT-1)*(dT)
    print sT, dT, eT
    theta_range = dnp.arange(sT, eT + dT, dT)
    print "Theta positions:"
    print theta_range

    # Loop over Theta positions
    count = 0
    for theta in theta_range:
        attempts_max = 3
        attempt_count = 0
        proj_ok = 0
        count += 1

        # Move Theta to next position
        t1_theta.moveTo(theta)
        print t1_theta
        print "projection number = ", count

        # If the projection fails it will be retried a few times
        while proj_ok == 0 and attempt_count < attempts_max:
            # Configure and arm the detector, configure the Zebra
            configure_detector(detector, nX, nY, exp, pv)
            arm_detector(pv, detector)
            configure_zebra(pv, detector, exp, readout, nX * nY)

            # Move sample X Y Z to initial position
            t1_sx.moveTo(xIn)
            t1_sy.moveTo(yIn)
            t1_sz.moveTo(zIn)

            # We only need to update the start and centre positions for the scan
            # on the Geobrick since the other settings stay the same
            configure_scan_stage(nX, nY, nZ, dX, dY, dZ)

            # Start the projection proper
            # - we judge preojection failed if it takes more than max_time
            max_time = 5 * ((exp + readout + 5e-3) * nX * nY)
            proj_ok, hdfpath = trigger(pv, detector, max_time, logfh, attempt_count)
            print "scan completed: status", proj_ok

            # What to do if projection failed
            if proj_ok == 0:
                attempt_count += 1
                if (attempt_count >= attempts_max):
                    # TODO: Send an emil?
                    print "Ran out of attempts"
                else:
                    print "Re-trying failed projection, attempt %d" % attempt_count
                    clear_det(attempt_count, pv, 2, 1)


        """
        while proj_ok == 0 and attempt_count < attempts_max:
            arm_detector(pv, detector)
            configure_detector(detector,nX,nY,exp,pv)
            
            t1_sx.moveTo(xIn)
            t1_sy.moveTo(yIn)
            t1_sz.moveTo(zIn)
            t1_theta.moveTo(theta)
            print t1_theta
            print "projection number = ", count
            count += 1
            configure_scan_stage(nX,nY,nZ,dX,dY,dZ)
            
            max_time = 5 * ((exp+readout+5e-3)*nX*nY)
            proj_ok, hdfpath = trigger(pv,detector,max_time,logfh, attempt_count)
            print "scan completed: status", proj_ok
            if proj_ok == 0:
                attempt_count += 1
                clear_det(attempt_count,pv,2,1)
                """
    # Close the log file
    logfh.close()
    
    
def ptychoScanTest(nX=5,nY=5,dX=2,dY=2,exp=1,detector="excalibur"):
    readout=hw_readout
    nZ = 0
    dZ = 0
    mot = 0
    
    pv = set_pvs(detector)
    configure_zebra(pv,detector,exp,readout,nX*nY)
    configure_detector(detector,nX,nY,exp,pv)
    configure_scan(nX,nY,nZ,dX,dY,dZ,detector,exp,readout,mot)
    
    from gda.data import NumTracker
    i13jNumTracker = NumTracker('i13j')
    
    logfile = "/dls_sw/i13-1/scripts/Testing/log4.txt"
    
    f = open(logfile,"w")
    f.write("Proj OK, Images CAM, Images HDF, Scan Number, Number Of Pulses\n")
    f.close()
    
    for i in dnp.arange(1000):
        attempts_max = 1000
        attempt_count = 0
        proj_ok = 0
        while proj_ok == 0 and attempt_count < attempts_max:
            configure_scan_stage(nX,nY,nZ,dX,dY,dZ)
            sleep(0.05)
            arm_detector(pv)
            sleep(0.05)
            
            caput('BL13J-EA-ZEBRA-03:PC_DISARM',1)
            caput('BL13J-EA-ZEBRA-03:PC_ARM',1)
            proj_ok, hdfpath = trigger(pv,detector)
            caput('BL13J-EA-ZEBRA-03:PC_DISARM',1)
            pulses = caget('BL13J-EA-ZEBRA-03:PC_TIME')
            pulses_split = pulses.split(':')
            
            count = 0
            found_zero = 0
            while (not found_zero) or (count == 10000):
                if float(pulses_split[count]) == 0:
                    found_zero = 1
                count += 1
            
            n_pulses = count-2 #subtract one extra for additional value in PC_TIME string
            
            out_str = str(proj_ok) + "," + str(caget('BL13J-EA-DET-04:CAM:NumImagesCounter_RBV')) + "," + str(caget('BL13J-EA-DET-04:HDF5:NumCaptured_RBV')) + "," + str(i13jNumTracker.currentFileNumber) + "," + str(n_pulses) + "," + pulses[0:7000]
            
            f = open(logfile,"a")
            f.write(out_str + "\n")
            f.close()
            print out_str
            
            if proj_ok == 0:
                attempt_count += 1
                clear_det(attempt_count,pv,2,0)
                configure_detector(detector,nX,nY,exp,pv)
    
def ptychoScan_SW(nX=5,nY=5,dX=2,dY=2,exp=1,detector="excalibur"):
    scan sample_lab_xy two_motor_positions merlin_sw_hdf exptime
    
def ptychoTomoScan_SW(nX=5,nY=5,dX=2,dY=2,exp=1,sT=-90.0,nT=180.0,rT=180.0):
    xIn = t1_sx.getPosition()
    yIn = t1_sy.getPosition()
    zIn = t1_sz.getPosition()
    
    dT = rT / (nT-1)
    eT = sT + (nT-1)*(dT)
    print sT, dT, eT
    theta_range = dnp.arange(sT, eT + dT, dT)
    print "Theta positions:"
    print theta_range
    
    for theta in theta_range:
        print theta
        t1_theta.moveTo(theta)
        print t1_theta
        scan sample_lab_xy two_motor_positions merlin_sw_hdf exptime

def configure_scan(nX,nY,nZ,dX,dY,dZ,detector,exp,readout,mot):
    """Set all P variables on Geobrick necessary to configure a scan"""
    configure_scan_params(nX,nY,nZ,dX,dY,dZ)
    configure_scan_stage(nX,nY,nZ,dX,dY,dZ)
    configure_scan_detector(detector,exp,readout,mot)

def configure_scan_params(nX,nY,nZ,dX,dY,dZ):
    """Set P variables for number of steps and setp size on Geobrick"""
    send_command('P2411',str(nX))# X_NUM_STEPS
    send_command('P2412',str(nY))# Y_NUM_STEPS
    send_command('P2428',str(nZ))# Z_NUM_STEPS
    
    send_command('P2413',str(dX))# X_STEP_SIZE [um]
    send_command('P2414',str(dY))# Y_STEP_SIZE [um]
    send_command('P2429',str(dZ))# Z_STEP_SIZE [um]

def configure_scan_stage(nX,nY,nZ,dX,dY,dZ):
    """Set P variables for start and centre positions on Geobrick"""
    roiX = nX*dX #[um]
    roiY = nY*dY #[um]
    roiZ = nZ*dZ #[um]
    
    centreX = sample_lab_x.getPosition() #[um]
    centreY = sample_lab_y.getPosition() #[um]
    centreZ = sample_lab_z.getPosition() #[um]
    
    startX = centreX - (roiX/2)# -dX
    startY = centreY - (roiY/2)# -dY
    startZ = centreZ - (roiZ/2)# -dZ
    
    send_command('P2416',str(startX))#X START
    send_command('P2417',str(startY))#Y START
    send_command('P2418',str(startZ))#Z START
    
    send_command('P2423',str(centreX))#X CENTRE
    send_command('P2424',str(centreY))#Y CENTRE
    send_command('P2425',str(centreZ))#Z CENTRE

def configure_scan_detector(detector,exp,readout,mot):
    """Set P variables for Exposure, Readout and Motion time (unused) on Geobrick"""
    print "Configure scan detector:"
    print "Readout = " + str(readout)
    print "Exposure = " + str(exp)
    print "Motion = " + str(mot)
    
    send_command('P2426',str(readout*1000))# Readout_time [ms]
    send_command('P2427',str(exp*1000))# Exposure_time [ms]
    send_command('P2431',str(mot*1000))# Motion_time [ms]

def wait_for_excalibur_state(desired_state, pv):
    """Wait for Excalibur to report it is in desired_state, with timeout"""
    count_max = 50
    count = 0
    detector_state = caget(pv.detector_state_pv)
    while (detector_state != desired_state and count < count_max):
        sleep(0.5)
        count += 1
        detector_state = caget(pv.detector_state_pv)
        print "Waiting for Excalibur to be in state %s. Waited %.1f s so far." % (desired_state, count * 0.5)
    if count >= count_max:
        print "Excalibur didn't become %s within 30s, something must be wrong." % (desired_state)
        # TOTO: Send email or similar to notify a problem with the detector

def zero_excalibur_counters():
    """ Zero Excalibur array counters so it's easier to spot problems """
    counter_pvs = ['BL13J-EA-EXCBR-01:CONFIG:ACQUIRE:ArrayCounter',
                'BL13J-EA-EXCBR-01:CONFIG:HDF5:ArrayCounter',
                'BL13J-EA-EXCBR-01:CONFIG:HDF5:DroppedArrays',
                'BL13J-EA-EXCBR-01:CONFIG:FIX:ArrayCounter',
                'BL13J-EA-EXCBR-01:CONFIG:FIX:DroppedArrays']
    for counter_pv in counter_pvs:
        caput(counter_pv, 0)

def arm_detector(pv, detector):
    """Arm the detector. Blocks until we think the detector is ready to accept triggers."""

    # Wait for Excalibur to be in state Idle before trying to arm it
    if detector.find("excalibur") >= 0:
        wait_for_excalibur_state("Idle",pv)

    # Set Acquire and start HDF writer
    caput(pv.acquire_pv, 1)
    caput(pv.hdf_capture_pv, 1)

    # Confirm that Acquire has been set
    acquire_state = caget(pv.acquire_pv)
    count_max = 50
    count = 0
    while (acquire_state == 'Done' and count < count_max):
        sleep(0.5)
        count +=1
        acquire_state = caget(pv.acquire_pv)

    # Wait for Excalibur to be in state Acquire before trying to trigger it
    if detector.find("excalibur") >= 0:
        wait_for_excalibur_state("Acquire",pv)


def configure_detector(detector,nX,nY,exp,pv):
    caput(pv.acquire_pv, 0)
    caput(pv.hdf_capture_pv, 0)
    caput(pv.imagemode_pv,'Multiple')
    if detector =='merlin':
        caput(pv.triggermode_pv,'Trigger start rising')
        caput("BL13J-EA-DET-04:HDF5:FileWriteMode","Stream")
    elif detector == 'excalibur':
        caput("BL13J-EA-EXCBR-01:CONFIG:ACQUIRE:CounterDepth","12 bit")
        caput(pv.triggermode_pv,'External')
    elif detector == 'excalibur_external':
        caput("BL13J-EA-EXCBR-01:CONFIG:ACQUIRE:CounterDepth","12 bit")
        caput(pv.triggermode_pv,'External')
    elif detector == 'excalibur_sync':
        caput("BL13J-EA-EXCBR-01:CONFIG:ACQUIRE:CounterDepth","12 bit")
        caput(pv.triggermode_pv,'Sync')
    caput(pv.numimages_pv,nX*nY)
    caput(pv.exposure_pv,exp)
    caput(pv.period_pv,exp)
    caput(pv.hdf_callback_pv,'Enable')
    caput(pv.hdf_numcapture_pv,nX*nY)
    
def configure_detector_STXM(detector,nX,nY,exp,pv):
    caput(pv.acquire_pv, 0)
    caput(pv.hdf_capture_pv, 0)
    caput(pv.imagemode_pv,'Multiple')
    if detector =='merlin':
        caput(pv.triggermode_pv,'Trigger start rising')
        caput("BL13J-EA-DET-04:HDF5:FileWriteMode","Stream")
    elif detector == 'excalibur':
        caput(pv.triggermode_pv,'External')
    elif detector == 'excalibur_external':
        caput(pv.triggermode_pv,'External')
    elif detector == 'excalibur_sync':
        caput(pv.triggermode_pv,'Sync')
    caput(pv.numimages_pv,nX*nY)
    caput(pv.exposure_pv,exp)
    caput(pv.period_pv,exp)
    caput(pv.hdf_callback_pv,'Enable')
    caput('BL13J-EA-DET-04:ROI:EnableCallbacks','Enable')
    caput('BL13J-EA-DET-04:HDF5:NDArrayPort','merlin1.roi')
    caput('BL13J-EA-DET-04:ROI:NDArrayPort','merlin1.cam')
    
    #optic_axis = [256,256]
    bin_size = [64,64]
    
    caput('BL13J-EA-DET-04:ROI:BinX',bin_size[0])
    caput('BL13J-EA-DET-04:ROI:BinY',bin_size[1])
    
    caput(pv.hdf_numcapture_pv,nX*nY)

def configure_zebra(pv,detector,exp,read,n_exps):
    caput("BL13J-EA-ZEBRA-02:PC_GATE_SEL","External")
    caput("BL13J-EA-ZEBRA-02:PC_GATE_INP",52)
    caput("BL13J-EA-ZEBRA-02:PULSE1_INP",1)
    caput("BL13J-EA-ZEBRA-02:PULSE1_WID", exp + read)
    
    
    caput("BL13J-EA-ZEBRA-02:PC_PULSE_WID", exp)
    caput("BL13J-EA-ZEBRA-02:PC_PULSE_STEP", exp+read)
    
    caput("BL13J-EA-ZEBRA-02:PC_GATE_NGATE",n_exps)
    caput("BL13J-EA-ZEBRA-02:PC_PULSE_MAX",1)
        
    if detector == "excalibur":
        #zebra_in = 36 #invert signal through OR gate
        #caput(pv.zebra_out_pv,zebra_in)
        
        caput("BL13J-EA-ZEBRA-02:OR2_INP1", 31)
        caput("BL13J-EA-ZEBRA-02:OUT2_TTL",37)
        
        caput("BL13J-EA-ZEBRA-02:PC_ARM",1)
        sleep(0.1)
        #caput("BL13J-EA-ZEBRA-02:OR1_INP1",1)
    elif detector == "merlin":
        #zebra_in = 31
        #caput(pv.zebra_out_pv,zebra_in)
        caput("BL13J-EA-ZEBRA-02:OUT1_TTL",31)
        caput("BL13J-EA-ZEBRA-02:PC_ARM",1)
        sleep(0.1)

def trigger(pv,detector,max_time = 300,logfh=None, attempt_count=0):
    proj_ok = 1
    nextfile = i13jNumTracker.getCurrentFileNumber() + 1
    i13jNumTracker.incrementNumber()
    print "nextfile:", nextfile
    if not logfh is None:
        msg = "%.5f, %d, %d" %(t1_theta.getPosition(), nextfile, attempt_count)
        logfh.write(msg+"\n")
        logfh.flush()
    caput(pv.hdf_nextfile_pv, nextfile)
    hdfpath = gethdfdatapath(nextfile,detector)
    createNexusScanFile(hdfpath)
    
    
    send_command('P2432','1')# SCAN XY
    
    ## RUN ##
    caput(pv.geobrick_cmd,'&2b24r')
    
    count_total = max_time
    
    if detector == "merlin":
        count = 0
        scan_finished = 0
        while (scan_finished == 0): #and (count < 300):
            capture_final = int(caget("BL13J-EA-DET-04:HDF5:NumCapture_RBV"))
            capture_current = int(caget("BL13J-EA-DET-04:HDF5:NumCaptured_RBV"))
            
            if capture_current+1 == capture_final:
                count_final = 0
                while count_final < count_total and capture_current < capture_final:
                    count_final += 1
                    sleep(1)
                    capture_final = int(caget("BL13J-EA-DET-04:HDF5:NumCapture_RBV"))
                    capture_current = int(caget("BL13J-EA-DET-04:HDF5:NumCaptured_RBV"))
                
                if count_final == count_total and capture_current < capture_final:
                    proj_ok = 0
                    scan_finished = 1
            
            if capture_current == capture_final:
                scan_finished = 1
                proj_ok = 1
                
            sleep(1)
            count += 1
    elif detector == "excalibur":

        capture_final = int(caget("BL13J-EA-EXCBR-01:CONFIG:HDF5:NumCapture_RBV"))
        capture_current = int(caget("BL13J-EA-EXCBR-01:CONFIG:HDF5:NumCaptured_RBV"))
        
        # Monitor number of frames written to HDF file
        count_final = 0
        while count_final < count_total and capture_current < capture_final:
            count_final += 1
            sleep(1)
            capture_final = int(caget("BL13J-EA-EXCBR-01:CONFIG:HDF5:NumCapture_RBV"))
            capture_current = int(caget("BL13J-EA-EXCBR-01:CONFIG:HDF5:NumCaptured_RBV"))
            
        # Say projection OK if we saved the right number of frames
        capture_final = int(caget("BL13J-EA-EXCBR-01:CONFIG:HDF5:NumCapture_RBV"))
        capture_current = int(caget("BL13J-EA-EXCBR-01:CONFIG:HDF5:NumCaptured_RBV"))
        
        if capture_current < capture_final:
            proj_ok = 0
            print "Projection %d failed. Captured %d, expected %d." % (nextfile, capture_current, capture_final)
        else:
            proj_ok = 1
            print "Projection %d completed successfully." % (nextfile)
                

    sleep(1.0)
    print " "
    
    caput("BL13J-EA-ZEBRA-02:PC_DISARM",1)
    #caput("BL13J-EA-ZEBRA-02:SYS_RESET.PROC",1)
    
    if proj_ok:
        #create vds
        generate_vds(hdfpath, capture_final)
    
    return proj_ok, hdfpath
    
def generate_vds(filepath, nimages, nnodes=6, scriptpath="/dls_sw/prod/tools/RHEL6-x86_64/defaults/bin/dls-vds-gen.py"):
    #dls-vds-gen.py /dls/i13-1/data/2017/cm16785-5/raw -f excalibur-1--133268.hdf excalibur-2--133268.hdf excalibur-3--133268.hdf excalibur-4--133268.hdf excalibur-5--133268.hdf excalibur-6--133268.hdf  --source_node /entry/instrument/detector/data --target_node /entry/instrument/detector/data -s 0 -m 121 --shape 3 259 2069 -t int32 -o excalibur-133268.hdf --empty
    node_filename_template = "excalibur-%d--%d.hdf"
    
    dirpath = filepath
    cmd = scriptpath
    cmd += " %s -f " %(dirpath)
    for i in range(nnodes):
        pass
    #/dls/i13-1/data/2017/cm16785-5/raw -f excalibur-1--133268.hdf excalibur-2--133268.hdf excalibur-3--133268.hdf excalibur-4--133268.hdf excalibur-5--133268.hdf excalibur-6--133268.hdf  --source_node /entry/instrument/detector/data --target_node /entry/instrument/detector/data -s 0 -m 121 --shape 3 259 2069 -t int32 -o excalibur-133268.hdf --empty

    
def collect_frame_HW(detector):
    pv = set_pvs(detector)
    trigger(pv,detector)

def createNexusScanFile(hdfpath):
    pass

def gethdfdatapath(nextfile,detector):
    if detector == "excalibur" or detector == "excalibur_external" or detector == "excalibur_sync":
        '''
        filepath = caget("BL13J-EA-EXCBR-01:CONFIG:PHDF:FilePath")
        name = caget("BL13J-EA-EXCBR-01:CONFIG:PHDF:FileName")
        template = caget("BL13J-EA-EXCBR-01:CONFIG:PHDF:FileTemplate")
        '''
        filepath = caget("BL13J-EA-EXCBR-01:CONFIG:HDF5:FilePath")
        name = caget("BL13J-EA-EXCBR-01:CONFIG:HDF5:FileName")
        template = caget("BL13J-EA-EXCBR-01:CONFIG:HDF5:FileTemplate")
        hdfpath = template %(filepath, name, nextfile)
    elif detector == "merlin":
        filepath = caget("BL13J-EA-DET-04:HDF5:FilePath")
        name = caget("BL13J-EA-DET-04:HDF5:FileName")
        template = caget("BL13J-EA-DET-04:HDF5:FileTemplate")
        hdfpath = template %(filepath, name, nextfile)
    print "hdfpath:", hdfpath
    return hdfpath

def send_command(address, data):
    geobrick_cmd = "BL13J-MO-STEP-25:ASYN.AOUT"
    #geobrick_out = "BL13J-MO-STEP-25:ASYN.AINP"
    caput(geobrick_cmd,address + '=' + data)
    waittime(0.1)
    #caput(geobrick_cmd,address)
    #rtn = str(caget(geobrick_out))[15:]

class blank_class():
    def __init__(detector):
        pass

def set_pvs(detector):
    pv = blank_class()
    pv.geobrick_cmd = "BL13J-MO-STEP-25:ASYN.AOUT"
    pv.geobrick_out = "BL13J-MO-STEP-25:ASYN.AINP"
    if detector == 'merlin':
        pv.acquire_pv="BL13J-EA-DET-04:CAM:Acquire"
        pv.exposure_pv="BL13J-EA-DET-04:CAM:AcquireTime"
        pv.period_pv="BL13J-EA-DET-04:CAM:AcquirePeriod"
        pv.imagemode_pv="BL13J-EA-DET-04:CAM:ImageMode"
        pv.triggermode_pv="BL13J-EA-DET-04:CAM:TriggerMode"
        pv.numimages_pv="BL13J-EA-DET-04:CAM:NumImages"
        pv.hdf_capture_pv="BL13J-EA-DET-04:HDF5:Capture"
        pv.hdf_numcapture_pv="BL13J-EA-DET-04:HDF5:NumCapture"
        pv.hdf_nextfile_pv = "BL13J-EA-DET-04:HDF5:FileNumber"
        pv.hdf_callback_pv = "BL13J-EA-DET-04:HDF5:EnableCallbacks"
        pv.zebra_out_pv = "BL13J-EA-ZEBRA-02:OUT1_TTL"
    elif detector == "excalibur" or detector == "excalibur_external" or detector == "excalibur_sync":
        pv.acquire_pv = "BL13J-EA-EXCBR-01:CONFIG:ACQUIRE:Acquire"
        # Overall state of detector
        pv.detector_state_pv = "BL13J-EA-EXCBR-01:CONFIG:ACQUIRE:DetectorState_RBV"
        pv.exposure_pv = "BL13J-EA-EXCBR-01:CONFIG:ACQUIRE:AcquireTime"
        pv.period_pv = "BL13J-EA-EXCBR-01:CONFIG:ACQUIRE:AcquirePeriod"
        pv.imagemode_pv = "BL13J-EA-EXCBR-01:CONFIG:ACQUIRE:ImageMode"
        pv.triggermode_pv = "BL13J-EA-EXCBR-01:CONFIG:ACQUIRE:TriggerMode"
        pv.numimages_pv = "BL13J-EA-EXCBR-01:CONFIG:ACQUIRE:NumImages"
        '''
        pv.hdf_capture_pv = "BL13J-EA-EXCBR-01:CONFIG:PHDF:Capture"
        pv.hdf_numcapture_pv = "BL13J-EA-EXCBR-01:CONFIG:PHDF:NumCapture"
        pv.hdf_nextfile_pv = "BL13J-EA-EXCBR-01:CONFIG:PHDF:FileNumber"
        pv.hdf_name_pv = "BL13J-EA-EXCBR-01:CONFIG:PHDF:FileName"
        pv.hdf_callback_pv = 'BL13J-EA-EXCBR-01:CONFIG:PHDF:EnableCallbacks'
        '''
        pv.hdf_capture_pv = "BL13J-EA-EXCBR-01:CONFIG:HDF5:Capture"
        pv.hdf_numcapture_pv = "BL13J-EA-EXCBR-01:CONFIG:HDF5:NumCapture"
        pv.hdf_nextfile_pv = "BL13J-EA-EXCBR-01:CONFIG:HDF5:FileNumber"
        pv.hdf_name_pv = "BL13J-EA-EXCBR-01:CONFIG:HDF5:FileName"
        pv.hdf_callback_pv = 'BL13J-EA-EXCBR-01:CONFIG:HDF5:EnableCallbacks'
        
        pv.zebra_out_pv = "BL13J-EA-ZEBRA-02:OUT2_TTL"
    return pv

whoto_lst = []
whoto_lst.append('silvia.cipiccia@diamond.ac.uk')
whoto_lst.append('darren.batey@diamond.ac.uk')
whoto_lst.append('xiaowen.shi@diamond.ac.uk')
whoto_lst.append('physicshome@gmail.com')
whoto_lst.append('kaz.wanelik@diamond.ac.uk')



def clear_det(attempt_count,pvs,sleep_sec=2,alert_email=0):
    _fname = clear_det.__name__
    body = "attempt_count %d" %(attempt_count)
    if alert_email:
        send_email(whoto_lst, _fname, body)
    caput(pvs.hdf_capture_pv, 0)
    caput(pvs.acquire_pv, 0)
    sleep(sleep_sec)
    exposure = caget(pvs.exposure_pv)
    try:
        print "Running the clearing scan..."
        repscan 1 merlin_sw_hdf exposure
        print "Finished running the clearing scan"
        caput(pvs.imagemode_pv,'Multiple')
        caput(pvs.triggermode_pv,'Trigger start rising')
    except Exception, e:
        msg = "Trouble in the clearing scan: %s" %(str(e))
        print msg
        if alert_email:
            send_email(whoto_lst, _fname, msg)
    

print 'stageMotion ready..'




def save(prevScan,ptychoScan):
    filename = ptychoScan.nxs_path + '_preview.hdf'
    print filename
    # open file for writing
    f = h5py.File(filename, "w")

    # populate the file with the classes tree
    entry_1 = f.create_group("entry_1")
    entry_1.attrs['NX_class'] = "NXentry"

    ##################
    ### EXPERIMENT ###
    ##################
    exp_1 = entry_1.create_group("experiment_1")
    exp_1.attrs['NX_class'] = "NXexperiment"
    exp_1.create_dataset("instrument",data="DLS I13-1")
#     exp_1.create_dataset("experiment_ID",data=gen.experiment_ID)

    ######################
    ### Preview Images ###
    ######################
    
    exp_1_pre_1 = exp_1.create_group("previews")
    exp_1_pre_1.create_dataset("preview_images",data=prevScan.imstack)
    
#     exp_1_pre_1.create_dataset("data_path",data=prevScan.nxs_path)
#     exp_1_pre_1.create_dataset("preview",data=prevScan.stxm)
#     exp_1_pre_1.create_dataset("STXM_BF",data=prevScan.stxm_bf)
#     exp_1_pre_1.create_dataset("STXM_DF",data=prevScan.stxm_df)
#     exp_1_pre_1.create_dataset("COM_X",data=prevScan.com_x)
#     exp_1_pre_1.create_dataset("COM_Y",data=prevScan.com_y)
    
#     exp_1_pre_1.create_dataset("centre",data=prevScan.centre)
#     exp_1_pre_1.create_dataset("pixel-pitch",data=prevScan.step)
#     exp_1_pre_1.create_dataset("scan size",data=prevScan.sz)
    
    f.close()

def question(quest = 'Question?',ans_typ = 'str',default = 'default',limits = ['y','n']):
    ''' Ask the user for input with error checking
    '''
    if ans_typ == 'str':
        cont2 = False
        while cont2 == False:
            cont = False
            while cont == False:
                if cont == False:
                    limits_str = '/'.join(limits)
                    print quest
                    quest_in = 'Default-[%s] Options-[%s]' %(default,limits_str)
                    user = requestInput(quest_in)
                    if user == '':
                        user = default
                    cont = user.isalpha()
            for loop in range(0,len(limits)):
                if limits[loop]==user:
                    cont2 = True
    elif ans_typ == 'num':
        # Check limits
#         cont3 = False
#         while cont3 == False:
#             # Check format [n,n]7
#             cont2 = False
#             while cont2 == False:
#                 # Check not a string
#                 cont = False
#                 while cont == False:
#                     cont = True
#                     try:
#                         user = requestInput(quest+'\nDefault-[%s]\\n Limits-%s\n' %(default,limits,))
        print quest
        quest_in = 'Default-%s Range-[%s:%s]' %(default,limits[0],limits[1])
        user = requestInput(quest_in)
#         user = requestInput(quest)
        if user == '':
            user = default
        else:
            user = float(user)

#                     except NameError:
#                         cont = False
#                     except SyntaxError:
#                         user = default
#                         cont = True
#                 if (type(user) == int) | (type(user) == float):
#                     cont2 = True
#                 else:
#                     cont2 = False
#             if limits != None:
#                 if (float(user)<float(min(limits))) | (float(user)>float(max(limits))):
#                     None
#                 else:
#                     cont3 = True
#             else:
#                 cont3 = True
    elif ans_typ == 'tup':
#         a = '\nDefault-[%g,%g]\\n' %(default[0],default[1])
        # Check limits
#         cont3 = False
#         while cont3 == False:
#             # Check format [n,n]
#             cont2 = False
#             while cont2 == False:
#                 # Check not a string
#                 cont = False
#                 while cont == False:
#                     cont = True
#                     try:
#                         user = requestInput(quest+a+' Limits-%s\n' %(limits))
#         limits_str = '/'.join(limits)
        print quest
        quest_in = 'Default-%s Range-[%s:%s]' %(default,limits[0],limits[1])
        user = requestInput(quest_in)

        if user == '':
            user = default
        else:
            user_split = user.split(',')
            user_lst = []
    #         i = 0
            for x in user_split: 
                user_lst.append(float(x))
    #             i += 1
            user = tuple(user_lst)
#         print type(user)
#                     except NameError:
#                         cont = False
#                     except SyntaxError:
#                         user = default
#                         cont = True

#                 if (type(user) == tuple):
#                     cont2 = True
#                 else:
#                     cont2 = False
#             if (float(min(user))<float(min(limits))) | (float(max(user))>float(max(limits))):
#                 None
#             else:
#                 cont3 = True
    else:
        print 'Unknown answer type!'
    return user

def bragg_preview_labx_pitch(n1,n2,d1,d2,exp):
    #prev_scan = previewScan()
    
    create_prev = 'y'
    create_ptycho = 'y'
    run_prev = 'n'
    run_ptycho = 'n'
    
    stage = sample_lab_x_t1_pitch
    stage_x = sample_lab_x
    stage_y = t1_pitch

    # STXM MASK #
    width = 32
    height = 32
    centre = [256+32,256+32]
    stxm_mask_roi = (  ((centre[1] - (width/2)) , (centre[1] + (width/2)))  ,  ((centre[0] - (height/2)) , (centre[0] + (height/2)))  )
    
    centre[0] = stage_x.getPosition() * 1e-6
    centre[1] = stage_y.getPosition() * 1e-6

    typ = 'stxm'
    step = dnp.array([d1,d2])
    step = dnp.multiply(step._jdataset(),1e-6)
    sz = (int(n1),int(n2))
    
    
    positions = dnp.ones([2,(sz[0]*sz[1])])
    ### Generate grid ###
    count = 0
    for ii in range(0,sz[0]):
        for jj in range(0,sz[1]):
            positions[0,count] =  step[0] * ii
            if ii%2 != 1:
                positions[1,count] =  step[1] * jj # Negative on even and zero
            else:
                positions[1,count] = step[1] * (sz[1] - jj - 1)
            count += 1
    # Centre about 0,0
    positions[0,:] -= (dnp.amax(positions[0,:])/2)
    positions[1,:] -= (dnp.amax(positions[1,:])/2)
    
    dnp.plot.points(positions[0,:],positions[1,:],None,0,'Preview scan')
    
    imstack = dnp.zeros([1,sz[0],sz[1],5])
    

    detector_name = 'excalibur_config_normal'
    
    ### SETUP ###
    # From array to list of tuples
    pos_x = positions[0,:]
    pos_y = positions[1,:]
    
    pos_x *= 1e6
    pos_y *= 1e6
    pos_xy = []
    for i in range(0,pos_x.size): 
        pos_xy.append([pos_x[i],pos_y[i]])
    
    # Central coordinate in microns
    ctr = dnp.array(centre)
    ctr[0] *= 1e6
    ctr[1] *= 1e6
    
    two_motor_positions.offset = (ctr[0], ctr[1])
    two_motor_positions.values = pos_xy
    two_motor_positions.scale = 1.
    two_motor_positions.output_index=False
    
    ### RUN ###
    pos  expt_fastshutter "Open"
    scan stage two_motor_positions excalibur_config_normal exp
    pos  expt_fastshutter "Closed"
    
    num = i13jNumTracker.getCurrentFileNumber()
    nxs_path = '/dls/i13-1/data/2017/mt13529-1/raw/' + str(num) + '.nxs'
    
    f = dnp.io.load(nxs_path)
    tmp_path = 'entry1/instrument/'+ detector_name +'/data'
    dat = f[tmp_path]
    sm = stxm_mask_roi
    # STXM #
    tot = []
    com_x = []
    com_y = []
    stxm_bf = []
    
    # Quick image preview
    dnp.plot.image(dat[0,:,:], name="Full Frame Image")
    dnp.plot.image(dat[0,sm[0][0]:sm[0][1],sm[1][0]:sm[1][1]], name="Detector Image ROI")
    
    # STXM Images #
    for i in range(dat.shape[0]):
        print("Calculating for pixel %i" % (i))
        tot.append(int(dat[i,:,:].sum()))
        stxm_bf.append(int(dat[i,sm[0][0]:sm[0][1],sm[1][0]:sm[1][1]].sum()))
        com = dnp.centroid(dat[i,:,:])
        com_x.append(com[1])
        com_y.append(com[0])
        
    stxm = dnp.array(tot,dtype=dnp.float32)
    stxm_bf = dnp.array(stxm_bf,dtype=dnp.float32)
    com_x = dnp.array(com_x,dtype=dnp.float32)
    com_y = dnp.array(com_y,dtype=dnp.float32)
    
    stxm = dnp.reshape(stxm[::-1],[sz[0],sz[1]])
    stxm_bf = dnp.reshape(stxm_bf[::-1],[sz[0],sz[1]])
    com_x = dnp.reshape(com_x[::-1],[sz[0],sz[1]])
    com_y = dnp.reshape(com_y[::-1],[sz[0],sz[1]])
    
    ss = dnp.array(stxm)
    sbf = dnp.array(stxm_bf)
    com_xs = dnp.array(com_x)
    com_ys = dnp.array(com_y)
    
    count = 0
    for i in range(sz[0],0,-1):
        if count%2 != 1:
            ss[i-1,:] = stxm[i-1,::1]
            sbf[i-1,:] = stxm_bf[i-1,::1]
            com_xs[i-1,:] = com_x[i-1,::1]
            com_ys[i-1,:] = com_y[i-1,::1]
        else:
            ss[i-1,:] = stxm[i-1,::-1]
            sbf[i-1,:] = stxm_bf[i-1,::-1]
            com_xs[i-1,:] = com_x[i-1,::-1]
            com_ys[i-1,:] = com_y[i-1,::-1]
        count += 1
    
    stxm = ss[::-1,::-1]
    stxm_bf = sbf[::-1,::-1]
    stxm_df = stxm - stxm_bf
    
    stxm = dnp.swapaxes(stxm,0,1)
    stxm_bf = dnp.swapaxes(stxm_bf,0,1)
    stxm_df = dnp.swapaxes(stxm_df,0,1)
    
    dnp.plot.image(stxm,None,None,'Preview Image')
    dnp.plot.image(stxm_bf,None,None,'STXM_BF')
    dnp.plot.image(stxm_df,None,None,'STXM_DF')


class previewScan():
    '''### Probe properties, scan parameters, and preview image(s) ###
    '''
    def __init__(self):
        '''
        Constructor
        '''
        self.centre = [0,0] # Absolute scan position of scanning motors at centre of preview scan
        self.typ = 'stxm'
        self.step = dnp.array([1e-6,1e-6])
        self.sz = [40,40]
        self.exp = 0.01
        self.load_flag = 0 # Is the probe function imported from file
        self.path = 'blank' # Generate from experiment no
        self.positions = dnp.zeros([2,self.sz[0]*self.sz[1]]) # Relative scan positions about self.centre
        self.stxm = 0 # Preview image
        self.roi_point = [0,0] # roi from preview image
        self.roi_lengths = [0,0] # roi from preview image
        self.roi_centre = [0,0] # roi from preview image
        
        self.offs = [0.0,0.0]
        
        self.stage = sample_lab_x_t1_pitch
        self.stage_x = sample_lab_x
        self.stage_y = t1_pitch
        
        # STXM MASK #
        width = 32
        height = 32
        centre = [256+32,256+32]
        self.stxm_mask_roi = (  ((centre[1] - (width/2)) , (centre[1] + (width/2)))  ,  ((centre[0] - (height/2)) , (centre[0] + (height/2)))  )
        
        self.centre[0] = self.stage_x.getPosition() * 1e-6
        self.centre[1] = self.stage_y.getPosition() * 1e-6
    
    def populate(self):
        ''' Populate the parameters with user inputs '''
        self.typ = question('What type of scan?','str',self.typ,['stxm','com'])
        q = dnp.multiply(self.step._jdataset(),1e6)
        self.step = question('What step size? [microns]','tup',q,[0,1000])
        self.step = dnp.array(self.step)
        self.step = dnp.multiply(self.step._jdataset(),1e-6)
        self.sz = question('How many positions?','tup',self.sz,[0,1000])
        self.sz = (int(self.sz[0]),int(self.sz[1]))
        self.exp = question('What exposure time per position? [seconds]','num',self.exp,[0,1000])
    
    def create(self):
        '''### Generate scan coordinates ###
        '''
        print 'Creating scan positions..
        ### Create two columns for list of coordinates ###
        self.positions = dnp.ones([2,(self.sz[0]*self.sz[1])])
        ### Generate grid ###
        count = 0
        for ii in range(0,self.sz[0]):
            for jj in range(0,self.sz[1]):
                self.positions[0,count] =  self.step[0] * ii
                if ii%2 != 1:
                    self.positions[1,count] =  self.step[1] * jj # Negative on even and zero
                else:
                    self.positions[1,count] = self.step[1] * (self.sz[1] - jj - 1)
                count += 1
        # Centre about 0,0
        self.positions[0,:] -= (dnp.amax(self.positions[0,:])/2)
        self.positions[1,:] -= (dnp.amax(self.positions[1,:])/2)
        
    def clearROI(self,name):
        # Clear ROIs
        b = dpl.getbean(name)
        dpl.delrois(b,None,True,name)
        dpl.delroi(b,None,True,name)
        dpl.setbean(b)
    
    def getROI(self,name,typ):
        if typ == 'zoom':
            # Clear ROIs
            b = dpl.getbean(name)
            dpl.delrois(b,None,True,name)
            dpl.delroi(b,None,True,name)
            dpl.setbean(b)
            # Draw FOV
            fov = droi.rect()
            fov.name = "fov"
            self.sz = dnp.array(self.sz)
            
            fov.lengths = dnp.divide(self.sz._jdataset(),4)
            
            fov_lengths = fov.lengths[1]
            fov_lengths = dnp.array(fov.lengths)
            A = dnp.divide(self.sz._jdataset(),2)
            B = dnp.divide(fov_lengths._jdataset(),2)
            
            A[0] = int(A[0])
            A[1] = int(A[1])
            B[0] = int(B[0])
            B[1] = int(B[1])
            
            A = dnp.array(A,dnp.int32)
            B = dnp.array(B,dnp.int32)
            
            fov.point = A - B
            b = dpl.getbean(name)
            b = dpl.setroi(b,fov,True,name)
            dpl.setbean(b)
            # User feedback
            requestInput('Select a region of interest')
            b = dpl.getbean(name)
            roi = dpl.getrect(b)
            self.roi_point = roi.point
            self.roi_lengths = roi.lengths
            self.roi_centre[0] = self.roi_point[0] + (self.roi_lengths[0]/2)
            self.roi_centre[1] = self.roi_point[1] + (self.roi_lengths[1]/2)
            
            print 'ROI point',self.roi_point
            print 'ROI lengths',self.roi_lengths
            print 'ROI centre',self.roi_centre
        if typ == 'pan':
            # Clear ROIs
            b = dpl.getbean(name)
            dpl.delrois(b,None,True,name)
            dpl.delroi(b,None,True,name)
            dpl.setbean(b)
            # Draw FOV
            fov = droi.point()
            fov.name = "fov_centre"
            self.sz = dnp.array(self.sz)
            
            fov.point = dnp.divide(self.sz._jdataset(),2) # centre of current fov
            
            b = dpl.getbean(name)
            b = dpl.setroi(b,fov,True,name)
            dpl.setbean(b)
            # User feedback
            requestInput('Select a region of interest')
            b = dpl.getbean(name)
            
            roi = dpl.getroi(b)
            self.roi_point = roi.point
            self.roi_lengths = dnp.array(self.sz)
            self.roi_centre = self.roi_point
            
            self.roi_centre[0] = self.roi_point[0]
            self.roi_centre[1] = self.roi_point[1]
            
            print 'ROI point',self.roi_point
            print 'ROI centre',self.roi_centre
        
    def update(self):
        self.centre[0] += (self.roi_centre[0] - (self.sz[0]/2)) * self.step[0]
        self.centre[1] += (self.roi_centre[1] - (self.sz[1]/2)) * self.step[1]
        
        A = dnp.array(self.sz,dnp.int32)
        B = dnp.array(self.roi_lengths,dnp.int32)
        mag = dnp.divide(A,B)
        print 'mag=',mag
        A = dnp.array(self.step,dnp.float32)
        B = dnp.array(mag,dnp.float32)
        self.step = dnp.divide(A,B)
    
    def run(self):
        ''' Run the preview scan and return an image '''
        print 'Creating preview...'
        triggering = 'sw'
        if triggering == 'sw':
            # Execute the generation of a STXM image
            
            detector_name = 'excalibur_config_normal'
            #detector_name = 'merlin_sw_hdf'
            
            ### SETUP ###
            # From array to list of tuples
            pos_x = self.positions[0,:]
            pos_y = self.positions[1,:]
            
            pos_x *= 1e6
            pos_y *= 1e6
            pos_xy = []
            for i in range(0,pos_x.size): 
                pos_xy.append([pos_x[i],pos_y[i]])
            
            # Central coordinate in microns
            ctr = dnp.array(self.centre)
            ctr[0] *= 1e6
            ctr[1] *= 1e6
            
            two_motor_positions.offset = (ctr[0], ctr[1])
            two_motor_positions.values = pos_xy
            two_motor_positions.scale = 1.
            two_motor_positions.output_index=False
            
            exptime = self.exp
            
            ### RUN ###
            pos  expt_fastshutter "Open"
            scan self.stage two_motor_positions excalibur_config_normal exptime
            pos  expt_fastshutter "Closed"
            
            num = i13jNumTracker.getCurrentFileNumber()
            self.nxs_path = '/dls/i13-1/data/2017/mt13529-1/raw/' + str(num) + '.nxs'
            
        elif triggering == 'hw':
            ctr = dnp.array(self.centre)
            ctr[0] *= 1e6
            ctr[1] *= 1e6
            self.stage_x.moveTo(ctr[0])
            self.stage_y.moveTo(ctr[1])
            self.nxs_path = stxmScan_HW(self.sz[0],self.sz[1],self.step[0],self.step[1],self.exp,"merlin")
        
        print self.nxs_path
        # Create STXM
        if triggering == 'sw':
            f = dnp.io.load(self.nxs_path)
            tmp_path = 'entry1/instrument/'+ detector_name +'/data'
            dat = f[tmp_path]
            sm = self.stxm_mask_roi
            # STXM #
            tot = []
            com_x = []
            com_y = []
            stxm_bf = []
            
            # Quick image preview
            dnp.plot.image(dat[0,:,:], name="Full Frame Image")
            dnp.plot.image(dat[0,sm[0][0]:sm[0][1],sm[1][0]:sm[1][1]], name="Detector Image ROI")
            
            # STXM Images #
            for i in range(dat.shape[0]):
                print("Calculating for pixel %i" % (i))
                tot.append(int(dat[i,:,:].sum()))
                stxm_bf.append(int(dat[i,sm[0][0]:sm[0][1],sm[1][0]:sm[1][1]].sum()))
                com = dnp.centroid(dat[i,:,:])
                com_x.append(com[1])
                com_y.append(com[0])
                
            stxm = dnp.array(tot,dtype=dnp.float32)
            stxm_bf = dnp.array(stxm_bf,dtype=dnp.float32)
            com_x = dnp.array(com_x,dtype=dnp.float32)
            com_y = dnp.array(com_y,dtype=dnp.float32)
            
            stxm = dnp.reshape(stxm[::-1],[self.sz[0],self.sz[1]])
            stxm_bf = dnp.reshape(stxm_bf[::-1],[self.sz[0],self.sz[1]])
            com_x = dnp.reshape(com_x[::-1],[self.sz[0],self.sz[1]])
            com_y = dnp.reshape(com_y[::-1],[self.sz[0],self.sz[1]])
            
            ss = dnp.array(stxm)
            sbf = dnp.array(stxm_bf)
            com_xs = dnp.array(com_x)
            com_ys = dnp.array(com_y)
            
            count = 0
            for i in range(self.sz[0],0,-1):
                if count%2 != 1:
                    ss[i-1,:] = stxm[i-1,::1]
                    sbf[i-1,:] = stxm_bf[i-1,::1]
                    com_xs[i-1,:] = com_x[i-1,::1]
                    com_ys[i-1,:] = com_y[i-1,::1]
                else:
                    ss[i-1,:] = stxm[i-1,::-1]
                    sbf[i-1,:] = stxm_bf[i-1,::-1]
                    com_xs[i-1,:] = com_x[i-1,::-1]
                    com_ys[i-1,:] = com_y[i-1,::-1]
                count += 1
            
            self.stxm = ss[::-1,::-1]
            self.com_x = com_xs[::-1,::-1]
            self.com_y = com_ys[::-1,::-1]
            self.stxm_bf = sbf[::-1,::-1]
            self.stxm_df = self.stxm - self.stxm_bf
            
            self.stxm = dnp.swapaxes(self.stxm,0,1)
            self.com_x = dnp.swapaxes(self.com_x,0,1)
            self.com_y = dnp.swapaxes(self.com_y,0,1)
            self.stxm_bf = dnp.swapaxes(self.stxm_bf,0,1)
            self.stxm_df = dnp.swapaxes(self.stxm_df,0,1)
        elif triggering == 'hw':
            f = dnp.io.load(self.nxs_path)
            tmp_path = '_entry_data_data'
            dat = f[tmp_path]
            
            roi_tl = [3,3]
            roi_br = [6,6]
            
            # STXM #
            tot = []
            bf = []
            
            # Quick image preview
            dnp.plot.image(dat[0,:,:], name="Full Frame Image")
            
            # STXM Images #
            for i in range(dat.shape[0]):
                print("Calculating for pixel %i" % (i))
                tot.append(int(dat[i,:,:].sum()))
                bf.append(int(dat[i,roi_tl[0]:roi_tl[1],roi_br[0]:roi_br[1]].sum()))
                
            stxm = dnp.array(tot,dtype=dnp.float32)
            bf = dnp.array(bf,dtype=dnp.float32)
            
            stxm = dnp.reshape(stxm[::-1],[self.sz[0],self.sz[1]])
            bf = dnp.reshape(bf[::-1],[self.sz[0],self.sz[1]])
            
            ss = dnp.array(stxm)
            sbf = dnp.array(bf)
            
            count = 0
            for i in range(self.sz[0],0,-1):
                if count%2 != 1:
                    ss[i-1,:] = stxm[i-1,::1]
                    sbf[i-1,:] = bf[i-1,::1]
                else:
                    ss[i-1,:] = stxm[i-1,::-1]
                    sbf[i-1,:] = bf[i-1,::-1]
                count += 1
            
            self.stxm = ss[::-1,::-1]
            self.stxm_bf = sbf[::-1,::-1]
            self.stxm_df = self.stxm - self.stxm_bf
            
            self.stxm = dnp.swapaxes(self.stxm,0,1)
            self.stxm_bf = dnp.swapaxes(self.stxm_bf,0,1)
            self.stxm_df = dnp.swapaxes(self.stxm_df,0,1)
            
    def load(self,ID):
        print 'Loading preview scan..'
    
    def save(self):
        print 'Saving preview scan, parameters and images..'
#         filename = gen.base_dir + '/' + gen.save_dir + '/' + gen.save_file + '.hdf'
#         print filename
#         # open the HDF5 CXI file for writing
#         f = h5py.File(filename, "w")
    
    def create_file(self):
        print 'Creating preview scan parameter file..'
    
    def dispParams(self):
            # Display parameters
        print '\n'
        print '### Preview scan parameters ###'
        print 'Scan type ---------------------', self.typ
        print 'Scan size ---------------------', self.sz
        print 'Step size ---------------------', self.step
        print 'Scan centre -------------------', self.centre
        print 'Exposure time -----------------', self.exp
        print '###############################'
    
#     def addmeta(self):
# #         self.centre = [0,0] # Absolute scan position of scanning motors at centre of preview scan
# #         self.typ = 'stxm'
# #         self.step = dnp.array([9e-6,9e-6])
# #         self.sz = [20,20]
# #         self.exp = 0.1
# #         self.load_flag = 0 # Is the probe function imported from file
# #         self.path = 'blank' # Generate from experiment no
# #         self.positions = dnp.zeros([2,self.sz[0]*self.sz[1]]) # Relative scan positions about self.centre
# #         self.stxm = 0 # Preview image
# #         self.roi_point = [0,0] # roi from preview image
# #         self.roi_lengths = [0,0] # roi from preview image
# #         self.roi_centre = [0,0] # roi from preview image
#         
#         
#         
#         centre_list = []
#         for i in self.centre:
#             centre_list.append(i)
#         meta_add("scan_centre", self.centre)
#         meta_add("scan_type", self.typ)
#         meta_add("scan_step", self.step)
#         meta_add("scan_size", self.sz)
#         meta_add("scan_exposure", self.exp)
#         meta_add("scan_load_flag", self.load_flag)
#         stxm_list =[]
#         for x in self.stxm:
#             stxm_lst.append(x[0])
#         meta_add("scan_stxm", stxm_list)
#         
#         scan_path = pwd()
#         scan_path_split = scan_path.split('/')
#         prev_path = ''
#         for pc in scan_path_split:
#             if pc != 'raw' and pc != '':
#                 prev_path += os.sep + pc
#         (head, tail)=os.path.split(prev_path)
#         prev_path = head + os.sep + 'processing' + os.sep + 'ptycho_preview'
#         #meta_add("scan_stxm1", "/dls/i13-1/data/2014/cm4965-5/processing/ptycho_preview/filename.ext")
#         meta_add("scan_stxm1", prev_path + os.sep + "filename.ext")
#         
#         
#         
#         #example how to save file
#         #d3=dnp.array(d2)
#         #dnp.io.save("/scratch/dimax2_sum.tiff", d3, format="tiff", signed=False, bits=32)

class ptychoScan():
    def __init__(self):
        '''
        Constructor
        '''
        self.typ = 'snake' #1-rect/2-spiral
        self.sz = [10,10] # Number of positions
        self.step = dnp.array([2e-6,2e-6]) # Nominal step size
        self.offs = [0.4,0.4] # Random offsets (+/-)self.offs = [0.4,0.4] # Random offsets (+/-)
        self.centre = [0,0]
        self.exp = 1 # Exposure per position in seconds
        self.rot = 0 # rotation of positions in deg cc
        self.orientation = '10' # Flip directions (00'/'01'/'10'/'11')
        self.scale = [1,1]
        self.xy = 'xy' # ('xy'/'yx') (x->/y|^)
        self.positions = dnp.zeros([2,self.sz[0]*self.sz[1]])
        self.stxm = 0 # Preview image
        self.path = 'blank' # Generate from experiment no
        self.roi = 0 # roi from preview image
        self.roi_point = [0,0] # roi from preview image
        self.roi_lengths = [0,0] # roi from preview image
        self.roi_centre = [0,0] # roi from preview image
        self.max_n = 2048#self.sz[0]*self.sz[1] # max number of position in any single nxs file
    
    def populate(self,prev_scan):
        ''' Populate the parameters with user in '''
        self.typ = question('What type of scan?','str',self.typ,['snake','rect','spiral'])
        self.step = question('What step size? [microns]','tup',dnp.multiply(self.step._jdataset(),1e6),[0,1000])
#         self.step = list(self.step)
        self.step = dnp.array(self.step)
        self.step = dnp.multiply(self.step._jdataset(),1e-6)
        self.exp = question('What exposure time per position? [seconds]','num',self.exp,[0,1000])
        if prev_scan.have_prev == True:
            scan_ok = 'n'
            while scan_ok == 'n':
                self.getROI("Preview Image")
                # New Centre
                self.centre[0] += ((self.roi_point[0] + (self.roi_lengths[0]/2)) - (prev_scan.sz[0]/2)) * prev_scan.step[0]
                self.centre[1] += ((self.roi_point[1] + (self.roi_lengths[1]/2)) - (prev_scan.sz[1]/2)) * prev_scan.step[1]
                
                prev_scan.dispParams()
                prev_scan.create()
                
                print self.sz
                
                self.sz[0] = (self.roi_lengths[0] * prev_scan.step[0])/self.step[0]
                self.sz[1] = (self.roi_lengths[1] * prev_scan.step[1])/self.step[1]
#                 self.rot = self.roi.angle
                self.sz = dnp.array(self.sz,dnp.int32)
                self.sz = dnp.ceil(self.sz)
                self.sz = dnp.array(self.sz,dnp.int32)
                
                scan_ok = question('Number of scan positions = [%d,%d] - Proceed?' %(self.sz[0],self.sz[1]),'str','y',['y','n'])
        else:
            self.sz = question('How many positions?','tup',self.sz,[0,1000])
            print self.sz
            self.sz = (int(self.sz[0]),int(self.sz[1]))
    
    def create(self):
        ''' Generate scan coordinates and export as a csv list '''
        print 'Creating scan positions..'
        if self.typ == 'snake': # Snake
            ### Create two columns for list of coordinates ###
            self.positions = dnp.ones([2,(self.sz[0]*self.sz[1])])
            ### Generate grid ###
            count = 0
            for ii in range(0,self.sz[0]):
                for jj in range(0,self.sz[1]):
                    self.positions[0,count] =  self.step[0] * ii
                    if ii%2 != 1:
                        self.positions[1,count] =  self.step[1] * jj # Negative on even and zero
                    else:
                        self.positions[1,count] = self.step[1] * (self.sz[1] - jj - 1)
                    count += 1
            # Centre about 0,0
            self.positions[0,:] -= (dnp.amax(self.positions[0,:])/2)
            self.positions[1,:] -= (dnp.amax(self.positions[1,:])/2)
            ### Create two columns of random offsets ###
            tmp = drd.rand(2,(self.sz[0]*self.sz[1])) - 0.5
            ### Apply random offsets ###
            self.positions[0,:] += tmp[0,:]*self.step[0]*self.offs[0]
            self.positions[1,:] += tmp[1,:]*self.step[1]*self.offs[1]
        elif self.typ == 'rect': # Rect
            ### Create two columns for list of coordinates ###
            self.positions = dnp.ones([2,(self.sz[0]*self.sz[1])])
            ### Generate grid ###
            count = 0
            for ii in range(0,self.sz[0]):
                for jj in range(0,self.sz[1]):
                    self.positions[0,count] =  self.step[0] * ii
                    self.positions[1,count] =  self.step[1] * jj
                    count += 1
            # Centre about 0,0
            self.positions[0,:] -= (dnp.amax(self.positions[0,:])/2)
            self.positions[1,:] -= (dnp.amax(self.positions[1,:])/2)
            ### Create two columns of random offsets ###
            tmp = drd.rand(2,(self.sz[0]*self.sz[1])) - 0.5
            ### Apply random offsets ###
            self.positions[0,:] += tmp[0,:]*self.step[0]*self.offs[0]
            self.positions[1,:] += tmp[1,:]*self.step[1]*self.offs[1]
        elif self.typ == 'spiral': # Spiral
            None
#         self.positions[0] += self.centre[0]
#         self.positions[1] += self.centre[1]
    
    def load(self,ID):
        ''' Import the scan positions '''
        print 'Loading ptychography scan..'
        # Load scan parameters and positions from previous nxs file
#         f = h5py.File(path,'r')
#         pos_x = f['entry1/merlin_sw_hdf_nochunking/t1_sx']
#         pos_y = f['entry1/merlin_sw_hdf_nochunking/t1_sy']
#         pos_x = dnp.squeeze(pos_x)
#         pos_y = dnp.squeeze(pos_y)
#         pos = dnp.ones([256,2])
#         f.close()
#         # Stage positions
#         if self.orientation == '01':
#             pos[:,1] = pos_x[:]
#             pos[:,0] = -1*pos_y[:]
#         elif self.orientation == '10':
#             pos[:,0] = -1*pos_x[:]
#             pos[:,1] = pos_y[:]
#         elif self.orientation == '11':
#             pos[:,1] = pos_x[:]
#             pos[:,0] = pos_y[:]
#         else:
#             pos[:,1] = -1*pos_x[:]
#             pos[:,0] = -1*pos_y[:]
        # Position rotation
#         rot = -1*self.rot *dnp.pi/180 # Convert to radians cc
#         rot_mat = dnp.matrix([[dnp.cos(rot),-1*dnp.sin(rot)],[dnp.sin(rot),np.cos(rot)]])
#         for loop in range(dnp.size(pos,0)):
#             pos[loop,:] = dnp.dot(dnp.mat(pos[loop,:]),rot_mat)
#         # Probe positions
#         pos *= -1
#         # Positions in metres
#         pos *= 1e-6
#         self.positions = pos
    
    def save(self):
        print 'Saving ptychography scan..'
        # Save experimental parameters, ptycho scan parameters and positions, and preview scan parameters and image(s).
    
    def create_file(self):
        print 'Creating ptychography scan parameter file..'
    
    def run(self):
        ''' Run scan and return ptyhographic dataset '''
        print 'Collecting data...'
        # Execute the collection of ptychography data
        ### SETUP ###
        # From array to list of tuples
        x = self.positions[0,:]
        y = self.positions[1,:]
        pos_x = x
        pos_y = y
        pos_x *= 1e6
        pos_y *= 1e6
        
        pos_xy = []
        for i in range(0,pos_x.size): 
            pos_xy.append([pos_x[i],pos_y[i]])
        
        # Central coordinate in microns
        ctr = dnp.array(self.centre)
        ctr[0] *= 1e6
        ctr[1] *= 1e6

        loop = dnp.arange(0,(pos_x.size/self.max_n),1)
        pos  expt_fastshutter "Open"

        #for offset in loop:
            #print 'offset is ' + str(offset)
            #start = offset * self.max_n
        two_motor_positions.offset = (ctr[0], ctr[1])
        two_motor_positions.values = pos_xy#[start:start+self.max_n]
        two_motor_positions.scale = 1.
        two_motor_positions.output_index=False
        exptime = self.exp
        '''
        while ion_current < value:
            time.sleep(1)
        '''
        #topupMonitor.setCollectionTime(self.exp)
        #topupMonitor.collectionTime
        ### RUN ###
        n = 2
        range_theta = 180.0
        dTheta = range_theta / n
        start_theta = -90.0
        
        
        print start_theta
        print range_theta
        print dTheta
        
        print dnp.arange(start_theta, start_theta + range_theta + 1, dTheta)
        
        
        for theta in dnp.arange(start_theta, start_theta + range_theta + 1, dTheta):
            pos t1_theta theta
            scan sample_lab_xy two_motor_positions merlin_sw_hdf exptime #beamok #topupMonitor
        
        #scan sample_lab_xy two_motor_positions merlin_sw_hdf exptime
            
            
            
        #for inc in range(0,7):
        '''
        for s1_slit in [0.025,0.05,0.075,1.0]:
            print s1_slit
            for inc in range(0,4):
                
                #exptime = 0.25*(2^inc)
                #exptime = 0.25*pow(2,inc)
                pos s1_xsize s1_slit
                exptime = 0.5*pow(2,inc)
                print inc
                print exptime
        
                #scan t1_sxy two_motor_positions excalibur_config_normal exptime beamok #topupMonitor
                scan t1_sxy two_motor_positions merlin_sw_hdf exptime beamok 
        #scan diff_xy two_motor_positions excalibur_config_normal exptime
        #scan diff_xz two_motor_positions merlin_sw_hdf exptime
        '''
        
        
        #scan t1_sxy two_motor_positions excalibur_config_normal exptime #xmapMca exptime beamok
        self.nxs_path = pwd() + '.nxs'
        print self.nxs_path
        pos  expt_fastshutter "Closed"
        print 'Full scan complete.'
    
    def clearROI(self,name):
        # Clear ROIs
        b = dpl.getbean(name)
        dpl.delrois(b,None,True,name)
        dpl.delroi(b,None,True,name)
        dpl.setbean(b)
    
    def getROI(self,name):
        # Clear ROIs
        b = dpl.getbean(name)
        dpl.delrois(b,None,True,name)
        dpl.delroi(b,None,True,name)
        dpl.setbean(b)
        # Draw FOV
        prev_sz = self.stxm.shape
        fov = droi.rect()
        fov.name = "fov"
        prev_sz = dnp.array(prev_sz,dnp.int32)
        fov.lengths = dnp.divide(prev_sz._jdataset(),4)
        fov_lengths = fov.lengths[1]
        fov_lengths = dnp.array(fov.lengths)
        fov.point = dnp.divide(prev_sz._jdataset(),2) - dnp.divide(fov_lengths._jdataset(),2)
        b = dpl.getbean(name)
        b = dpl.setroi(b,fov,True,name)
        dpl.setbean(b)
        # Draw points
        
        # Draw probe shape and size
        requestInput('Select a region of interest')
        b = dpl.getbean(name)
#         self.roi = dpl.getrect(b)
        roi = dpl.getrect(b)
        self.roi_point = roi.point
        self.roi_lengths = roi.lengths
        self.roi_centre[0] = self.roi_point[0] + (self.roi_lengths[0]/2)
        self.roi_centre[1] = self.roi_point[1] + (self.roi_lengths[1]/2)
        
        print 'ROI point',self.roi_point
        print 'ROI lengths',self.roi_lengths
        print 'ROI centre',self.roi_centre
    
    def dispParams(self):
            # Display parameters
        print '\n'
        print '### Ptychography scan parameters ###'
        print 'Scan type --------------------------', self.typ
        print 'Scan size --------------------------', self.sz
        print 'Step size --------------------------', self.step
        print 'Scan centre ------------------------', self.centre
        print 'Exposure time ----------------------', self.exp
        print '####################################'

def collectData():
    ### Preview scan ###
    prev_scan = previewScan()
    ptycho_scan = ptychoScan()
    
    prev_no = 0
    
    create_prev = 'y'
    create_ptycho = 'y'
    run_prev = 'n'
    run_ptycho = 'n'
    prev_scan.have_prev = False
    
    #ask_question = 0
    #if ask_question
    
    while create_prev != 'n':
        create_prev = question('Create a preview scan?','str','y',['y','n','l']) # Default = blank return / l = load previous params
          
        if create_prev == 'y':
            # Open windows
            #dnp.plot.window_manager.open_view('Preview Image')
            #dpl.window_manager.open_view(view_name='Preview Image')
            #dpl.window_manager.open_view(view_name='STXM_BF')
            #dpl.window_manager.open_view(view_name='STXM_DF')
            #dpl.window_manager.open_view(view_name='COM_X')
            #dpl.window_manager.open_view(view_name='COM_Y')
            prev_scan.populate()
            prev_scan.create()
            dnp.plot.points(prev_scan.positions[0,:],prev_scan.positions[1,:],None,0,'Preview scan')
         
        if create_prev == 'l':
            prev_ID = question('Enter datasetID','num',00000,None)
            prev_scan = previewScan()
            prev_scan.load(prev_ID)
            dnp.plot.points(prev_scan.positions[0,:],prev_scan.positions[1,:],None,0,'Preview scan')
         
        if create_prev != 'n':
            prev_scan.dispParams()
            run_prev = question('Run this preview scan?','str','y',['y','n'])
            if run_prev == 'y':
                create_prev = 'n'
    
    prev_scan.imstack = dnp.zeros([1,prev_scan.sz[0],prev_scan.sz[1],5])
    while run_prev != 'n':
#         prev_scan.addmeta()
        prev_scan.run()
        prev_no += 1
        prev_scan.have_prev = True
        dnp.plot.image(prev_scan.stxm,None,None,'Preview Image')
        dnp.plot.image(prev_scan.stxm_bf,None,None,'STXM_BF')
        dnp.plot.image(prev_scan.stxm_df,None,None,'STXM_DF')
        #dnp.plot.image(prev_scan.com_x,None,None,'COM_X')
        #dnp.plot.image(prev_scan.com_y,None,None,'COM_Y')
        
        '''
        edit = question('Change view?','str','n',['n','z','p'])
        if edit == 'z':
            prev_scan.getROI('Preview Image','zoom')
            prev_scan.update()
            prev_scan.dispParams()
            prev_scan.create()
        if edit == 'p':
            prev_scan.getROI('Preview Image','pan')
            prev_scan.update()
            prev_scan.dispParams()
            prev_scan.create()
        if edit == 'n':
            run_prev = 'n'
        print prev_scan.imstack.shape
        print prev_scan.stxm.shape
        # Place preview images into stack for saving later
        prev_scan.imstack[prev_no-1,:,:,0] = prev_scan.stxm
        prev_scan.imstack[prev_no-1,:,:,1] = prev_scan.stxm_bf
        prev_scan.imstack[prev_no-1,:,:,2] = prev_scan.stxm_df
        #prev_scan.imstack[prev_no-1,:,:,3] = prev_scan.com_x
        #prev_scan.imstack[prev_no-1,:,:,4] = prev_scan.com_y
        '''
        
### Ptychography scan ###
    while create_ptycho != 'n':
        create_ptycho = question('Create a ptychographic scan from this region?','str','y',['y','n','l'])
        if create_ptycho == 'y':
            prev_scan.save() # Save the preview parameters and image
            ptycho_scan.stxm = prev_scan.stxm # Transfer preview image to ptycho scan
            ptycho_scan.centre = prev_scan.centre
            ptycho_scan.populate(prev_scan)
            
            ptycho_scan.create()
            #dnp.plot.window_manager.open_view('Ptycho scan')
            dnp.plot.points(ptycho_scan.positions[0,:],ptycho_scan.positions[1,:],None,0,'Ptycho scan')
            ptycho_scan.dispParams()
#          
        if create_ptycho == 'l':
            ptycho_ID = question('Enter datasetID','num',25232,None)
            ptycho_scan.load(ptycho_ID)
#             dnp.plot.window_manager.open_view('Ptycho scan')
            dnp.plot.points(ptycho_scan.positions[0,:],ptycho_scan.positions[1,:],None,0,'Ptycho scan')
#          
        run_ptycho = question('Run this ptychographic scan?','str','y',['y','n'])
        if run_ptycho == 'y':
            create_ptycho = 'n'
            ptycho_scan.run()
            #save(prev_scan,ptycho_scan)

print "Ptycho data collection ready."