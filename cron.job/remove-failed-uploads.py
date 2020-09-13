#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Turku University (2020) Department of Future Technologies
# Course Virtualization / Website / Cron Jobs
# Assemble Flow.js upload chunks and create database entry.
#
# remove-failed-uploads.py - Jani Tammi <jasata@utu.fi>
#   2020-09-13  Skeleton/framework - does not do anything yet.
#
#   - Job added to crontab by 'setup.py'.
#   - Logging to syslog.
#   - Must be executed as 'root'.
#
#
import os
import pwd
import logging
import logging.handlers

# Unprivileged os.nice() values: 0 ... 20 (= lowest priority)
NICE            = 20
EXECUTE_AS      = "root"
LOGLEVEL        = logging.INFO  # logging.[DEBUG|INFO|WARNING|ERROR|CRITICAL]
CONFIG_FILE     = "site.config" # All instance/site specific values

SCRIPTNAME = os.path.basename(__file__)



def read_config_file(cfgfile: str):
    """Reads (with ConfigParser()) '[Site]' and creates global variables. Argument 'cfgfile' has to be a filename only (not path + file) and the file must exist in the same directory as this script."""
    cfgfile = os.path.join(
        os.path.split(os.path.realpath(__file__))[0],
        cfgfile
    )
    if not os.path.exists(cfgfile):
        raise FileNotFoundError(f"Site configuration '{cfgfile}' not found!")
    import configparser
    cfg = configparser.ConfigParser()
    cfg.optionxform = lambda option: option # preserve case
    cfg.read(cfgfile)
    for k, v in cfg.items('Site'):
        globals()[k] = v



###############################################################################
#
# MAIN
#
###############################################################################
if __name__ == '__main__':

    script_start_time = time.time()
    #
    # Be nice, we're not in a hurry
    #
    os.nice(NICE)


    #
    # Set up logging
    #
    log = logging.getLogger(SCRIPTNAME)
    log.setLevel(LOGLEVEL)
    handler = logging.handlers.SysLogHandler(address = '/dev/log')
    handler.setFormatter(
        logging.Formatter('%(name)s: [%(levelname)s] %(message)s')
    )
    log.addHandler(handler)

    #
    # Resolve user and require to be executed as EXECUTE_AS
    #
    running_as = pwd.getpwuid(os.geteuid()).pw_name
    if running_as != EXECUTE_AS:
        log.error(
           f"This job must be executed as {EXECUTE_AS} (stared by user '{running_as}')"
        )
    else:
        log.debug(f"Started! (executing as '{running_as}')")


    #
    # Read site specific configuration
    #
    try:
        log.debug(f"Reading site configuration '{CONFIG_FILE}'")
        read_config_file(CONFIG_FILE)
    except:
        log.exception(f"Error reading site configuration '{CONFIG_FILE}'")
        os._exit(-1)


    #
    # ACTUAL WORK GOES HERE
    #
    try:
        log.info("NOT YET IMPLEMENTED!")
    except:
        log.exception("Process failure! Database might need manual clean-up!")
        os._exit(-1)


# EOF
