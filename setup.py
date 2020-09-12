#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Turku University (2020) Department of Future Technologies
# Course Virtualization / Website
# Flask Application setup
#
# setup.py - Jani Tammi <jasata@utu.fi>
#
#   2020-01-01  Initial version.
#   2020-01-02  Import do_or_die() from old scripts.
#   2020-01-02  Add database creation.
#   2020-01-02  Add overwrite/force parameter.
#   2020-01-02  Add cron job create.
#   2020-01-02  Add cron job detection and removal.
#   2020-01-02  Fix do_or_die() to handle script input.
#   2020-01-02  Add stdout and stderr output to do_or_die().
#   2020-01-08  Add download config items into flask app instance file.
#   2020-01-29  Drop Python requirement to v.3.6 (due to vm.utu.fi).
#   2020-01-30  GITUSER (owner of this file) resolved. Theory is that owner is
#               the same account that pulled/cloned this repo. This same
#               account is assumed to be the "maintainer" and is used as the
#               owner for files created by this script.
#   2020-09-11  Modified cron job creation code, added ability to configure
#               crontab scheduling (in the cronjobs dictionary) and option
#               to install cron jobs to specified user (see 'cronjobs' dict).
#
#
#   ==> REQUIRES ROOT PRIVILEGES TO RUN! <==
#
#
#   1. Creates instance/application.conf
#   2. Creates application.sqlite3
#   3. If DEV, inserts test data into application.sqlite3
#   4. Creates cron jobs
#
#
#   IMPORTANT NOTE!
#           While the execution of this script requires root privileges,
#           another, equally important local user is the "maintainer".
#           It is assumed that it will be the same local user who pulled/cloned
#           this repository and thus, the same user who is the owner of this
#           script file.
#
#           This local user will be awarded with the ownership of the new files
#           created by this script (which should mean that the new files have
#           the same owner as the files pulled from the repository).
#           Maintainer (local user) will also run the cron jobs
#  NOTE !!! UNLESS the local user is root, in which case, 'www-data' user will
#           run the cron jobs.
#
#           Root user is expected to be the maintainer for production instance.
#           This way, root user's RSA ID can be used as a Deploy Key in GitHub
#           while DEV / UAT instance user(s) can have keys that enable pushes.
#
# .config for this script
#       You *must* have "[System]" section at the beginning of the file.
#       You make write any or all the key = value properties you find in the
#       'details' dictionary's sub-dictionaries.
#       NOTE: Boolean values are problematic. I haven't decided how to handle
#             them yet... For parameters that get written out to the instance
#             configuration file, they are fine - because they will be written
#             as strings anyway.
#             BUT(!!) for 'overwrite' this is an unsolved issue.
#

# Requires Python 3.6+ (f-strings, ordered dictionaries)
# IMPORTANT! CANNOT be pre-3.6 due to reliance on ordered dicts!!
REQUIRE_PYTHON_VER = (3, 6)


import re
import os
import sys

if sys.version_info < REQUIRE_PYTHON_VER:
    import platform
    print(
        "You need Python {}.{} or newer! ".format(
            REQUIRE_PYTHON_VER[0],
            REQUIRE_PYTHON_VER[1]
        )
    )
    print(
        "You have Python ver.{} on {} {}".format(
            platform.python_version(),
            platform.system(),
            platform.release()
        )
    )
    print(
        "Are you sure you did not run 'python {}' instead of".format(
            os.path.basename(__file__)
        ),
        end = ""
    )
    print(
        "'python3 {}' or './{}'?".format(
            os.path.basename(__file__),
            os.path.basename(__file__)
        )
    )
    os._exit(1)


# PEP 396 -- Module Version Numbers https://www.python.org/dev/peps/pep-0396/
__version__ = "0.9.1"
__author__  = "Jani Tammi <jasata@utu.fi>"
VERSION = __version__
HEADER  = """
=============================================================================
University of Turku, Department of Future Technologies
Course Virtualization Project
vm.utu.fi Setup Script
Version {}, 2020 {}
""".format(__version__, __author__)


import pwd
import grp
import logging
import sqlite3
import argparse
import subprocess
import configparser

