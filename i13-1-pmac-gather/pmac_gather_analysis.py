#!/bin/env dls-python
""" Script to plot data from dls-pmac-control gather function
Copied from work done by Chris Turner on GPFS test analysis
"""
from pkg_resources import require
require('matplotlib')
import csv, sys, getopt
from collections import OrderedDict
import os

import matplotlib.pyplot as plt
from matplotlib.legend_handler import HandlerLine2D

class GatherPlotter():

    def __init__(self, timebase_ms):
        self.headers = []
        self.column = {}
        self.timebase_ms = timebase_ms

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

        for h in self.headers:
            self.column[h] = []

        # Read the row data
        for row in reader:
            for label, v in zip(self.headers, row):
                # Get time in ms
                if label == self.headers[0]:
                    v = float(v) * self.timebase_ms

                self.column[label].append(v)

        f.close()


    def plot(self, plotParams, outputfig):

        # Preapre the data
        y1 = self.column[self.headers[1]]
        y2 = self.column[self.headers[2]]
        x1 = self.column[self.headers[0]]
        x2 = self.column[self.headers[0]]

        # Create and configure the plot
        fig = plt.figure()

        ax = fig.add_axes([0.1, 0.1, 0.7, 0.7])

        # Axes for first series
        ax.plot(x1, y1, "b-")

        # Axes for second series - shares x axis
        ax2 = ax.twinx()
        ax2.plot(x2, y2, "r-")

        #ax.set_xticks(x1)
        #ax.set_xticklabels(, rotation=45)

        # Labels
        ax.set_ylabel(self.headers[1], color="b")
        ax2.set_ylabel(self.headers[2], color="r")
        ax.set_xlabel(self.headers[0])
        ax.set_title(plotParams['title'])

        # Legend
        #legend = plt.legend(bbox_to_anchor=(1.01, 1), loc=2, borderaxespad=0.)

        # Show, save
        #plt.show()
        fig.savefig(outputfig, bbox_inches='tight')

def do_plot(input_filename, title, timebase_ms, output_filename):
    # Create plotter object
    my_plotter = GatherPlotter(timebase_ms)
    my_plotter.read_csv_file(input_filename)

    my_plotter.plot({'title': title}, output_filename)

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
