#!/dls_sw/prod/tools/RHEL6-x86_64/defaults/bin/dls-python
# Script to generate a diff between backed up and live autosave files for a beamline
# producing an HTML output file

import sys, difflib

class AutosaveDiffer():
    
    def makeDiff(self, backupFilename, liveFilename, heading):
        
        # Heading string
        headingString = '<h2>{0}</h2>'.format(heading)
        
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
        diffString = d.make_table(backupLines, liveLines, fromdesc='Backup: '+backupFilename, todesc='Live file: '+liveFilename, context=True, numlines=0)
        diffTable = [headingString, diffString]
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
        #backupFilename = "bk_0.sav"
        #liveFilename = "live_0.sav"
        inputFiles = [["bk_0.sav", "live_0.sav", "BL13I-MO-IOC-02 level 0"],
        ["bk_1.sav", "live_1.sav", "BL13I-MO-IOC-02 level 1"],
        ["bk_2.sav", "live_2.sav", "BL13I-MO-IOC-02 level 2"]]
        self.headFilename = "head.html"
        self.footFilename = "foot.html"
        outFilename = "out.html"
        
        self.headLines = ['']
        self.footLines = ['']
        
        # Get the lines from the HTML header and footer
        self.readHtmlTemplate()
        
        # Generate the diff
        diffTable = ['']
        for [backupFilename, liveFilename, heading] in inputFiles:
            diffTable = diffTable + self.makeDiff(backupFilename, liveFilename, heading)
        
        # Build list of lines to write
        finalLines = self.headLines + diffTable + self.footLines
        self.writeFile(outFilename, finalLines)

        
        
        
if __name__ == "__main__":
    
    d = AutosaveDiffer()