# vm.utu.fi project folder, commonly ['vm.utu.fi', 'vm-dev.utu.fi']
# This script is in the project root, so we get the path to this script
ROOTPATH = os.path.split(os.path.realpath(__file__))[0]
# Local account that pulled/clones the repository = owner of this file
GITUSER  = pwd.getpwuid(os.stat(__file__).st_uid).pw_name


#
# CONFIGURATION
#
#   Modify the values in this dictionary, if needed.
#
defaults = {
    'choices':                      ['DEV', 'UAT', 'PRD'],
    'common': {
        'mode':                     'PRD',
        'upload_folder':            ROOTPATH + '/uploads',
        'upload_allowed_ext':       ['ova', 'zip', 'img'],
        'download_folder':          '/var/www/downloads',
        'download_urlpath':         '/x-accel-redirect/',
        'sso_cookie':               'ssoUTUauth',
        'sso_session_api':          'https://sso.utu.fi/sso/json/sessions/',
        'overwrite':                False   # Force overwrite on existing files?
    },
    'DEV': {
        'mode':                     'DEV',
        'debug':                    True,
        'explain_template_loading': True,
        'log_level':                'DEBUG',
        'session_lifetime':         1,
        'overwrite':                True
    },
    'UAT': {
        'mode':                     'UAT',
        'debug':                    False,
        'explain_template_loading': False,
        'log_level':                'INFO',
        'session_lifetime':         30
    },
    'PRD': {
        'mode':                     'PRD',
        'debug':                    False,
        'explain_template_loading': False,
        'log_level':                'ERROR',
        'session_lifetime':         30,
        'overwrite':                False
    }
}


# If in doubt, use: https://crontab.guru/#0_3/3_*_*_*
# See also class CronJob
# NOTE: 'script' cannot start with '/' character - it has to be
#       a path relative to the execution directory of this script.
cronjobs = {
    'remove failed uploads': {
        'script':   'cron.job/remove-failed-uploads.py',
        'schedule': '0 3 * * *'         # At 03:00 every day
    },
    'calculate SHA1 checksums':
    {
        'script':   'cron.job/calculate-checksum.py',
        'schedule': '*/5 * * * *'       # Every 5 minutes
    },
    'assemble flow chunks':
    {
        'script':   'cron.job/flow-upload-processor.py',
        'schedule': '*/1 * * * *',      # Every minute
        'user':     'www-data'
    }
}

class CronJob():

    def __init__(self, script: str, schedule: str, user: str = None):
        """."""
        self.script = os.path.join(
            # NOT working directory, but directory for this script!
            os.path.dirname(os.path.realpath(__file__)),
            script
        )
        self.schedule = schedule
        self.user = user


    def remove(self):
        usr = "-u " + self.user if self.user else ""
        cmd =  f"crontab {usr} -l 2>/dev/null | "
        cmd += f"grep -v '{self.script}' | crontab {usr} -"
        CronJob.subprocess(cmd, shell = True)


    def create(self, force: bool = False):
        if self.exists:
            if force:
                self.remove()
            else:
                raise ValueError(
                    f"Job '{self.script}' already exists!"
                )
        #self.script += " -with args"
        usr = "-u " + self.user if self.user else ""
        cmd = f'(crontab {usr} -l 2>/dev/null; echo "{self.schedule} '
        cmd += f'{self.script} >/dev/null 2>&1") | crontab {usr} -'
        CronJob.subprocess(cmd, shell = True)


    @property
    def exists(self) -> bool:
        """Argument is script name."""
        usr = "-u " + self.user if self.user else ""
        pipe = subprocess.Popen(
            f'crontab {usr} -l 2> /dev/null',
            shell = True,
            stdout = subprocess.PIPE
        )
        for line in pipe.stdout:
            if self.script in line.decode('utf-8'):
                return True
        return False


    @staticmethod
    def subprocess(
        cmd: str,
        shell: bool = False,
        stdout = subprocess.DEVNULL,
        stderr = subprocess.DEVNULL
    ):
        """Call do_or_die("ls", stdout = subprocess.PIPE), if you want output. Otherwise / by default the output is sent to /dev/null."""
        if not shell:
            # Set empty double-quotes as empty list item
            # Required for commands like; ssh-keygen ... -N ""
            cmd = ['' if i == '""' or i == "''" else i for i in cmd.split(" ")]
        prc = subprocess.run(
            cmd,
            shell  = shell,
            stdout = stdout,
            stderr = stderr
        )
        if prc.returncode:
            raise ValueError(
                f"code: {prc.returncode}, command: '{cmd}'"
            )
        # Return output (stdout, stderr)
        return (
            prc.stdout.decode("utf-8") if stdout == subprocess.PIPE else None,
            prc.stderr.decode("utf-8") if stderr == subprocess.PIPE else None
        )



