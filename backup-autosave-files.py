#!/dls_sw/prod/tools/RHEL6-x86_64/defaults/bin/dls-python
# Script to back up latest autosave files for a beamline

import os, shutil

def get_path():
    bl = "i13"
    #autosaveTop = "/dls_sw/%s/epics/autosave/".format(bl)
    autosaveTop = "/home/tdq39642/tmp/autosave/{0}/epics/autosave/".format(bl)
    print autosaveTop
    
    
    os.listdir(autosaveTop)
    
if __name__ == "__main__":
    get_path()