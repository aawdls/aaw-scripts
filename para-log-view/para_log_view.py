#!/bin/env dls-python
import argparse, os, sys, logging, re, datetime
import para_log_view_html_template as html

def parse_arguments():
    """Parse command line arguments"""
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
    match = re.search('^\[(\w{3}.+?)\]', line)

    if match is None:
        logging.debug("No date in line %s" % line)
        return ""
    else:
        return match.group(1)

def get_date_from_line(line):
    date_string = parse_date(line)
    # Format: Sat Jan 27 09:13:38 2018
    try:
        date_obj = datetime.datetime.strptime(date_string, "%a %b %d %H:%M:%S %Y")
    except:
        date_obj = None
    return date_obj


def main():
    logging.basicConfig(level=logging.WARNING)
    args = parse_arguments()

    logging.debug("Open output file")

    index_filename = os.path.join(args.output_dir, "index.html")

    hour_filenames = []

    for hour in xrange(0, 25):
        hour_string = "%02d" % hour
        hour_filename = os.path.join(args.output_dir, "%s.html" % hour_string)
        hour_filenames.append(hour_filename)
        with open(hour_filename, "wb") as output_file:
            output_file.write(html.page_head)
            output_file.write(html.body_start)
            output_file.write(html.table_head.format(file1=args.log_filename[0],
                                                     file2=args.log_filename[
                                                         1]))

    with open(index_filename, "wb") as output_file:

        output_file.write(html.page_head)
        output_file.write(html.body_start)

        for hour in xrange(0, 25):
            hour_string = "%02d" % hour
            output_file.write('<a href="%s.html">%s</a> ' % (hour_string, hour_string))

        output_file.write(html.page_end)


    input_lines = []

    logging.debug("Opening files and loading into memory")
    longest_row = 0
    for input_path in args.log_filename:
        row_counter = 0
        logging.debug("Open %s for reading" % input_path)
        input_file = open(input_path, "rb")

        lines_from_file = []

        for line in input_file:
            lines_from_file.append(line)
            row_counter += 1

        input_lines.append(lines_from_file)

        longest_row = max([row_counter, longest_row])
        logging.debug("longest_row = %d" % longest_row)

    logging.debug("Pad lists to same length")
    for one_list in input_lines:
        one_list += [""] * (longest_row - len(one_list))

    logging.debug("At first work on 100 lines")
    x_index = 0
    y_index = 0
    current_hour = 0
    state = "start"
    for row in xrange(0, longest_row):
        if state == "start":
            # Parse one line from each file to get time
            x_line = input_lines[0][x_index]
            y_line = input_lines[1][y_index]

            x_date = get_date_from_line(x_line)
            y_date = get_date_from_line(y_line)

            # Advance the hour if necessary
            if x_date is None:
                if y_date is None:
                    pass
                else:
                    current_hour = y_date.hour
            else:
                current_hour = x_date.hour


            # Open correct file and append a line

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



    for hour_filename in hour_filenames:
        with open(hour_filename, "ab") as output_file:
            output_file.write(html.table_bottom)
            output_file.write(html.page_end)

if __name__ == "__main__":
    main()