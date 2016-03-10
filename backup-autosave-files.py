#!/dls_sw/prod/tools/RHEL6-x86_64/defaults/bin/dls-python
# Script to back up latest autosave files for a beamline

import os, shutil, time, re, sys

class AutosaveBackup:
    
    def isAnIoc(self, inputStr):
        iocDirectoryPattern = r"^BL[0-9]{2}[IJ]-[A-Z]{2}-IOC-[0-9]{2}$"
        matches = re.match(iocDirectoryPattern, inputStr)
        if matches is not None:
            return True
        else:
            return False

    def scanSourceDirs(self):
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
                print "doesn't look like an IOC dir."
                
        return dirsToSearch
        
    def findLatestFilesIn(self, targetDir):
        # Want a pattern ".....01_0.sav"
        #                ".....01_1.sav"
        #                ".....01_2.sav"
        latestFilePattern = r".+[0-9]{2}_[0-2]\.sav$"
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
        # cd to backup directory
        os.chdir(self.backupTarget)
        
        # Create a directory with date and time
        print "Create subdirectory {0} in {1}".format(subdir, self.backupTarget)
        
        os.mkdir(subdir)
        
    def createBackupDir(self):
        # cd to backup top level
        os.chdir(self.backupTop)
        
        # Check new directory doesn't already exist
        if os.path.exists(self.newDirectory):
            print "New directory {0} in {1} already exists. Exiting.".format(self.newDirectory, self.backupTop)
            sys.exit()
        else:
            print "New directory {0} in {1} doesn't already exist: OK to create it".format(self.newDirectory, self.backupTop)
            os.mkdir(self.newDirectory)
        
    def __init__(self, bl, whichIoc):
        self.bl = bl
        self.whichIoc = whichIoc

        self.autosaveTop = "/home/tdq39642/tmp/autosave-for-testing/"
        self.backupTop = "/home/tdq39642/tmp/autosave_backup/{0}".format(self.bl)
        
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
            
        # Check which IOC is valid
        if not self.isAnIoc(self.whichIoc):
            if not (self.whichIoc == "all"):
                self.printUsage()
                sys.exit()
            
        print "We will back up the latest autosave files for {0}, ioc {1}".format(self.bl, self.whichIoc)
        print " from {0}".format(self.autosaveTop)
        print " to {0}".format(self.backupTarget)
        user = raw_input( "Is this right? (y/n) " )
        
        matches = re.match(r"^y", user)
        
        if (matches is None):
            print "Exiting."
            sys.exit()
        
        
        self.createBackupDir()
        
        # Initialise the list of files we will want to back up
        self.backupFileList = dict()
        
        # List contents of top-level directory
        dirsToSearch = self.scanSourceDirs()
                
        if (dirsToSearch is None or len(dirsToSearch) == 0):
            print "Couldn't find any autosave directories in the source path."
            sys.exit()
            
        print "\nLooking for files..."
        for onedir in dirsToSearch:
            self.backupFileList[onedir] = self.findLatestFilesIn(onedir)
                
        print "\nList of files we will back up:"
        for subdir in self.backupFileList:
            
            self.createBackupSubdir(subdir)
            
            
            for fileToBackUp in self.backupFileList[subdir]:
                
                sourcepath = os.path.join(self.autosaveTop,subdir,fileToBackUp)
                destpath = os.path.join(self.backupTarget,subdir)
                print "Copy {0} to {1} .".format(sourcepath, destpath)
                shutil.copy2(sourcepath, destpath)
    
    @staticmethod       
    def printUsage():
        print "Usage:"
        print "backup-autosave-files.py <bl> <ioc> [<more iocs>]"
        print "backup-autosave-files.py <bl> all"
        
    

    
if __name__ == "__main__":
    if (len(sys.argv) < 3):
        AutosaveBackup.printUsage()
        sys.exit()
        
    bl = sys.argv[1]
    
    whichIoc = sys.argv[2]
    
    a = AutosaveBackup(bl, whichIoc)