class ConfigFile:
    """As everything in this script, assumes superuser privileges. Only filename and content are required. User and group will default to effective user and group values on creation time and permissions default to common text file permissions wrxwr-wr- (0o644).
    Properties:
    name            str     Full path and name
    owner           str     Username ('pi', 'www-data', etc)
    group           str     Group ('pi', ...)
    uid             int     User ID
    gid             int     Group ID
    permissions     int     File permissions. Use octal; 0o644
    content         str     This class was written to handle config files

    Once properties and content are satisfactory, write the file to disk:
    myFile = File(...)
    myFile.create(overwrite = True)
    If you wish the write to fail when the target file already exists, just leave out the 'overwrite'.
    """
    def __init__(
        self,
        name: str,
        content: str,
        owner: str = None,          # None defaults to EUID
        group: str = None,          # None defaults to EGID
        permissions: int = 0o644
    ):
        # Default to effective UID/GID
        owner = pwd.getpwuid(os.geteuid()).pw_name if not owner else owner
        group = grp.getgrgid(os.getegid()).gr_name if not group else group
        self.name           = name
        self._owner         = owner
        self._group         = group
        self._uid           = pwd.getpwnam(owner).pw_uid
        self._gid           = grp.getgrnam(group).gr_gid
        self.permissions    = permissions
        self.content        = content


    def create(self, overwrite = False, createdirs = True):
        def createpath(path, uid, gid, permissions = 0o775):
            """Give path part only as an argument"""
            head, tail = os.path.split(path)
            if not tail:
                head, tail = os.path.split(head)
            if head and tail and not os.path.exists(head):
                try:
                    createpath(head, uid, gid)
                except FileExistsError:
                    pass
                cdir = os.curdir
                if isinstance(tail, bytes):
                    cdir = bytes(os.curdir, 'ASCII')
                if tail == cdir:
                    return
            try:
                os.mkdir(path, permissions)
                # This is added - ownership equal to file ownership
                os.chown(path, uid, gid)
            except OSError:
                if not os.path.isdir(path):
                    raise
        # Begin create()
        if createdirs:
            path = os.path.split(self.name)[0]
            if path:
                createpath(path, self._uid, self._gid)
                #os.makedirs(path, exist_ok = True)
        mode = "x" if not overwrite else "w+"
        with open(self.name, mode) as file:
            file.write(self.content)
        os.chmod(self.name, self.permissions)
        os.chown(self.name, self._uid, self._gid)


    def replace(self, key: str, value: str):
        self.content = self.content.replace(key, value)


    @property
    def owner(self) -> str:
        return self._owner
    @owner.setter
    def owner(self, name: str):
        self._uid           = pwd.getpwnam(name).pw_uid
        self._owner         = name


    @property
    def group(self) -> str:
        return self._group
    @group.setter
    def group(self, name: str):
        self._gid           = grp.getgrnam(name).gr_gid
        self._group         = name


    @property
    def uid(self) -> int:
        return self._uid
    @uid.setter
    def uid(self, uid: int):
        self._uid           = uid
        self._owner         = pwd.getpwuid(uid).pw_name


    @property
    def gid(self) -> int:
        return self._gid
    @gid.setter
    def gid(self, gid: int):
        self._gid           = gid
        self._group         = grp.getgrgid(gid).gr_name


    def __str__(self):
        return "{} {}({}).{}({}) {} '{}'". format(
            oct(self.permissions),
            self._owner, self._uid,
            self._group, self._gid,
            self.name,
            (self.content[:20] + '..') if len(self.content) > 20 else self.content
        )


files = {}

