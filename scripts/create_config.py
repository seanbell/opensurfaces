#!/usr/bin/env python2.7
#
# Sets up the scripts/config.sh file
#

import re
import os
import sys
import glob
import string
import socket
import readline

# script directory
DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_TEMPLATE = os.path.join(DIR, 'config_template.sh')
CONFIG = os.path.join(DIR, 'config.sh')

# responses from user
variables = {}


# tab autocomplete with file names
def complete(text, state):
    return (glob.glob(text + '*') + [None])[state]
readline.set_completer_delims(' \t\n;')
readline.parse_and_bind("tab: complete")
readline.set_completer(complete)


def prompt(var_name, default, choices, regex, no_whitespace, message):
    print ''
    print '=' * 10
    print ''
    print message.strip()
    while True:
        if choices:
            if len(choices) < 3:
                l = [default.upper()] + [c.lower() for c in choices if c != default]
            else:
                l = default
            ans = raw_input('\n  %s: [%s] ' % (var_name, '/'.join(l)))
            ans = ans.strip()
            if ans:
                return default
            elif ans in choices:
                return ans
        else:
            ans = raw_input('\n  %s: [%s] ' % (var_name, default))
            ans = ans.strip()
            if '"' in ans or "'" in ans:
                continue
            elif not ans:
                return default
            elif regex and not re.match(regex, ans):
                print "Response must match %s" % regex
                continue
            elif no_whitespace and any(c in string.whitespace for c in ans):
                print "Response cannot contain whitespace"
                continue
            else:
                return ans


def prompt_var(var_name, default, choices=[], regex=None, no_whitespace=True, message=''):
    variables[var_name] = prompt(var_name, default, choices, regex, no_whitespace, message)
    print '  %s="%s"' % (var_name, variables[var_name])


print """
This script sets up some variables and saves your responses in
'scripts/config.sh'.

Defaults are indicated in [brackets].
Press enter with no input to select the default.
You can use tab-completion for file paths.
""".strip()

if os.path.exists(CONFIG):
    print """
The configuration (config.sh) already exists; are you sure that you want to
overwrite it?  Note that you can simply edit the file (%s)
instead of use this script.
""".strip() % CONFIG
    ans = raw_input("\nAre you sure? [y/N] ")
    if not ans or ans.lower() != "y":
        sys.exit(1)


prompt_var(
    'PROJECT_NAME',
    default='opensurfaces',
    regex=r'^[a-zA-Z_][a-zA-Z0-9_]*$',
    message='''
Name for the project (used by scripts, database, S3, key prefixes, to refer to this project).
Must be a valid variable name (no spaces).
''')

while True:
    prompt_var(
        'SERVER_NAME',
        default='localhost',
        message='''
Public hostname for the webserver, or localhost if you are going to run locally.
    Correct: localhost or example.com or subdomain.example.com
    Incorrect: http://example.com or http://www.example.com
    ''')

    prompt_var(
        'SERVER_IP',
        default='127.0.0.1',
        regex=r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
        message='''
Public IP address for the webserver, or 127.0.0.1 if you are going to run locally.
    ''')

    print "Checking hostname '%s' to make sure that it resolves to %s ..." % (
        variables['SERVER_NAME'], variables['SERVER_IP'])

    try:
        resolved_ip = socket.gethostbyname(variables['SERVER_NAME'])
    except Exception as e:
        print 'Exception: %s' % e
        resolved_ip = None

    if variables['SERVER_IP'] == resolved_ip:
        print "Success: hostname and IP match"
        break
    else:
        if resolved_ip:
            print "Error: the hostname SERVER_NAME='%s' resolves to '%s', which does not match SERVER_IP='%s'" % (
                variables['SERVER_NAME'], resolved_ip, variables['SERVER_IP'])
        else:
            if variables['SERVER_NAME'] == 'localhost':
                print "The hostname 'localhost' could not be resolved; something is seriously wrong with your setup."
                print "I am guessing that the entry for 'localhost' is missing from your /etc/hosts file."
                sys.exit(1)
            else:
                print "Error: the hostname SERVER_NAME='%s' does not resolve to any IP address" % (
                    variables['SERVER_NAME'])
                print "If you are setting up a public webserver, you need to register your domain before it can be used."
                print ("If you are using a private hostname in a network (e.g. you.cs.someuniversity.edu), "
                       "make sure that your hostname is correctly set up.  You should be able to ping the "
                       "hostname and get a response.")
                print "You can always use 'localhost' until you fix your hostname"

prompt_var(
    'DATA_DIR',
    default='$REPO_DIR/data',
    message='''
Location where local data is to be stored (e.g. js, css, any locally saved images).
Note: $REPO_DIR refers to the repository directory.
''')

prompt_var(
    'BACKUP_DIR',
    default='$REPO_DIR/backup',
    message='''
Location where backups are to be stored (i.e. snapshot dumps of the database)
Note: $REPO_DIR refers to the repository directory.
''')

prompt_var(
    'DB_DIR',
    default='',
    message='''
Optional -- non-default directory for database.  Leave blank to use the Ubuntu default.

Common use case: you have an EC2 server with a small boot volume and a large
EBS disk.  In that case, set this to a directory on the mounted EBS disk.
''')

# make sure paths are not local
for f in 'BACKUP_DIR', 'DATA_DIR', 'DB_DIR':
    if (variables[f] and
            not variables[f].startswith('/') and
            not variables[f].startswith('$REPO_DIR/')):
        new_dir = '$REPO_DIR/' + variables[f]
        print "%s: %s --> %s" % (f, variables[f], new_dir)
        variables[f] = new_dir

prompt_var(
    'ADMIN_EMAIL',
    default='admin@example.com',
    message='''
Your email (for emailing stack traces when the server crashes)
''')

prompt_var(
    'ADMIN_NAME',
    default='Admin Name',
    no_whitespace=False,
    message='''
Your name (for emailing stack traces when the server crashes)
''')

# find default timezone from OS
if os.path.exists('/etc/timezone'):
    default_timezone = open('/etc/timezone').read().strip()
    if not default_timezone:
        default_timezone = 'America/New_York'

prompt_var(
    'TIME_ZONE',
    default=default_timezone,
    message='''
Time zone for server.  List of valid time zones:
    http://en.wikipedia.org/wiki/List_of_tz_database_time_zones
''')

# parse the template and replace variables with indicated values
lines = []
for line in open(CONFIG_TEMPLATE):
    l = line.strip()
    if l and not l.startswith('#') and re.match('^\s*\w+=.*$', l):
        var_name = l.split('=')[0]
        if var_name in variables:
            var_value = variables[var_name]
            if ' ' in var_value:
                lines.append('%s="%s"' % (var_name, var_value))
            else:
                lines.append('%s=%s' % (var_name, var_value))
            continue

    lines.append(l)

with open(CONFIG, 'w') as f:
    f.writelines([l + '\n' for l in lines])

print ''
print 'Done!  Saved config in: %s' % CONFIG
