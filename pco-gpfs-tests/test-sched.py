#!/dls_sw/prod/tools/RHEL6-x86_64/defaults/bin/dls-python
from pkg_resources import require
require('cothread') #http://cothread.readthedocs.io/en/latest/catools.html
from cothread.catools import *
from cothread import Sleep
#from pcoSim import *
import datetime, time, csv, sys, os, sched

begin = time.time()


def print_time():
    print "From print_time", (time.time() - begin)
    return
    
s = sched.scheduler(time.time, time.sleep)

minute = 0.1#60
half_hour = 30 * minute
hour = 2 * half_hour
test_duration = int(round(24 * hour))
test_interval = int(round(half_hour))

for delay in xrange (0, test_duration, test_interval):
    print "Schedule delay of", delay, "s"
    s.enter(delay, 1, print_time, ())

#s.enter(5, 1, print_time, ())
s.run()
print time.time()
