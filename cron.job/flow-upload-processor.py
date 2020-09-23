#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Turku University (2020) Department of Future Technologies
# Course Virtualization / Website / Cron Jobs
# Assemble Flow.js upload chunks and create database entry.
#
# flow-upload-processor.py - Jani Tammi <jasata@utu.fi>
#   2020-09-09  Initial version.
#   2020-09-10  OVF parsing added.
#   2020-09-12  Fixed OVFData constructor logger -argument.
#               Now writes '.error' files for failed image concatenations.
#   2020-09-13  Site specific configurations now read from CONFIG_FILE.
#   2020-09-18  Config file now 'site.conf'.
#   2020-09-23  Add SHA1 calculation
#
#   - Job added to crontab by 'setup.py'.
#   - Logging to syslog.
#   - Must be executed as 'www-data'.
#
#
# FUNCTIONAL DESCRIPTION
#
#   1. Scan UPLOAD_DIR for '.job' files (completed Flow.js uploads).
#   2. Add '.{PID}' suffix to each '.job' file to reserve them for this task.
#   3. Read '.job' JSON and assemble file into DOWNLOAD_DIR
#   4. Try extracting .OVA information.
#   5. Insert database entry.
#
#
#   If there will be a post-Flow update page that monitors / waits until this
#   task is complete, the event API endpoint must resolve the inserted row ID.
#   That should not be an issue, since all filenames are unique in DOWNLOAD_DIR
#
# PARALLERIZATION
#
#   This script is disk I/O heavy, not processing power heavy, and thus
#   significant gains are not found in parallerizing this execution.
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
LOGLEVEL        = logging.INFO  # logging.[DEBUG|INFO|WARNING|ERROR|CRITICAL]
CONFIG_FILE     = "site.conf" # All instance/site specific values

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


def exists(file: str) -> bool:
    """Accepts path/file or file and tests if it exists (as a file)."""
    if os.path.exists(file):
        if os.path.isfile(file):
            return True
    return False


def allocate(filename: str, size: int) -> str:
    """Allocates file and returns it full filepath. Argument must be file name only! Returns full filepath."""
    if '/' in filename:
        raise ValueError(
            f"allocate(): Argument must NOT contain path! ('{filename}')"
        )
    else:
        filepath = os.path.join(DOWNLOAD_DIR, filename)


    #
    # Terminate on filename conflict
    #
    if exists(filepath):
        raise ValueError(
            f"File '{filepath}' already exists!"
    )


    # Create empty target file
    # 1. Create new file
    # 2. seek to size-1 byte position
    # 3. write 1 byte
    # NOTE: Will NOT work as expected in some systems/filesystems
    #       Linux + ReiserFS will NOT allocate all the space,
    #       although it APPEARS that the file is as big as it should.
    try:
        with open(filepath, "wb") as f:
            f.seek(size - 1)
            f.write(b"\0")
        log.debug(f"allocate(): {filepath} {size} bytes")
    except Exception as e:
        # If the file was created, remove it
        try:
            os.remove(filepath)
        except:
            pass
        log.error(f"allocate(): Creating '{filepath}' failed!")
        raise e
    return filepath


def assemble_file(job: dict) -> str:
    """Assembles flow chunks into a VM image file. Returns full filepath as received from allocate()."""
    chunks = glob.glob(os.path.join(UPLOAD_DIR, f"{job['flowid']}.[0-9]*"))
    BLKSIZE = 1024 * 1024
    total = 0       # Total bytes written into target file
    # allocate raises an exception, if it fails -> terminates this function.
    try:
        tgtname = allocate(job['filename'], job['size'])
        try:
            with open(tgtname, 'wb') as tgt:
                #for cnknum in range (1, job['chunks'] + 1):
                for srcname in sorted(chunks):
                    log.debug(f"write chunk '{srcname}' to '{tgtname}'")
                    srcsize = os.stat(srcname).st_size
                    with open(srcname, 'rb') as src:
                        # Copy in BLKSIZE blocks
                        for pos in range(0, srcsize, BLKSIZE):
                            if srcsize - pos > BLKSIZE:
                                readsize = BLKSIZE
                            else:
                                readsize = srcsize - pos
                            src.seek(pos)
                            tgt.seek(total)
                            tgt.write(src.read(readsize))
                            total += readsize
        except Exception as e:
            # Remove whatever we managed to create until exception
            try:
                os.remove(tgtname)
            except:
                pass
            raise e
    except Exception as e:
        try:
            # Dump exception to an error file
            with open(f"{job['flowid']}.error", "w") as errorfile:
                errorfile.write(str(e))
        except:
            pass
        raise e
    else:
        for srcname in chunks:
            os.remove(srcname)
    return tgtname



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



def sha1(filepath: str) -> str:
    """Return SHA1 checksum for given file, in hex format."""
    import hashlib
    # BUF_SIZE is totally arbitrary. Anywhere between 64kB and 1MB ??
    BUF_SIZE = 1024 * 1024
    sha1 = hashlib.sha1()
    with open(filepath, 'rb') as f:
        while True:
            data = f.read(BUF_SIZE)
            if not data:
                break
            sha1.update(data)
    return sha1.hexdigest()



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


    #
    # Compile list of '.job' files and reserve them
    #
    log.debug(f"Looking for jobs in '{UPLOAD_DIR}'")
    pid = os.getpid()
    jobs = []
    try:
        os.chdir(UPLOAD_DIR)
        for jobfilename in glob.glob(os.path.join(UPLOAD_DIR, "*.job")):
            jobs.append(f"{jobfilename}.{pid}")
            os.rename(jobfilename, jobs[-1])
    except Exception as e:
        log.exception("Job list creation failed!")
        os._exit(-1)
    else:
        log.debug(f"Job list has {len(jobs)} tasks")


    #
    # Execute jobs
    #
    job = {}
    n_success = 0
    for jobfilename in jobs:
        job_start_time = time.time()


        #
        #   Concatenate chunks into an image file
        #
        try:
            with open(jobfilename, "r") as jsonfile:
                job = json.load(jsonfile)
            #log.debug(str(job))
            # vmfile will be full filepath
            vmfile = assemble_file(job)
        except Exception as e:
            log.error(
                f"Assembly of '{job.get('filename', '(null)')}' failed! See error file for details."
            )
            log.debug(f"Exception: {str(e)}")
            # Try next
            continue
        else:
            # Chunks assembled into image, '.job' can also be removed
            os.remove(jobfilename)


        #
        # Get attributes
        #
        _, ext = os.path.splitext(vmfile)
        # Required attributes
        data = basic_attributes(vmfile)
        # Add 'owner'
        data['owner'] = job['owner']
        # .OVF attributes, if an '.ova' file
        if ext.lower() == '.ova':
            try:
                ovfdata = ova_attributes(vmfile)
            except:
                log.error(f".OVF extraction failed from {vmfile}!")
            else:
                # Merge, 'ovfdata' overwrites values in 'data' dictionary
                data = {**data, **ovfdata}


        #
        # Calculate SHA1 checksum
        #
        try:
            data['sha1'] = sha1(vmfile)
        except:
            log.exception("Error while calculating SHA1")
            # we can ignore this, backgroud task will take care of it


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
                try:
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
            log.error("Error while inserting 'file' row!")
            # Jump to the ext job
            continue
        else:
            n_success += 1
            # report time
            log.info(
                f"{job['filename']} (file_id: {file_id}): {(time.time() - job_start_time):.2f} seconds"
            )
 
    if jobs:
        log.info(
            f"{n_success}/{len(jobs)} files processed, execution time {(time.time() - script_start_time):.2f} seconds"
        )

# EOF