#!/bin/env dls-python
import subprocess, os, sys

def run_vds_gen(working_directory, file_number, excalibur_bit_mode):
    """Run dls-vds-gen.py to create a virtual dataset"""
    # Arguments for VDS command
    vds_params = {}
    vds_params["wd"] = working_directory
    vds_params["file_number"] = int(file_number)

    # Must use int32 for 24 bit mode, int16 for 12 bit mode
    if excalibur_bit_mode.find("24") >= 0:
        data_type = "int32"
    else:
        data_type = "int16"
    vds_params["data_type"] = data_type

    # Substitute the arguments
    command = "dls-vds-gen.py %(wd)s -f "
    for fem in xrange(1, 7):
        command = command + "excalibur-%d" % (fem)
        command = command + "--%(file_number)d.hdf "

    command = command + "--source_node /entry/instrument/detector/data "
    command = command + "--target_node /entry/instrument/detector/data "
    command = command + "-s 0 -m 121 -o excalibur_%(file_number)d_vds.h5 -l 1 "

    command = command % (vds_params)

    # Execute the command
    print "Generate virtual dataset:"
    print command
    subprocess.call(command.split(" "))

if __name__ == "__main__":
    number_of_arguments = 3
    if len(sys.argv) != (number_of_arguments + 1):
        print "%s <directory> <scan number> <number of images>" % sys.argv[0]
        print "\tdirectory = directory containing data files"
        print "\tscan number = scan number of the files we want"
    else:
        # Get arguments from command line
        working_directory = sys.argv[1]
        file_number = sys.argv[2]

        # Run VDS gen command
        run_vds_gen(working_directory, file_number)