#!/bin/env dls-python
import os, time, sys, re
import argparse
from pkg_resources import require

def read_api_token():
    """Read user's Toggl API token from their home directory"""

    # Easy place to put it
    home_directory = os.getenv("HOME")
    token_file_path = os.path.join(home_directory, '.toggl', 'api_token')

    # Check if file exists
    if not os.path.exists(token_file_path):
        print "Can't find your API token file at %s" % token_file_path
        print "Log in to toggl, go to your account page and put it into a file at that location."
        sys.exit(1)

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
        sys.exit(1)

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
    help_text="""Log a time entry to Toggl
  
You need to do a bit of setup to use this script.

1) mkdir ~/.toggl
2) cd ~/.toggl
3) Create the file api_token and put your API token in it. To get this,
   log in to Toggl, click on your name in the bottom left, and click Profile
   Settings. It's near the bottom of that page.
4) chmod 600 api_token
5) Create the file projects.txt to store the list of project IDs you'll use.
   Sorry this bit is fiddly, but you only have to do it once.
   To get these, in Toggl, click on Projects in the left hand menu, then find
   your favourite Toggl project in the list and click on it. It's the last part
   of the URL of that page. E.g. for I13:
   https://toggl.com/app/projects/610396/edit/5088229
   the PID is 5088229. Write one PID per line with a name you can remember,
   in the following format, e.g.:
   
   I12,5088258
   I13,5088229
   PCO,84584301
   
   You will use that name to log time to the project with the -p argument.
6) You're all set! See below for the arguments to use.

Example:
do-toggl.py 2.5 -m "Set up test with excalibur" -d 2018-01-11 -t 14:00 -p I13"""
    arg_parser = argparse.ArgumentParser(description=help_text, formatter_class=argparse.RawDescriptionHelpFormatter)
    arg_parser.add_argument('hours', metavar='hours', type=float, help="Number of hours to log (float). e.g. 2.5")
    arg_parser.add_argument('-p', '--project', type=str, help="Identifier of the project to log to. (You define these in a file, see help text.) Default is no project.")
    arg_parser.add_argument('-d', '--date', type=str, help="Work date in format YYYY-MM-DD. Default is today.")
    arg_parser.add_argument('-t', '--time', type=str, help="Start time in format HH:MM. Default is 09:00.")
    arg_parser.add_argument('-m', '--message', type=str, help="Work description message.")
    arg_parser.add_argument("-n", "--dryrun", help="Dry run - print the request we would make but don't send anything.", action="store_true")

    # Parse arguments
    args = arg_parser.parse_args()

    # Defaults
    api_token = read_api_token()
    request_url = 'https://www.toggl.com/api/v8/time_entries'

    # List of project IDs
    if args.project is not None:
        # A project is specified
        PID_list = read_PID_list()
        # Check if we recognise it
        if args.project not in PID_list:
            raise ValueError(
                'That project is not in your list at ~/.toggl/projects.txt')
        else:
            use_PID = PID_list[args.project]
    else:
        use_PID = None

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
            print 'Date should be in format YYYY-MM-DD'
            sys.exit(1)

    # Work time
    if (args.time is None):
        work_time = "09:00"
    else:
        match = re.search('^(\d{2}):(\d{2})$',args.time)
        if match is not None:
            work_time = match.group(0)
        else:
            print 'Time should be in format HH:MM'
            sys.exit(1)

    # Encode the info for our HTTP request
    payload = '{"time_entry":{'
    if work_description is not None:
        payload += '"description":"%s",' % (work_description)
    if use_PID is not None:
        payload += '"pid":%d,' % use_PID
    payload +='"duration":%d,"start":"%sT%s:00.000Z","created_with":"do_toggl.py"}}' % (duration_seconds, work_date, work_time)

    # Testing mode?
    if args.dryrun:
        print "Dry run, will not send anything."
        print payload
    else:
        # Real request
        require("requests")
        import requests
        # Suppress warnings from requests due to our old version of it
        requests.packages.urllib3.disable_warnings()

        # Do HTTP request
        r = requests.post(request_url, auth=(api_token, 'api_token'), data=payload)
        if r.status_code == 200:
            print "Time logged successfully."
            print "Toggl said:"
            print r.text
        else:
            print "Request didn't work."
            print "HTTP Return code: %d, %s" % (r.status_code, r.reason)
            print "Toggl said:"
            print r.text
            sys.exit(1) # Nonzero exit code for failure