files['application.conf'] = ConfigFile(
    ROOTPATH + '/instance/application.conf',
    """
# -*- coding: utf-8 -*-
#
# Turku University (2019) Department of Future Technologies
# Website for Course Virtualization Project
# Flask application configuration
#
# application.conf - Jani Tammi <jasata@utu.fi>
#
#   0.1.0   2019.12.07  Initial version.
#   0.2.0   2019.12.23  Updated for SSO implementation.
#   0.3.0   2020.01.01  Generated format.
#   0.4.0   2020.01.08  Download configuration items added.
#
#
# See https://flask.palletsprojects.com/en/1.1.x/config/ for details.
#
#
import os

DEBUG                    = {{debug}}
EXPLAIN_TEMPLATE_LOADING = {{explain_template_loading}}

TOP_LEVEL_DIR            = os.path.abspath(os.curdir)
BASEDIR                  = os.path.abspath(os.path.dirname(__file__))

SESSION_COOKIE_NAME      = 'FLASKSESSION'
SESSION_LIFETIME         = {{session_lifetime}}
SECRET_KEY               = {{secret_key}}


#
# Single Sign-On session validation settings
#
SSO_COOKIE              = '{{sso_cookie}}'
SSO_SESSION_API         = '{{sso_session_api}}'


#
# Flask app logging
#
LOG_FILENAME             = 'application.log'
LOG_LEVEL                = '{{log_level}}'


#
# SQLite3 configuration
#
SQLITE3_DATABASE_FILE   = 'application.sqlite3'


#
# File upload and download
#
UPLOAD_FOLDER           = '{{upload_folder}}'
UPLOAD_ALLOWED_EXT      = {{upload_allowed_ext}}
DOWNLOAD_FOLDER         = '{{download_folder}}'
DOWNLOAD_URLPATH        = '{{download_urlpath}}'

# EOF

""",
    GITUSER, 'www-data'
)


###############################################################################
#
# General functions
#
def file_exists(file: str) -> bool:
    """Accepts path/file or file and tests if it exists (as a file)."""
    if os.path.exists(file):
        if os.path.isfile(file):
            return True
    return False



def do_or_die(
    cmd: str,
    shell: bool = False,
    stdout = subprocess.DEVNULL,
    stderr = subprocess.DEVNULL
):
    """Call do_or_die("ls", stdout = subprocess.PIPE), if you want output. Otherwise / by default the output is sent to /dev/null."""
    if not shell:
        # Set empty double-quotes as empty list item
        # Required for commands like; ssh-keygen ... -N ""
        cmd = ['' if i == '""' or i == "''" else i for i in cmd.split(" ")]
    prc = subprocess.run(
        cmd,
        shell  = shell,
        stdout = stdout,
        stderr = stderr
    )
    if prc.returncode:
        raise ValueError(
            f"code: {prc.returncode}, command: '{cmd}'"
        )
    # Return output (stdout, stderr)
    return (
        prc.stdout.decode("utf-8") if stdout == subprocess.PIPE else None,
        prc.stderr.decode("utf-8") if stderr == subprocess.PIPE else None
    )


##############################################################################
#
# MAIN
#
##############################################################################

