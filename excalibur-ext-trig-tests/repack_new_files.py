#!/bin/env dls-python
import os,sys,subprocess

# Search directory for VDS files and repack them into single files
# Skip those that already have a repacked file

COMMON = "/dls_sw/prod/R3.14.12.3/support/BL13I-COMMON/1-28"

def build_file_list(path_to_crawl, output_directory):
    """Build list of files to repack"""
    complete_file_list = []

    # Walk the directory tree collecting a list of what is there
    for root, dirs, files in os.walk(path_to_crawl, topdown=False):

        # Building a complete list of orphaned files
        for one_file in files:
            # Full path
            file_path = os.path.join(root, one_file)

            # Filename contains "vds" and not "repacked"
            if one_file.find("vds") >= 0 and one_file.find("repacked") < 0:
                # Already has repacked file?
                repacked_file_path = os.path.join(output_directory, "repacked_" + one_file)
                if (os.path.exists(repacked_file_path)):
                    # Yes, skip and say so
                    print file_path + " (already repacked to %s, will be skipped)" % repacked_file_path
                else:
                    # No, add to list
                    complete_file_list.append(file_path)
                    print file_path

        return complete_file_list

def run_repack_on_file(path_to_repack_script, file_path, output_directory):
    """Call script to repack a file"""
    print "### Repack VDS file %s..." % file_path
    command = "%s %s %s" % (path_to_repack_script, file_path, output_directory)
    print command
    subprocess.call(command.split(" "))

if (__name__ == "__main__"):

    # Path to the script which does one repack
    path_to_repack_script = os.path.join(COMMON, "etc", "repack_vds.sh")

    # Get list of VDS files in this directory which haven't been repacked yet
    source_directory = sys.argv[1]
    output_directory = sys.argv[2]
    print "Looking for VDS files in %s:" % source_directory

    list_of_vds = build_file_list(source_directory, output_directory)

    # Do the repacking on the necessary files
    if len(list_of_vds) > 0:
        print "\nRepacking data for each file"
        print "Write output files to %s" % output_directory
        for file_path in list_of_vds:
            run_repack_on_file(path_to_repack_script, file_path, source_directory)
    else:
        print "\nNo files to repack"

    print "Script finished"