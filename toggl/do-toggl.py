#!/bin/env python
import requests, os, time, sys, re
import argparse

def read_api_token():
    """Read user's Toggl API token from their home directory"""

    # Easy place to put it
    home_directory = os.getenv("HOME")
    token_file_path = os.path.join(home_directory, '.toggl', 'api_token')

    # Check if file exists
    if not os.path.exists(token_file_path):
        print "Can't find your API token file at %s" % token_file_path
        print "Log in to toggl, go to your account page and put it into a file at that location."
        sys.exit()

    # Read token from file, remove whitespace
    token_file = open(token_file_path, 'rb')
    api_token = token_file.readline().strip()
    token_file.close()

    return api_token

def read_PID_list():
    """Read list of user's saved PIDs from their home directory"""
    # Easy place to put it
    home_directory = os.getenv("HOME")
    projects_file_path = os.path.join(home_directory, '.toggl', 'projects.txt')

    # Check if file exists
    if not os.path.exists(projects_file_path):
        print "Can't find your list of projects at %s" % projects_file_path
        print "Create a list of project IDs and names there in this format:"
        print "name1,PID1"
        print "name2,PID2"
        sys.exit()

    projects_file = open(projects_file_path, 'rb')
    lines = projects_file.readlines()
    PID_list = {}
    for line in lines:
        match = re.search('^(.*),(\d+)$', line.strip())
        if match is None:
            print "Warning: couldn't understand line in projects file: %s" % line.strip()
        else:
            PID = int(match.group(2))
            name = match.group(1)
            PID_list[name] = PID

    return PID_list


if __name__ == "__main__":

    # Define command line arguments
    arg_parser = argparse.ArgumentParser(description="Log a time entry to Toggl")
    arg_parser.add_argument('hours', metavar='hours', type=float, help="Number of hours to log (float). e.g. 2.5")
    arg_parser.add_argument('-p', '--project', type=str, help="Identifier of the project to log to. (You define these in ~/.toggl/projects.txt). Default is no project.")
    arg_parser.add_argument('-d', '--date', type=str, help="Work date in format YYYY-MM-DD. Default is today.")
    arg_parser.add_argument('-t', '--time', type=str, help="Start time in format HH:MM. Default is 09:00.")
    arg_parser.add_argument('-m', '--message', type=str, help="Work description message.")

    # Parse arguments
    args = arg_parser.parse_args()

    # Defaults
    api_token = read_api_token()
    request_url = 'https://www.toggl.com/api/v8/time_entries'

    # List of project IDs
    if args.project is not None:
        PID_list = read_PID_list()
    if args.project not in PID_list:
        raise ValueError('That project is not in your list at ~/.toggl/projects.txt')
    else:
        use_PID = PID_list[args.project]

    # Give me the duration in hours
    duration_hours = args.hours
    duration_seconds = duration_hours * 3600.0

    # Work description
    if (args.message is not None):
        work_description = args.message
        work_description = work_description.replace('"','\"')
        work_description = work_description.replace("'", "\'")

    # Work date
    if (args.date is None):
        work_date = time.strftime("%Y-%m-%d", time.gmtime())
    else:
        match = re.search('^(\d{4})-(\d{2})-(\d{2})$',args.date)
        if match is not None:
            work_date = match.group(0)
        else:
            raise ValueError('Date is not of format YYYY-MM-DD')

    # Work time
    if (args.time is None):
        work_time = "09:00"
    else:
        match = re.search('^(\d{2}):(\d{2})$',args.time)
        if match is not None:
            work_time = match.group(0)
        else:
            raise ValueError('Time is not of format HH:SS')

    payload = '{"time_entry":{'
    if work_description is not None:
        payload += '"description":"%s",' % (work_description)
    if use_PID is not None:
        payload += '"pid":%d,' % use_PID
    payload +='"duration":%d,"start":"%sT%s:00.000Z","created_with":"do_toggl.py"}}' % (duration_seconds, work_date, work_time)


    testing = False

    if testing == True:
        print payload
    else:
        r = requests.post(request_url, auth=(api_token, 'api_token'), data=payload)
        if r.status_code == 200:
            print "Time logged successfully."
            print "Toggl said:"
            print r.text
        else:
            print "Request didn't work."
            print "HTTP Return code: %d" % r.status_code
            print "Toggl said:"
            print r.text
