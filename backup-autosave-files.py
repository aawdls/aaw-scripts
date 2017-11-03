#!/dls_sw/prod/tools/RHEL6-x86_64/defaults/bin/dls-python
# Script to back up latest autosave files for a beamline

import os, shutil, time, re, sys

class AutosaveBackup:
    """@class AutosaveBackup
    @brief Back up most recent autosave files for a beamline
    @description We assume the latest files are those called XXX_0.sav, XXX_1.sav and XXX_2.sav without any suffix.
    """
    
    def isAnIoc(self, inputStr):
        """Check string looks like an ioc BLXXX-XX-IOC-XX
        @param inputStr String to chceck"""
        iocDirectoryPattern = r"^BL[0-9]{2}[BCIJ]-[A-Z]{2}-IOC-[0-9]{2}$"
        matches = re.match(iocDirectoryPattern, inputStr)
        if matches is not None:
            return True
        else:
            return False

    def scanSourceDirs(self):
        """Scan all directories in source directory, and return a list of subdirectories having IOC names
        @return List of subdirectories which look like IOCs"""
        lastDirectoryPattern = r"\S+/(\S+)$"
        
        directories = os.listdir(self.autosaveTop)
        
        print "Directories:"
        
        dirsToSearch = list()
        
        for onedir in directories:
            print onedir,
            if self.isAnIoc(onedir):
                currentdir = onedir
                print "looks like an IOC dir"
                dirsToSearch.append(currentdir)
            else:
                print "doesn't look like an IOC dir. Skipping."
                
        return dirsToSearch
        
    def findLatestFilesIn(self, targetDir):
        """Find the latest files in targetDir, assuming they have the the form ...XXX_0.sav to ...XXX_2.sav
        @param targetDir Directory to search
        @return latestFiles A list of the latest files in targetDir"""
        latestFilePattern = r".+_[0-2]\.sav$"
        latestFiles = list()
        
        print targetDir
        
        files = os.listdir(os.path.join(self.autosaveTop, targetDir))
        
        for thisFile in files:
            matches = re.match(latestFilePattern, thisFile)
            
            if (matches is not None):

                fileToBackUp = thisFile
                print " ", thisFile
                latestFiles.append(fileToBackUp)
                
        return latestFiles
        
    def createBackupSubdir(self, subdir):
        """Create an IOC subdirectory in the backup target directory
        @param subdir Subdirectory name"""
        # cd to backup directory
        os.chdir(self.backupTarget)
        
        # Create a directory with date and time
        print "Create subdirectory {0} in {1}".format(subdir, self.backupTarget)
        
        os.mkdir(subdir)
        
    def createBackupDir(self):
        """Create a new directory with date and time which will be the taret for the backup files"""
        # cd to backup top level
        os.chdir(self.backupTop)
        
        # Check new directory doesn't already exist
        if os.path.exists(self.newDirectory):
            print "New directory {0} in {1} already exists. Exiting.".format(self.newDirectory, self.backupTop)
            sys.exit()
        else:
            print "Creating target directory {0} in {1}".format(self.newDirectory, self.backupTop)
            os.mkdir(self.newDirectory)
        
    def startBackup(self):
        """Begin the backup. To be called after all setup is has been done."""
        for subdir in self.backupFileList:

            # Create backup directory for this IOC
            self.createBackupSubdir(subdir)

            # Copy files across individually
            for fileToBackUp in self.backupFileList[subdir]:
                
                sourcepath = os.path.join(self.autosaveTop,subdir,fileToBackUp)
                destpath = os.path.join(self.backupTarget,subdir)
                print "Copy {0} to {1} .".format(sourcepath, destpath)
                # Copy file and metadata
                shutil.copy2(sourcepath, destpath)
        
        
    def __init__(self, bl, whichIocs):
        """@param bl Beamline in IT notation e.g. i13 i13-1
        @param whichIoc IOC name eg BL13I-EA-IOC-03"""
        self.bl = bl
        self.whichIocs = whichIocs

        # Key paths
        self.autosaveTop = "/dls_sw/{0}/epics/autosave".format(self.bl)
        self.backupTop = "/home/tdq39642/autosave_backup/{0}".format(self.bl)
        
        # Name for new backup subdirectory
        self.newDirectory = "autosave_backup_{0}".format(time.strftime("%Y-%m-%d_%H%M%S"))
        self.backupTarget = os.path.join(self.backupTop, self.newDirectory)
        
        # Check source and destination paths are OK
        if not os.path.exists(self.autosaveTop):
            print "Source directory for autosave does not seem to exist: {0}".format(self.autosaveTop)
            sys.exit()
        if not os.path.exists(self.backupTop):
            print "Target top level directory for backing up files does not seem to exist: {0}".format(self.backupTop)
            sys.exit()
            
        # Check "which IOC" argument is valid
        for given_argument in self.whichIocs:
            if not self.isAnIoc(given_argument):
                if not (self.whichIocs[0] == "all"):
                    self.printUsage()
                    sys.exit()
        
        # Make the user check details before proceeding
        print "We will back up the latest autosave files for {0}, ioc:".format(self.bl)
        print self.whichIocs
        print " from {0}".format(self.autosaveTop)
        print " to {0}".format(self.backupTarget)
        user = raw_input( "Is this right? (y/n) " )
        
        # Drop out of not "y" or "yes"
        matches = re.match(r"^y", user)
        if (matches is None):
            print "Exiting."
            sys.exit()
        
        # Create target directory for backup
        self.createBackupDir()
        
        # Initialise the list of files we will want to back up
        self.backupFileList = dict()
        
        # If "all": list contents of top-level directory
        if (self.whichIocs[0] == "all"):
            dirsToSearch = self.scanSourceDirs()
                    
            if (dirsToSearch is None or len(dirsToSearch) == 0):
                print "Couldn't find any autosave directories in the source path."
                sys.exit()
        else:
            # Otherwise just search for given IOCs
            dirsToSearch = self.whichIocs
            
        print "\nLooking for files..."
        for onedir in dirsToSearch:
            self.backupFileList[onedir] = self.findLatestFilesIn(onedir)
            if ( len(self.backupFileList[onedir]) == 0):
                print "Warning: no files found for {0}.".format(onedir)
                
        print "\nStarting backup..."
        self.startBackup()

                
        print "\nFinished. Backup created in {0} .".format(self.backupTarget)
    
    @staticmethod       
    def printUsage():
        print "  "
        print "  Back up the latest autosave files for an IOC or all IOCs on a beamline."
        print "  We assume the latest files are those called XXX_0.sav, XXX_1.sav and XXX_2.sav without any suffix."
        print "  Usage:"
        print "  - backup-autosave-files.py <beamline> <ioc name>"
        print "  - backup-autosave-files.py <beamline> all"
        print "\n  Example:"
        print "  - backup-autosave-files.py i13 BL13I-EA-IOC-03"
        print "  "
        
    

    
if __name__ == "__main__":
    if (len(sys.argv) < 3):
        AutosaveBackup.printUsage()
        sys.exit()
        
    # First argument: beamline name
    bl = sys.argv[1]
    
    # Second argument: IOC name or "all"
    whichIocs = sys.argv[2:]
    
    a = AutosaveBackup(bl, whichIocs)