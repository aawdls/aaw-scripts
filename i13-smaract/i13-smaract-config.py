#!/bin/env dls-python
"""Configure SmarAct Axes for I13 """
from pkg_resources import require
require("cothread==2.14")

from cothread import catools



class SmaractAxis:
    """Represents an axis and can get/set its config"""

    def __init__(self, pv_prefix, phys_axis=-1, sensor_type=-1, active_hold=1):
        self.prefix = pv_prefix
        self.phys_axis = phys_axis
        self.sensor_type = sensor_type
        self.active_hold = active_hold

        self.phys_axis_pv = "%s:PHYSAXIS" % self.prefix
        self.sensor_type_pv = "%s:SENSORTYPE" % self.prefix
        self.active_hold_pv = "%s:ACTIVEHOLD" % self.prefix

    def get_phys_axis(self):
        self.phys_axis = catools.caget(self.phys_axis_pv)
        #print "%s = %d" %( self.phys_axis_pv, self.phys_axis)

    def get_sensor_type(self):
        self.sensor_type = catools.caget(self.sensor_type_pv)
        #print "%s = %d" % (self.sensor_type_pv, self.sensor_type)

    def put_phys_axis(self):
        print "caput %s %d" % (self.phys_axis_pv, self.phys_axis)
        catools.caput(self.phys_axis_pv, self.phys_axis)

    def put_sensor_type(self):
        print "caput %s %d" % (self.sensor_type_pv, self.sensor_type)
        catools.caput(self.sensor_type_pv, self.sensor_type)

    def put_active_hold(self):
        print "caput %s %d" % (self.active_hold_pv, self.active_hold)
        catools.caput(self.active_hold_pv, self.active_hold)

def print_current_config():
    """Cagets the current configuration
    prints the info out in a format that can be copied
    to create a function to put it"""

    prefixes = [  # Controller 1
        "BL13I-MO-STAGE-01:SAMPLE2X",
        "BL13I-MO-STAGE-01:SAMPLE2Y",
        "BL13I-MO-STAGE-01:SAMPLE2Z",
        "BL13I-OP-PHRNG-01:X",
        "BL13I-OP-PHRNG-01:Y",
        "BL13I-OP-PHRNG-01:Z",
        "BL13I-OP-ABSB-06:X",
        "BL13I-OP-ABSB-06:Y",
        "BL13I-OP-ABSB-06:Z",
        "BL13I-OP-ZONEP-01:X",
        "BL13I-OP-ZONEP-01:Y",
        "BL13I-OP-ZONEP-01:Z",
        "BL13I-MO-SMAR-01:X2",
        "BL13I-MO-SMAR-01:Y2",
        "BL13I-MO-SMAR-01:Z2",
        "BL13I-MO-SMAR-01:RX2",
        "BL13I-MO-SMAR-01:RY2",
        "BL13I-MO-SMAR-01:RZ2",
        "BL13I-MO-SMAR-01:GRX",
        "BL13I-MO-SMAR-01:GRZ",
        # Controller 2
        "BL13I-MO-SMAR-02:X",
        "BL13I-MO-SMAR-02:Y",
        "BL13I-MO-SMAR-02:Z"]

    for prefix in prefixes:
        axis = SmaractAxis(prefix)
        axis.get_phys_axis()
        axis.get_sensor_type()

        print 'SmaractAxis("%s",   phys_axis=%d, sensor_type=%d),' % (
        axis.prefix, axis.phys_axis, axis.sensor_type)

def put_config_for_grating():
    """Caput the configuration for grating experiment 2018-03-09"""
    axes = [SmaractAxis("BL13I-MO-STAGE-01:SAMPLE2X",   phys_axis=7, sensor_type=1),
    SmaractAxis("BL13I-MO-STAGE-01:SAMPLE2Y",   phys_axis=8, sensor_type=21),
    SmaractAxis("BL13I-MO-STAGE-01:SAMPLE2Z",   phys_axis=6, sensor_type=1),
    SmaractAxis("BL13I-OP-PHRNG-01:X",   phys_axis=3, sensor_type=0),
    SmaractAxis("BL13I-OP-PHRNG-01:Y",   phys_axis=5, sensor_type=0),
    SmaractAxis("BL13I-OP-PHRNG-01:Z",   phys_axis=4, sensor_type=0),
    SmaractAxis("BL13I-OP-ABSB-06:X",   phys_axis=6, sensor_type=0),
    SmaractAxis("BL13I-OP-ABSB-06:Y",   phys_axis=8, sensor_type=0),
    SmaractAxis("BL13I-OP-ABSB-06:Z",   phys_axis=7, sensor_type=0),
    SmaractAxis("BL13I-OP-ZONEP-01:X",   phys_axis=12, sensor_type=0),
    SmaractAxis("BL13I-OP-ZONEP-01:Y",   phys_axis=14, sensor_type=0),
    SmaractAxis("BL13I-OP-ZONEP-01:Z",   phys_axis=13, sensor_type=0),
    SmaractAxis("BL13I-MO-SMAR-01:X2",   phys_axis=15, sensor_type=0),
    SmaractAxis("BL13I-MO-SMAR-01:Y2",   phys_axis=16, sensor_type=0),
    SmaractAxis("BL13I-MO-SMAR-01:Z2",   phys_axis=17, sensor_type=0),
    SmaractAxis("BL13I-MO-SMAR-01:RX2",   phys_axis=18, sensor_type=0),
    SmaractAxis("BL13I-MO-SMAR-01:RY2",   phys_axis=10, sensor_type=2),
    SmaractAxis("BL13I-MO-SMAR-01:RZ2",   phys_axis=9, sensor_type=2),
    SmaractAxis("BL13I-MO-SMAR-01:GRX",   phys_axis=12, sensor_type=16),
    SmaractAxis("BL13I-MO-SMAR-01:GRZ",   phys_axis=13, sensor_type=17),
    SmaractAxis("BL13I-MO-SMAR-02:X",   phys_axis=4, sensor_type=1),
    SmaractAxis("BL13I-MO-SMAR-02:Y",   phys_axis=5, sensor_type=21),
    SmaractAxis("BL13I-MO-SMAR-02:Z",   phys_axis=3, sensor_type=1)]

    for axis in axes:
        axis.put_phys_axis()
        axis.put_sensor_type()
        axis.put_active_hold()

if __name__ == "__main__":
    put_config_for_grating()
