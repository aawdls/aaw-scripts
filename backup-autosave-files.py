#!/dls_sw/prod/tools/RHEL6-x86_64/defaults/bin/dls-python
# Script to back up latest autosave files for a beamline

import os, shutil, time

def get_path():
    bl = "i13"
    #autosaveTop = "/dls_sw/{0}/epics/autosave/".format(bl)
    autosaveTop = "/home/tdq39642/tmp/autosave/{0}/epics/autosave/".format(bl)
    backupTop = "/home/tdq39642/tmp/autosave_backup/{1}/{0}/epics/autosave/".format(bl, time.strftime("%Y-%m-%d_%H%M%S"))
    

    print "Top level autosave dir is "+autosaveTop+": what's inside?\n"
    
    for root, dirs, files in os.walk(autosaveTop):
        print root, "has", len(files), ("file" if len(files) == 1 else "files"),
        print "and", len(dirs), ("directory" if len(dirs) == 1 else "directories")
        
        if (len(files) > 0):
            lastTime = None
            lastFile = None
            
            for file in files:
                fileStatus = os.stat( os.path.join(root, file) )
                modTime = time.localtime(fileStatus.st_mtime)
                if (lastTime is None or modTime > lastTime):
                    lastTime = modTime
                    lastFile = file
                print "-", file, time.strftime("%Y-%m-%d %H:%M:%S", modTime)
                
            print "+", lastFile, "was modified last."
            
    print "Backup dir will be:", backupTop
    
if __name__ == "__main__":
    get_path()