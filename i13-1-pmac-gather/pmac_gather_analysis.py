#!/bin/env dls-python
""" Script to plot data from dls-pmac-control gather function
Copied from work done by Chris Turner on GPFS test analysis
"""
from pkg_resources import require
require('matplotlib')
import csv, sys, getopt, re
from collections import OrderedDict
import os

import matplotlib.pyplot as plt
#from matplotlib.legend_handler import HandlerLine2D

IS_A_TIME = 1
IS_A_POSITION = 2
IS_A_VELOCITY = 3

class GatherPlotter():

    def __init__(self, timebase_ms, number_of_data_columns=2, mres=1, egu="deg"):
        self.headers = []
        self.column = {}
        self.column_data_type = {}
        self.column_multiplier = {}
        self.timebase_ms = timebase_ms
        self.number_of_data_columns = number_of_data_columns
        self.mres = mres
        self.egu = egu

    def read_csv_file(self, input_filename):

        # Open file for reading
        f = open(input_filename, 'rb')
        # Interpret as CSV
        reader = csv.reader(f)
        # First row contains headers
        self.headers = reader.next()

        # Read the headers and label up the columns
        self.column = OrderedDict()
        self.headers[0] = "Time /ms"

        # We will give friendlier labels to our columns
        new_headers = []
        
        print "self.mres", self.mres
        
        for h in self.headers:
            new_header = ""
            # Working out what data type this is
            if re.search('position', h, re.IGNORECASE):

                new_header = "Position / %s" % self.egu
                self.column_data_type[new_header] = IS_A_POSITION
                self.column_multiplier[new_header] = float(self.mres)
            elif re.search('velocity', h, re.IGNORECASE):

                new_header = "Velocity / %s/s" % self.egu
                self.column_data_type[new_header] = IS_A_VELOCITY
                self.column_multiplier[new_header] = float(self.mres) * 1000.0 * 5
            elif re.search('time', h, re.IGNORECASE):

                new_header = "Time /ms"
                self.column_data_type[new_header] = IS_A_TIME
                self.column_multiplier[new_header] = self.timebase_ms
            new_headers.append(new_header)
            
            print new_header, self.column_multiplier
        # Updated header names
        
        self.headers = new_headers
        print self.headers
        
        for h in self.headers:
            self.column[h] = []

        # Read the row data
        for row in reader:
            for label, v in zip(self.headers, row):
                # Ignore empty columns
                if label != "":
                    
                    # Scale axis appropriately
                    v = float(v) * self.column_multiplier[label]
                    #print "Scaling %s by %f" % (label, self.column_multiplier[label])
                    
                self.column[label].append(v)

        f.close()


    def plot(self, plotParams, outputfig, desired_xnlim, desired_xplim, desired_ynlim=None, desired_yplim=None):

        # Preapre the data
        y1 = self.column[self.headers[1]]
        y2 = self.column[self.headers[2]]
        x1 = self.column[self.headers[0]]
        x2 = self.column[self.headers[0]]

        # Create and configure the plot
        fig = plt.figure()
        ax = fig.add_axes([0.1, 0.1, 0.7, 0.7])
        
        at_leat_two_data_column = self.number_of_data_columns >= 2
        
        if at_leat_two_data_column:
            # Axes for second series - shares x axis
            ax2 = ax.twinx()



        # Set optional limits on x axis
        if desired_xnlim is not None and desired_xplim is not None:
            print "Set xlim for", plotParams['title'], "to %d - %d" % (desired_xnlim,desired_xplim)
            ax.set_xlim(desired_xnlim,desired_xplim)
            if at_leat_two_data_column:
                ax2.set_xlim(desired_xnlim,desired_xplim)

        # Set optional limits on y axis
        if desired_ynlim is not None and desired_yplim is not None:
            print "Set ylim for", plotParams['title'], "to %d - %d" % (
            desired_ynlim, desired_yplim)
            ax.set_ylim(desired_ynlim, desired_yplim)

        # Axes for first series
        ax.plot(x1, y1, "b-")
        if at_leat_two_data_column:
            ax2.plot(x2, y2, "r-")

        #ax.set_xticks(x1)
        #ax.set_xticklabels(, rotation=45)

        # Labels
        ax.set_ylabel(self.headers[1], color="b")
        if at_leat_two_data_column:
            ax2.set_ylabel(self.headers[2], color="r")
        ax.set_xlabel(self.headers[0])
        ax.set_title(plotParams['title'])
        ax.grid(color="gray")

        # Legend
        #legend = plt.legend(bbox_to_anchor=(1.01, 1), loc=2, borderaxespad=0.)

        # Show, save
        #plt.show()
        fig.savefig(outputfig, bbox_inches='tight')

def do_plot(input_filename, title, timebase_ms, output_filename, desired_xnlim=None, desired_xplim=None, num_columns=2, mres=1, egu="deg", desired_ynlim=None, desired_yplim=None):
    # Create plotter object
    my_plotter = GatherPlotter(timebase_ms, number_of_data_columns=num_columns, mres=mres, egu=egu)
    my_plotter.read_csv_file(input_filename)

    my_plotter.plot({'title': title}, output_filename, desired_xnlim, desired_xplim, desired_ynlim=desired_ynlim, desired_yplim=desired_yplim)

def main(argv):
    # Parse command line options
    usage = "Usage: %s -f <input CSV file> -t <servo cycles per point> -o <output image file>" % sys.argv[0]

    timebase_ms = 1
    input_filename = ""
    try:
        opts,args = getopt.getopt(argv,"f:t:o:", ["inputfile=","timebase=","outputfile="])
    except getopt.GetoptError:
        print usage
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print usage
            sys.exit()
        elif opt in ("-t", "--timebase"):
            timebase_cycles = int(arg)
            timebase_ms = timebase_cycles * 0.2
        elif opt in ("-f", "--inputfile"):
            input_filename = arg
        elif opt in ("-o", "--outputfile"):
            output_filename = arg
        elif opt in ("-T", "--title"):
            title = arg

    if title is None or output_filename is None or input_filename is None or timebase_ms is None:
        print usage
        sys.exit()

    # Have all the required info
    do_plot(input_filename, title, timebase_ms, output_filename)


if __name__ == "__main__":
    main(sys.argv[1:])
