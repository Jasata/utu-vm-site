#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Turku University (2020) Department of Future Technologies
# Course Virtualization / Website / Cron Jobs
# Create database records for files in DOWNLOAD_DIR that do not have one.
#
# import-download-folder.py - Jani Tammi <jasata@utu.fi>
#   2020-09-18  Initial version.
#
#   - Job added to crontab by 'setup.py'.
#   - Logging to syslog.
#   - Must be executed as 'www-data'.
#
#
# FUNCTIONAL DESCRIPTION
#
#   1. Scan DOWNLOAD_DIR for '.job' files (completed Flow.js uploads).
#   2. Add '.{PID}' suffix to each '.job' file to reserve them for this task.
#   3. Read '.job' JSON and assemble file into DOWNLOAD_DIR
#   4. Try extracting .OVA information.
#   5. Insert database entry.
#
#
import os
import pwd
import json
import glob
import time
import logging
import logging.handlers
import sqlite3

from OVFData import OVFData

# pylint: disable=undefined-variable

# Unprivileged os.nice() values: 0 ... 20 (= lowest priority)
NICE            = 20
EXECUTE_AS      = "www-data"
LOGLEVEL        = logging.DEBUG  # logging.[DEBUG|INFO|WARNING|ERROR|CRITICAL]
CONFIG_FILE     = "site.conf" # All instance/site specific values

# Settings specific for this script (and, unlikely to change)
OWNER           = "jmjmak"

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



def ova_attributes(filepath: str) -> dict:
    # Establish defaults
    _, filename = os.path.split(filepath)
    # Initialize required attributes
    attributes = {}
    #
    # Extract XML from .OVF -file from inside the .OVA tar-archive
    # into variable 'xmlstring'
    #
    try:
        import tarfile
        # Extract .OVF - exactly one should exist
        with tarfile.open(filepath, "r") as ova:
            for tarinfo in ova.getmembers():
                if os.path.splitext(tarinfo.name)[1].lower() == '.ovf':
                    ovf = tarinfo
                    break
            if not ovf:
                raise ValueError(".OVF file not found!!")
            xmlstring = ova.extractfile(ovf).read().decode("utf-8")
    except Exception as e:
        log.debug(f"Error extracting .OVF from '{filename}'")
        raise e
    #
    # Read OVF XML
    #
    try:
        ovfdata = OVFData(xmlstring, logger = log)
        if ovfdata.cpus:
            attributes['cores'] = ovfdata.cpus
        if ovfdata.ram:
            attributes['ram'] = ovfdata.ram
        if ovfdata.name:
            attributes['label'] = ovfdata.name
        if ovfdata.description:
            attributes['description'] = ovfdata.description
        if ovfdata.disksize:
            attributes['disksize'] = ovfdata.disksize
        if ovfdata.ostype:
            attributes['ostype'] = ovfdata.ostype
    except Exception as e:
        log.debug(
            f"Error reading OVF XML from '{filename}': {str(e)}"
        )
        raise e
    return attributes



def basic_attributes(filepath: str) -> dict:
    # Images and .ZIP archives (for pendrives)
    filedir, filename = os.path.split(filepath)
    # Establish defaults
    attributes = {
        'name':     filename,
        'label':    filename,
        'size':     os.stat(filepath).st_size,
        'type':     'vm'
    }
    return attributes


###############################################################################
#
# MAIN
#
###############################################################################
if __name__ == '__main__':

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
           f"This job must be executed as {EXECUTE_AS} (started by user '{running_as}')"
        )
        os._exit(-1)
    else:
        log.debug(f"Started! (executing as '{running_as}')")


    #
    # Read site specific configuration
    #
    log.debug(f"CWD: {os.getcwd()}")
    try:
        log.debug(f"Reading site configuration '{CONFIG_FILE}'")
        read_config_file(CONFIG_FILE)
    except:
        log.exception(f"Error reading site configuration '{CONFIG_FILE}'")
        os._exit(-1)
    # Convert ALLOWED_EXT into list
    ALLOWED_EXT = [n.strip() for n in ALLOWED_EXT.split(',')]


    #
    # Get lists from database and DOWNLOAD_DIR
    #
    log.debug(f"Getting file list from '{DOWNLOAD_DIR}'")
    folder_files = [s for s in os.listdir(DOWNLOAD_DIR) if s.endswith(tuple(ALLOWED_EXT))]
    log.debug(f"Getting file list from '{DATABASE}'")
    sql = "SELECT name FROM file"
    try:
        with sqlite3.connect(DATABASE) as db:
            db.row_factory = lambda cursor, row: row[0]
            try:
                cursor = db.cursor()
                db_files = cursor.execute(sql).fetchall()
            except sqlite3.Error as e:
                log.error(
                    f"sqlite3.Error! SQL: {sql}"
                )
                raise e
            except Exception as e:
                log.error("Non-SQL error!")
                raise e
    except Exception as e:
        log.debug(str(e))
        log.error("Error retrieving file list from database!")
        os._exit(-1)


    #
    # Orphaned
    #
    #orphaned = [x for x in folder_files if x not in db_files]
    for vmfile in [x for x in folder_files if x not in db_files]:

        start_time = time.time()
        try:

            #
            # Get attributes
            #
            _, ext = os.path.splitext(vmfile)
            vmfile = os.path.join(DOWNLOAD_DIR, vmfile)
            # Required attributes
            data = basic_attributes(vmfile)
            # Add 'owner'
            data['owner'] = OWNER
            # .OVF attributes, if an '.ova' file
            if ext.lower() == '.ova':
                try:
                    ovfdata = ova_attributes(vmfile)
                except:
                    log.error(f".OVF extraction failed from {vmfile}! Can continue...")
                else:
                    # Merge, 'ovfdata' overwrites values in 'data' dictionary
                    data = {**data, **ovfdata}


            #
            # Parse SQL
            #
            try:
                sql  = f"INSERT INTO file ({','.join(data.keys())}) "
                sql += f"VALUES (:{',:'.join(data.keys())})"
            except Exception as e:
                log.exception("Error parsing SQL!")
                continue
            #
            # Insert record
            #
            try:
                with sqlite3.connect(DATABASE) as db:
                    cursor = db.cursor()
                    cursor.execute(sql, data)
                    # Get AUTOINCREMENT PK
                    file_id = cursor.lastrowid
                    cursor.connection.commit()
            except sqlite3.IntegrityError as e:
                cursor.connection.rollback()
                log.error(
                    f"sqlite3.IntegrityError! SQL: {sql}, data: {str(data)}"
                )
                raise e
            except Exception as e:
                cursor.connection.rollback()
                log.error("Non-SQL error!")
                raise e
        except Exception as e:
            log.debug(str(e))
            log.error(f"Error while inserting 'file' row for '{vmfile}'!")
            # Try next orphaned file
            continue
        else:
            # report time
            log.info(
                f"{vmfile} (file_id: {file_id}): {(time.time() - start_time):.2f} seconds"
            )
 

# EOF
