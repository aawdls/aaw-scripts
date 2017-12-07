import subprocess, os

#!/bin/env dls-python
import os

def bzip_my_file(directory, file_number, raw_dir):

        file_name = "excalibur-%(FEM_PLACEHOLDER)s--%(file_number)d.hdf" % ({"FEM_PLACEHOLDER":"%(FEM)d", "file_number": file_number})

        for FEM in xrange(1,7):
            this_file = file_name % {"FEM": FEM}
            my_path = os.path.join(directory, this_file)
            try:
                my_stat = os.stat(my_path)

                size_bytes = my_stat.st_size
                mtime = my_stat.st_mtime

                print "%d.%d: %d, %d s" % (file_number, FEM, size_bytes, (mtime))

                command = "bzip2 -v %s" % this_file
                print "Execute: %s" % command
                try:
                    subprocess.call(command.split(" "))
                    my_bzip_file = os.path.join(directory, (this_file + ".bz2"))
                    my_bzip_file_in_raw = os.path.join(raw_dir, (this_file + ".bz2"))
                    print "Rename %s -> %s" % (my_bzip_file, my_bzip_file_in_raw)
                    try:
                        os.rename(my_bzip_file, my_bzip_file_in_raw)
                    except:
                        print "Move failed"
                except:
                    print "bzip command failed"

            except:
                print "Couldn't stat %s" % my_path

if __name__ == "__main__":

    data_dir = "/dls/i13-1/data/2017/cm16785-5/tmp"
    raw_dir  = "/dls/i13-1/data/2017/cm16785-5/raw"

    for file_number in xrange(178, 810):
        print "File number: ", file_number
        bzip_my_file(data_dir, file_number, raw_dir)