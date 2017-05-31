#!/bin/env dls-python
# Plot data from tests run on J13 on 2017-05-30
import pmac_gather_analysis
import os

# Build in some assumptions about filename and timebase to save typing
def plot_wrapper(file_stem, title=None):
    if title is None:
        title=file_stem

    pmac_gather_analysis.do_plot("src/%s.csv" % file_stem, title,
                                 20, "output/%s.png" % file_stem)

# Output directory
if not os.path.exists("output"):
    os.mkdir("output")

# Process CSV files
plot_wrapper("stationary", "Stage statonary in position")
#plot_wrapper("single_step_2", "Single software step 2")
plot_wrapper("single_step_200_um_s_accl_1_s", "Speed = 200 um/s, acceleration time = 1s")
plot_wrapper("single_step_150_um_s", "Speed = 150 ums / s")
plot_wrapper("single_point", "Single software step")
plot_wrapper("i24_dwell_1_s", "I24 step scan, dwell time 1 s")
plot_wrapper("i24_dwell_1_s_2", "I24 step scan, dwell time 1 s")
plot_wrapper("i24_dwell_100_ms", "I24 step scan, dwell time 100 ms")
plot_wrapper("1um_steps_with_velocity", "1um step scan, spped = 200 um/s")
plot_wrapper("10um_steps_with_velocity", "10um step scan, speed = 200 ums/")
#plot_wrapper("10um_steps")
plot_wrapper("10um_scan_rdbd_0.1_um")

