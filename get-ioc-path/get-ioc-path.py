import subprocess
import re

"""Generate a BL module configure/RELEASE file from the currently configured versions of a list of IOCs"""

# List of macros to be substituted in paths
macros = {"$(PROD_IOCS)": "/dls_sw/prod/R3.14.12.3/ioc",
            "$(WORK_IOCS)": "/dls_sw/work/R3.14.12.3/ioc",
            "$(BUILDER_IOCS)": "/dls_sw/work/R3.14.12.3/support/BL13I-BUILDER/iocs"}

# List of IOCs to check
iocs = {
        "MO2I": "BL13I-MO-IOC-02",
        "MO3I": "BL13I-MO-IOC-03",
        "MO4I": "BL13I-MO-IOC-04",
        "MO5I": "BL13I-MO-IOC-05",
        "MO24I": "BL13I-MO-IOC-24",
        "DI1I": "BL13I-DI-IOC-01",
        "DI10I": "BL13I-DI-IOC-10",
        "DI16I": "BL13I-DI-IOC-16",
        
        }
        
def get_running_version(ioc_name):
    
    try:
        output = subprocess.check_output(["configure-ioc", "show", ioc_name]).split()
    
    except:
        return "NOT FOUND"
    
    path = output[1]
    
    for macro, expansion in macros.iteritems():
        path = path.replace(expansion, macro)   
        
    tokens = path.split("/bin")
    
    path = tokens[0]
    
    return path
    
input_file = open("RELEASE_TEST", "r")
output_file = open("RELEASE_OUTPUT", "w")

"""
for macro, expansion in macros.iteritems():
    lines.append("%s = %s" %(macro, expansion))
"""


for line in input_file:

    if line.find("-IOC-") >= 0:
        
        # Extract IOC name...
        tokens = line.split("/")
        for token in tokens:
            if token.find("-IOC-") >= 0:
                ioc_name = token
        
        if ioc_name:

                tokens = line.split("=")
                path_in_RELEASE = tokens[1].strip()
                
                path_in_redirector = get_running_version(ioc_name)
                if (path_in_RELEASE == path_in_redirector):
                    print "%s matches redirector" % (ioc_name)
                else:
                    print ioc_name, "in RELEASE:", path_in_RELEASE, "in redirector:", path_in_redirector
                    
                throwAway = raw_input("Hit return to do next")
                    

input_file.close()
output_file.close()

"""

for label, ioc_name in iocs.iteritems():
    path = get_running_version(label, ioc_name)
    lines.append("%s = %s" %(label, path))
    
for line in lines:
    print line
"""
