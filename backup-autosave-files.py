#!/dls_sw/prod/tools/RHEL6-x86_64/defaults/bin/dls-python
# Script to back up latest autosave files for a beamline

import os, shutil, time, re, sys

class AutosaveBackup:
    
    def scanSourceDirs(self):
        lastDirectoryPattern = r"\S+/(\S+)$"
        iocDirectoryPattern = r"BL[0-9]{2}[IJ]-[A-Z]{2}-IOC-[0-9]{2}"
        
        directories = os.listdir(self.autosaveTop)
        
        print "Directories:"
        
        dirsToSearch = list()
        
        for onedir in directories:
            print onedir,
            dirmatches = re.match(iocDirectoryPattern, onedir)
            if dirmatches is not None:
                currentdir = dirmatches.group(0)
                print "looks like dir for", currentdir
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
        
    def __init__(self):
        self.bl = "i13"

        self.autosaveTop = "/home/tdq39642/tmp/autosave-for-testing/"
        self.backupTop = "/home/tdq39642/tmp/autosave_backup/{0}".format(self.bl)
        
        # Name for new backup subdirectory
        self.newDirecoty = "autosave_backup_{0}".format(time.strftime("%Y-%m-%d_%H%M%S"))

        print "Top level autosave dir is "+self.autosaveTop+": what's inside?\n"
        
        # Check source and destination paths are OK
        if not os.path.exists(self.autosaveTop):
            print "Source directory for autosave does not seem to exist: {0}".format(self.autosaveTop)
            sys.exit()
        if not os.path.exists(self.backupTop):
            print "Target top level directory for backing up files does not seem to exist: {0}".format(self.backupTop)
            sys.exit()
        
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
            
            
        
    #    for root, dirs, files in os.walk(self.autosaveTop):
    #        print root, "has", len(files), ("file" if len(files) == 1 else "files"),
    #        print "and", len(dirs), ("directory" if len(dirs) == 1 else "directories")
    #        
    #        if (len(files) > 0):
    #            
    #            # Get last directory component
    #            dirmatches = re.match(lastDirectoryPattern, root)
    #            
    #            currentdir = dirmatches.group(1)
    #            
    #            for thisFile in files:
    #                # The three most recent files are those that end in .sav without a suffix.
    #                matches = re.match(latestFilePattern, thisFile)
    #                
    #                if (matches is not None):
    #
    #                    fileToBackUp = os.path.join(currentdir, thisFile)
    #                    print thisFile
    #                    self.backupFileList.append(fileToBackUp)
                
        print "\nList of files we will back up:"
        for subdir in self.backupFileList:
            print subdir
            for fileToBackUp in self.backupFileList[subdir]:
                print " "+fileToBackUp
            
        # cd to backup directory
        #os.chdir(self.backupTop)
        
        # Create a directory with date and time
        #os.mkdir()
            
            
    #    print "Backup dir will be:", self.backupTop
    
if __name__ == "__main__":
    a = AutosaveBackup()