if __name__ == '__main__':

    #
    # Commandline arguments
    #
    parser = argparse.ArgumentParser(
        description     = HEADER,
        formatter_class = argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        '-m',
        '--mode',
        help    = "Instance mode. Default: '{}'".format(
            defaults['common']['mode']
        ),
        choices = defaults['choices'],
        dest    = "mode",
        default = defaults['common']['mode'],
        type    = str.upper,
        metavar = "MODE"
    )
    parser.add_argument(
        '--config',
        help    = "Configuration file.",
        dest    = "config_file",
        metavar = "CONFIG_FILE"
    )
    parser.add_argument(
        '-q',
        '--quiet',
        help    = 'Do not display messages.',
        action  = 'store_true',
        dest    = 'quiet'
    )
    parser.add_argument(
        '-f',
        '--force',
        help    = 'Overwrite existing files.',
        action  = 'store_true',
        dest    = 'force'
    )
    args = parser.parse_args()



    #
    # Require root user
    # Checked here so that non-root user can still get help displayed
    #
    if os.getuid() != 0:
        parser.print_help(sys.stderr)
        print("ERROR: root privileges required!")
        print(
            "Use: 'sudo {}' (alternatively 'sudo su -' or 'su -')".format(
                App.Script.name
            )
        )
        os._exit(1)


    #
    # Read config file, if specified
    #
    if args.config_file:
        cfgfile = configparser.ConfigParser()
        if file_exists(args.config_file):
            try:
                cfgfile.read(args.config_file)
            except Exception as e:
                print("read-config():", e)
                os._exit(-1)
            #finally:
            #    print({**cfgfile['System']})
        else:
            print(f"Specified config file '{args.config_file}' does not exist!")
            os._exit(-1)
    else:
        cfgfile = {'System': {}}


    #
    # Combine configuration values
    #
    cfg = {**defaults['common'], **defaults[args.mode], **cfgfile['System']}
    # Add special value; generated SECRET_KEY
    cfg['secret_key'] = os.urandom(24)
    # Unfortunately, argparse object cannot be merged (it's not a dictionary)
    if args.force:
        # Could not test against None, as the 'action=store_true' means that
        # this option value is ALWAYS either True or False
        cfg['overwrite'] = args.force


    # TODO: REMOVE THIS DEV TIME PRINT
    #from pprint import pprint
    #pprint(cfg)


    #
    # Set up logging
    #
    logging.basicConfig(
        level       = logging.INFO,
        filename    = "setup.log",
        format      = "%(asctime)s.%(msecs)03d %(levelname)s: %(message)s",
        datefmt     = "%H:%M:%S"
    )
    log = logging.getLogger()
    if not args.quiet:
        log.addHandler(logging.StreamHandler(sys.stdout))



    try:
        #
        # Create instance config
        #
        log.info("Creating configuration file for Flask application instance")
        log.info(files['application.conf'].name)
        for key, value in cfg.items():
            files['application.conf'].replace(
                '{{' + key + '}}',
                str(value)
            )
        # Write out the file
        files['application.conf'].create(overwrite = cfg['overwrite'])



        #
        # Create application.sqlite3
        #
        script_file     = ROOTPATH + '/create.sql'
        devscript_file  = ROOTPATH + '/insert_dev.sql'
        database_file   = ROOTPATH + '/application.sqlite3'
        log.info("Creating application database")
        # Because sqlite3.connect() has no open mode parameters
        if cfg['overwrite']:
            os.remove(database_file)
        with    open(script_file, "r") as file, \
                sqlite3.connect(database_file) as db:
            script = file.read()
            cursor = db.cursor()
            try:
                cursor.executescript(script)
                db.commit()
            except Exception as e:
                log.exception(str(e))
                log.error("SQL script failed!")
                raise
            finally:
                cursor.close()
        #
        # Insert Development Data (for DEV setup)
        #
        if cfg['mode'] == 'DEV':
            with    open(devscript_file, "r") as file, \
                    sqlite3.connect(database_file) as db:
                script = file.read()
                cursor = db.cursor()
                try:
                    cursor.executescript(script)
                    db.commit()
                except Exception as e:
                    log.exception(str(e))
                    log.error("SQL script failed!")
                    raise
                finally:
                    cursor.close()
        do_or_die(f"chown {GITUSER}.www-data {database_file}")
        do_or_die(f"chmod 664 {database_file}")



        #
        # Create cron jobs
        #
        # Required cronjobs dictionary format:
        #   { 'titlestring':
        #       {'script': str, 'schedule': str[,'user': str]},
        #       ... 
        #   }
        # 'script'      filepath relative to the path of this script
        # 'schedule'    crontab "* * * * *" format
        # 'user'        (optional) to run cron job as user (other than root)
        for title, jobDict in cronjobs.items():
            cronjob = CronJob(**jobDict)
            if cronjob.exists:
                if cfg['overwrite']:
                    cronjob.remove()
                    log.info(f"Pre-existing job '{title}' removed")
                else:
                    log.error(f"Job '{title}' already exists")
                    raise ValueError(
                        f"Job '{title}' already exists!"
                    )
            log.info(f"Creating cron job to {title}")
            cronjob.create()


    except Exception as e:
        msg = "SETUP DID NOT COMPLETE SUCCESSFULLY!"
        if args.quiet:
            print(msg)
            print(str(e))
        else:
            log.exception(msg)


    else:
        log.info("Setup completed successfully!")


# EOF
