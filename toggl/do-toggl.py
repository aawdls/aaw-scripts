import requests, os, time, sys

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

    # Read token from file
    token_file = open(token_file_path, 'r')
    api_token = token_file.readline()
    token_file.close()

    return api_token


# Defaults
api_token = read_api_token()
request_url = 'https://www.toggl.com/api/v8/time_entries'

# List of project IDs
PID = {'I13': 5088229}
use_PID = PID['I13']

# Give me the duration in hours
duration_hours = 0.5
duration_seconds = duration_hours * 3600.0

# Work description
work_description = "Testing toggl"

# Work date
work_date = time.strftime("%Y-%m-%d", time.gmtime())

payload = '{"time_entry":{"description":"%s","duration":%d,"start":"%sT09:00:00.000Z","pid":%d,"created_with":"curl"}}' % (work_description, duration_seconds, work_date, use_PID)

testing = True

if testing == True:
    print payload
else:
    r = requests.post(request_url, auth=(api_token, 'api_token'), data=payload)
    print r.status_code
