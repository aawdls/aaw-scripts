#!/bin/env dls-python
import argparse, os, sys, logging, re, datetime
import para_log_view_html_template as html

def parse_arguments():
    """Parse and breifly check command line arguments"""
    help = """Write an HTML file to show two conserver log files
    side by side for easy comparison."""
    argument_parser = argparse.ArgumentParser(description=help)
    argument_parser.add_argument("log_filename", type=str, nargs="+",
                                 help="Paths to input log files")
    argument_parser.add_argument("output_dir", type=str,
                                 help="Directory to put output HTML files")
    args = argument_parser.parse_args()

    # Check arguments
    for input_path in args.log_filename:
        if not os.path.exists(input_path):
            print "Input file not found: %s" % input_path
            sys.exit()

    if False and os.path.exists(args.output_filename):
        print "Output HTML file already exsits: %s" % args.output_filename
    return args

def parse_date(line):
    """Return the date prefix from a conserver line
    If it doesn't fit the pattern, return None"""
    match = re.search('^\[(\w{3}.+?)\]', line)

    if match is None:
        logging.debug("No date in line %s" % line)
        return ""
    else:
        return match.group(1)

def get_date_from_line(line):
    """Return a datetime object from string date in
    format such as Sat Jan 27 09:13:38 2018
    On failure return None"""
    date_string = parse_date(line)
    try:
        date_obj = datetime.datetime.strptime(date_string, "%a %b %d %H:%M:%S %Y")
    except:
        date_obj = None
    return date_obj


def main():
    logging.basicConfig(level=logging.INFO)
    args = parse_arguments()

    logging.info("Write headers")
    index_filename = os.path.join(args.output_dir, "index.html")

    # Write headers in hour files
    hour_filenames = []
    for hour in xrange(0, 24):
        hour_string = "%02d" % hour
        hour_filename = os.path.join(args.output_dir, "%s.html" % hour_string)
        hour_filenames.append(hour_filename)
        with open(hour_filename, "wb") as output_file:
            output_file.write(html.page_head)
            output_file.write(html.body_start)
            output_file.write(html.table_head.format(file1=args.log_filename[0],
                                                     file2=args.log_filename[1]))


    input_lines = []

    logging.info("Opening input files and loading into memory")
    longest_col = 0
    for input_path in args.log_filename:
        row_counter = 0
        logging.debug("Open %s for reading" % input_path)
        input_file = open(input_path, "rb")

        lines_from_file = []
        # Build a list in memory of all lines in file
        for line in input_file:
            lines_from_file.append(line)
            row_counter += 1
        # Store this
        input_lines.append(lines_from_file)

        # Keeping a record of longest column
        # so we know how far to go.
        longest_col = max([row_counter, longest_col])
        logging.debug("longest_col = %d" % longest_col)

    # Not sure this is best idea but pad all of
    # 1st dimenion in input_lines to same length
    logging.debug("Pad lists to same length")
    for one_list in input_lines:
        one_list += [""] * (longest_col - len(one_list))

    x_index = 0
    y_index = 0
    current_hour = 0
    hour_counts = [0]*24

    # Stepping through all our rows in memory
    for row in xrange(0, longest_col):

        # Parse one line from each file to get time
        x_line = input_lines[0][x_index]
        y_line = input_lines[1][y_index]

        x_date = get_date_from_line(x_line)
        y_date = get_date_from_line(y_line)

        # Advance the hour if necessary
        current_hour = advance_hour(current_hour, x_date, y_date)
        # Stats for recording number of lines per hour
        hour_counts[current_hour] += 1

        # Open correct file to append a row
        with open(hour_filenames[current_hour], "ab") as output_file:

            if x_date is None or y_date is None or x_date == y_date:
                logging.debug("Equal")
                output_file.write(html.one_row.format(col1=x_line, col2=y_line))
                x_index += 1
                y_index += 1
            elif x_date < y_date:
                logging.debug("x before y")
                output_file.write(html.one_row.format(col1=x_line, col2=""))
                x_index += 1
            else:
                logging.debug("y before x")
                output_file.write(html.one_row.format(col1="", col2=y_line))
                y_index += 1

    # Write footer for each hour file
    logging.info("Write hour file footers")
    for hour_filename in hour_filenames:
        with open(hour_filename, "ab") as output_file:
            output_file.write(html.table_bottom)
            output_file.write(html.page_end)

    # Finally Write the index page
    logging.info("Write index page")
    with open(index_filename, "wb") as output_file:
        output_file.write(html.page_head)
        output_file.write(html.body_start)
        output_file.write("<p>View logs by hour.</p>")

        for hour in xrange(0, 24):
            hour_string = "%02d" % hour
            output_file.write(
                '<a href="%s.html" target="hour_page">%s</a> (%d) ' % (hour_string, hour_string, hour_counts[hour]))

        output_file.write(html.iframe)

        output_file.write(html.page_end)


def advance_hour(current_hour, x_date, y_date):
    """Set current_hour based on the earlier of x_date and y_date,
    or do not change it if neither usable"""

    prev_hour = current_hour

    if x_date is not None and y_date is not None:
        if x_date <= y_date:
            current_hour = x_date.hour
        else:
            current_hour = y_date.hour
    elif x_date is not None:
        current_hour = x_date.hour
    elif y_date is not None:
        current_hour = y_date.hour
    else:
        pass

    if prev_hour != current_hour:
        logging.info("Advanced to hour %d" % current_hour)

    return current_hour


if __name__ == "__main__":
    main()