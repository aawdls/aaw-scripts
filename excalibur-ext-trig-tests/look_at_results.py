#!/bin/env dls-python
import os

def get_file_sizes(directory, file_number, expected_bytes):

        file_name = "excalibur-%(FEM_PLACEHOLDER)s--%(file_number)d.hdf" % ({"FEM_PLACEHOLDER":"%(FEM)d", "file_number": file_number})

        for FEM in xrange(1,7):
            this_file = file_name % {"FEM": FEM}
            my_path = os.path.join(directory, this_file)
            my_stat = os.stat(my_path)

            size_bytes = my_stat.st_size

            print "%d.%d: %d" % (file_number, FEM, size_bytes)
            if size_bytes != expected_bytes:
                print "\tWRONG SIZE!"

def delete_file

if __name__ == "__main__":

    data_dir = "/dls/i13-1/data/2017/cm16785-5/tmp"
    expected_bytes = 10717908148
    for file_number in xrange(32, 32+140):
        r = get_file_sizes(data_dir, file_number, expected_bytes)