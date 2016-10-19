#!/dls_sw/prod/tools/RHEL6-x86_64/defaults/bin/dls-python
import os, sys, re

class wikiConversion():
    
    inFile = None
    outFile = None
    
    def __init__(self, clArgs):
        self.inFilePath = clArgs[1]
        self.outFilePath = clArgs[2]
        self.inFile = open(self.inFilePath, "r")
        self.outFile = open(self.outFilePath, "w")
        
        
    def __enter__(self):

        return self
        
    def doConversion(self):
        for line in self.inFile:
            #results = re.match(r"===(.+)===",line)
            line = re.sub(r"^===(.+)===",r"\nh3. \1\n",line)
            line = re.sub(r"^==(.+)==",r"\nh2. \1\n",line)
            line = re.sub(r"^=(.+)=",r"\nh1. \1\n",line)
            self.outFile.write(line)
        return
        
    def __exit__(self, exc_type, exc_value, traceback):
        for eachFile in [self.inFile, self.outFile]:
            if eachFile:
                eachFile.close()
        return
                

        
        
if __name__=="__main__":
    with wikiConversion(sys.argv) as c:
        c.doConversion()