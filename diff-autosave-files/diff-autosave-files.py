#!/dls_sw/prod/tools/RHEL6-x86_64/defaults/bin/dls-python
# Script to generate a diff between backed up and live autosave files for a beamline
# producing an HTML output file

import sys, difflib

class AutosaveDiffer():
    
    def __init__(self):
        backupFilename = "bk_0.sav"
        liveFilename = "live_0.sav"
        headFilename = "head.html"
        footFilename = "foot.html"
        outFilename = "out.html"
        
        backupLines = ['']
        liveLines = ['']
        headLines = ['']
        footLines = ['']
        
        # Open input files
        with open(backupFilename) as backupFile:
            backupLines = backupFile.readlines()
        with open(liveFilename, 'r') as liveFile:
            liveLines = liveFile.readlines()
        with open(headFilename, 'r') as headFile:
            headLines = headFile.readlines()
        with open(footFilename, 'r') as footFile:
            footLines = footFile.readlines()
        
        # Open output file
        with open(outFilename, 'w') as outFile:

            # Generate the diff
            d = difflib.HtmlDiff()
            diffTable = d.make_table(backupLines, liveLines, fromdesc='Backup', todesc='Live file', context=True, numlines=0)
            
            finalLines = headLines + [diffTable] + footLines
            
            for line in finalLines:
                outFile.write(line)
        
        
        
if __name__ == "__main__":
    
    d = AutosaveDiffer()