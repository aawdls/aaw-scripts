#!/dls_sw/prod/tools/RHEL6-x86_64/defaults/bin/dls-python
import subprocess
import re
import os.path, sys

"""Parse a BL module configure/RELEASE file and check the versions of IOCs against those in the redirector"""

class ReleaseFileIocChecker:
    
    def __init__(self, filename):
        # This will hold the list of macros we find in the RELEASE file
        self.macros = {}
        self.filename = filename
        self.input_file = None


    def configure_ioc_show(self, ioc_name):
        """
        Run "configure-ioc show <ioc_name>" and return the path with macros applied
        """
        
        try:
            output = subprocess.check_output(["configure-ioc", "show", ioc_name]).split()
        
        except:
            return "NOT FOUND"
        
        # Second word returned by configre-ioc is the path
        path = output[1]
        
        # Apply macros from configure-ioc
        for macro, expansion in self.macros.iteritems():
            macro_with_dollar = "$(%s)" % (macro)
            path = path.replace(expansion, macro_with_dollar)   
            
        # Throw away the script name, only care about the directory
        tokens = path.split("/bin")
        path = tokens[0]
        
        return path
        
    def check(self):
    
        # Open the RELEASE File
        if os.path.exists(self.filename):
            self.input_file = open(self.filename, "r")
            print "Checking input file %s\n" % self.filename
        else:
            print "Cannot open input file %s" % self.filename
            return
            

        # Parse the RELEASE file
        for line in self.input_file:

            # Naively look for macros
            if line.find("/dls_sw/") >= 0:
                # Assume this is a macro definition
                tokens = line.split("=")
                if len(tokens) == 2:
                    key = tokens[0].strip()
                    value = tokens[1].strip()
                    self.macros[key] = value
                    print "$(%s) = %s" %(key, value)
                    
            # Naively look for IOCs
            elif line.find("-IOC-") >= 0:
                
                # Extract IOC name...
                tokens = line.split("/")
                for token in tokens:
                    if token.find("-IOC-") >= 0:
                        ioc_name = token.strip()
                
                # Got one!
                if ioc_name:

                        # So messy...
                        tokens = line.split("=")
                        path_in_RELEASE = tokens[1].strip()
                        
                        # Ask the redirector
                        path_in_redirector = self.configure_ioc_show(ioc_name)
                        
                        # Are they the same?
                        if (path_in_RELEASE == path_in_redirector):
                            print "%s matches redirector" % (ioc_name)
                        else:
                            print ioc_name, "\tIn RELEASE:", path_in_RELEASE, "in redirector:", path_in_redirector
                            
                        # Debug breakpoint...
                        #throwAway = raw_input("Hit return to do next")

    def __enter__(self):
        return self
         
    def __exit__(self, exc_type, exc_value, traceback):
        # Close file
        if self.input_file:
            self.input_file.close()

if __name__ == "__main__":
    
    if (len(sys.argv) != 2):
        print "Usage: get-ioc-path.py <Path to configure/RELEASE>"
        exit()
    
    with ReleaseFileIocChecker(sys.argv[1]) as p:
        p.check()
