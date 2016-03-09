#!/dls_sw/prod/tools/RHEL6-x86_64/defaults/bin/dls-python
# Script to back up latest autosave files for a beamline

import os, shutil, time, re

def get_path():
    bl = "i13"
    #autosaveTop = "/dls_sw/{0}/epics/autosave/".format(bl)
    autosaveTop = "/home/tdq39642/tmp/autosave/{0}/epics/autosave/".format(bl)
    backupTop = "/home/tdq39642/tmp/autosave_backup/{1}/{0}/epics/autosave/".format(bl, time.strftime("%Y-%m-%d_%H%M%S"))
    
    latestFilePattern = r".sav$"

    print "Top level autosave dir is "+autosaveTop+": what's inside?\n"
    
    # List of files we will want to back up
    backupFileList = list()
    
    for root, dirs, files in os.walk(autosaveTop):
        print root, "has", len(files), ("file" if len(files) == 1 else "files"),
        print "and", len(dirs), ("directory" if len(dirs) == 1 else "directories")
        
        if (len(files) > 0):
            
            # The three most recent files are those that end in .sav without a suffix.
            matches = re.match(latestFilePattern, file)
            
            if (matches is not None):
                print "Found", len(matches), "most recent files:"
                for match in matches:
                    # Add full path to this file to list we want to back up
                    fileToBackUp = os.path.join(root, file)
                    print fileToBackUp
                    backupFileList.append(fileToBackUp)
            
    print "\nList of files we will back up:"
    for (fileToBackUp in backupFileList):
        print fileToBackUp
        
    print "Backup dir will be:", backupTop
    
if __name__ == "__main__":
    get_path()