#!/dls_sw/prod/tools/RHEL6-x86_64/defaults/bin/dls-python
# Script to generate a diff between backed up and live autosave files for a beamline
# producing an HTML output file

import sys, difflib

class AutosaveDiffer():
    
    def makeDiff(self, backupFilename, liveFilename):
        # Lists to hold lines read from files
        backupLines = ['']
        liveLines = ['']
        
        # Open input files
        with open(backupFilename, 'r') as backupFile:
            backupLines = backupFile.readlines()
        with open(liveFilename, 'r') as liveFile:
            liveLines = liveFile.readlines()
            
        # Generate the diff
        d = difflib.HtmlDiff()
        diffTable = d.make_table(backupLines, liveLines, fromdesc='Backup', todesc='Live file', context=True, numlines=0)
        return diffTable
        
    def writeFile(self, outFilename, finalLines):
        # Open output file
        with open(outFilename, 'w') as outFile:
            # Write output line by line
            for line in finalLines:
                outFile.write(line)
                
    def readHtmlTemplate(self):
        # Read header and footer lines
        with open(self.headFilename, 'r') as headFile:
            self.headLines = headFile.readlines()
        with open(self.footFilename, 'r') as footFile:
            self.footLines = footFile.readlines()
    
    def __init__(self):
        backupFilename = "bk_0.sav"
        liveFilename = "live_0.sav"
        self.headFilename = "head.html"
        self.footFilename = "foot.html"
        outFilename = "out.html"
        
        self.headLines = ['']
        self.footLines = ['']
        
        # Get the lines from the HTML header and footer
        self.readHtmlTemplate()
        
        # Generate the diff
        diffTable = self.makeDiff(backupFilename, liveFilename)
        
        # Build list of lines to write
        finalLines = self.headLines + [diffTable] + self.footLines
        self.writeFile(outFilename, finalLines)

        
        
        
if __name__ == "__main__":
    
    d = AutosaveDiffer()