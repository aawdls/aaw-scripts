#!/bin/env dls-python
import os

def get_file_sizes(directory, file_number, expected_bytes, last_mtime):

        file_name = "excalibur-%(FEM_PLACEHOLDER)s--%(file_number)d.hdf" % ({"FEM_PLACEHOLDER":"%(FEM)d", "file_number": file_number})

        for FEM in xrange(1,2):
            this_file = file_name % {"FEM": FEM}
            my_path = os.path.join(directory, this_file)
            try:
                my_stat = os.stat(my_path)

                size_bytes = my_stat.st_size
                mtime = my_stat.st_mtime

                print "%d.%d: %d, %d s" % (file_number, FEM, size_bytes, (mtime-last_mtime))
                if size_bytes != expected_bytes:
                    print "\tWRONG SIZE!"
                last_mtime = mtime
                return last_mtime
            except:
                print "Couldn't stat %s" % my_path

if __name__ == "__main__":

    data_dir = "/dls/i13-1/data/2017/cm16785-5/tmp"
    expected_bytes = 10717908148
    last_mtime = 0
    for file_number in xrange(210, 210+600):
        last_mtime = get_file_sizes(data_dir, file_number, expected_bytes, last_mtime)