#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Turku University (2020) Department of Future Technologies
# Course Virtualization / Website / Cron Jobs
# Calculate SHA1 Checksums for VM Images
#
# calculate-checksum.py - Jani Tammi <jasata@utu.fi>
#   2020-01-02  Initial version
#   2020-01-02  Parallerized processing
#   2020-01-03  Add os.nice()
#   2020-01-03  Slight improvements to error reporting
#   2020-09-13  Run as 'www-data' instead of root
#   2020-09-18  Config file now 'site.conf'.
#
#   - Job added to crontab by 'setup.py'.
#   - Logging to syslog.
#   - Must be executed as 'www-data'.
#
#
#   1) Script SELECTs all 'file' table rows that have NULL 'sha1' column
#   2) multiprosessing.Queue() is loaded with Task objects (id, filename)
#      and
#      'sha1' row is updated with a string about sheduled SHA1 calculation
#   3) Worker objects created (parallerization)
#      See "Each Worker"
#   4) While any Workers exist:
#       a) Fetch Task from Result Queue
#       b) If Task.id is NULL, worker exited (decrement alive Worker count)
#       c) If Task.result is NULL, SHA1 failed (log error)
#       d) Else SHA1 calculated OK
#
#   Each Worker:
#       1) Fetch Task object from Queue
#       2) If Task.id (and filename) are not NULL - Execute Task object:
#           TASK:
#           - Open file and feed it to hashlib.sha1() in chunks for SHA1
#           - Update 'file' table 'sha1' column with SHA1 value.
#           - Return
#       3) Put Task object into Result Queue
#       4) If Task was NULL, EXIT. Else goto step 1.
#
import os
import pwd
import sys
import logging
import logging.handlers
import sqlite3

import multiprocessing
from multiprocessing import Process

# pylint: disable=undefined-variable

# Unprivileged os.nice() values: 0 ... 20 (= lowest priority)
NICE        = 20
EXECUTE_AS      = "www-data"
LOGLEVEL        = logging.INFO  # logging.[DEBUG|INFO|WARNING|ERROR|CRITICAL]
CONFIG_FILE     = "site.conf" # All instance/site specific values

# Settings specific for this script (and, unlikely to change)
TABLE       = 'file'
PKCOLUMN    = 'id'
SHA1COLUMN  = 'sha1'
NAMECOLUMN  = 'name'

SCRIPTNAME  = os.path.basename(__file__)



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


#
# Task calculates SHA1 for *one* file and nothing else.
# Poison pill method is used (NULL work data
# triggers the Task to exit/"die").
#
class Task(object):
    id          = None
    filename    = None
    result      = None


    # default as Poison Pill (None values)
    def __init__(self, id = None, filename = None):
        self.id         = id
        self.filename   = filename


    def __call__(self, db):
        def sha1(filename: str) -> str:
            """Return SHA1 checksum for given file, in hex format."""
            import hashlib
            # BUF_SIZE is totally arbitrary. Anywhere between 64kB and 1MB ??
            BUF_SIZE = 1024 * 1024
            sha1 = hashlib.sha1()
            with open(filename, 'rb') as f:
                while True:
                    data = f.read(BUF_SIZE)
                    if not data:
                        break
                    sha1.update(data)
            return sha1.hexdigest()
        #    1. Update the row with process number
        #       This way a long-running calculation is not started again
        #       for the same missing checksum
        #    2. Calculate checksum
        #    3. Update the row with the actual checksum.
        update = f"UPDATE {TABLE} SET {SHA1COLUMN} = ? WHERE {PKCOLUMN} = ?"
        try:
            # Using worker's database connection
            cursor = db.cursor()
            self.result = sha1(DOWNLOAD_DIR + '/' + self.filename)
            # Update with actual SHA1 value
            cursor.execute(update, [self.result, self.id])
            if cursor.rowcount != 1:
                raise ValueError("None or too many rows updated!")
        except Exception as e:
            db.rollback()
            log.exception(f"Task failure for file '{self.filename}'")
            try:
                # Restore NULL so that another process will do this
                cursor.execute(update, [None, self.id])
            except Exception:
                pass
        finally:
            db.commit()
            cursor.close()
        # In case of an exception, this could still be None
        return self.result


    def __str__(self):
        """
        Explain the task and show variables. Used by Worker.run() when logging.
        """
        return f"id: '{self.id}', filename '{self.filename}' result: '{self.result or '(task has not been completed)'}'"




class Worker(multiprocessing.Process):
    db          = None
    qTask       = None
    qResult     = None
    taskCount   = 0
    #
    # On creation, Worker(Process) receives two queues:
    #   One for retrieving new work (tasks)
    #   Another for storing the tasks as results
    #
    def __init__(self, qTask, qResult):
        super().__init__()
        self.qTask      = qTask
        self.qResult    = qResult


    def run(self):
        # Be nice
        os.nice(NICE)
        log = logging.getLogger(
            os.path.basename(__file__) + ":" + \
            self.__class__.__name__ + "." + \
            sys._getframe().f_code.co_name + "()"
        )
        # Open connections cannot be shared by different processes
        self.db = sqlite3.connect(DATABASE)
        while True:
            # Retrieve a Task object (blocks until task becomes available)
            task = self.qTask.get()
            # Poison pill (values are 'None') means shutdown
            if task.id is None and task.filename is None:
                log.debug("{}: Exiting".format(self.name))
                # Put empty task into queue to signal Worker exit
                # ...but also pass the task count as a result
                task.result = self.taskCount
                self.qResult.put(task)
                break # end while-loop (terminate this worker)
            # perform the task, using Worker's DB connection
            r = task(self.db)
            log.debug(f"{self.name}: {str(task)}")
            self.qResult.put(task)
            self.taskCount += 1
        # Breaks here to exit
        return


def tag_file(db, id: int) -> bool:
    """Write a message into 'sha1' column so that the same row will not be picked up as a task by the next cron job starting."""
    import datetime
    success = True
    sql = f"UPDATE {TABLE} SET {SHA1COLUMN} = ? WHERE {PKCOLUMN} = ?"
    try:
        cursor = db.cursor()
        # Tag the row with PID to "protect" it against
        # other cron job instances
        msg = f"SHA1 checksum calculation for this file has been scheduled "
        msg += f"on {datetime.datetime.now().isoformat()}"
        cursor.execute(sql, [msg, id])
        if cursor.rowcount != 1:
            raise ValueError("None or too many rows updated!")
        db.commit()
        cursor.close()
    except Exception as e:
        db.rollback()
        success = False
    finally:
        cursor.close()
    return success


if __name__ == '__main__':

    #
    # Set up logging
    #
    log = logging.getLogger(SCRIPTNAME)
    log.setLevel(logging.INFO)
    handler = logging.handlers.SysLogHandler(address = '/dev/log')
    handler.setFormatter(
        logging.Formatter('%(name)s: [%(levelname)s] %(message)s')
    )
    log.addHandler(handler)
    log.info(f"Executing as {pwd.getpwuid(os.geteuid()).pw_name}")


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
    try:
        log.debug(f"Reading site configuration '{CONFIG_FILE}'")
        read_config_file(CONFIG_FILE)
    except:
        log.exception(f"Error reading site configuration '{CONFIG_FILE}'")
        os._exit(-1)


    #
    # Actual work
    #
    select = f"SELECT {PKCOLUMN}, {NAMECOLUMN} FROM {TABLE} "
    select += f"WHERE {SHA1COLUMN} IS NULL"
    try:
        with sqlite3.connect(DATABASE) as db:
            selcur = db.cursor()
            result = selcur.execute(select).fetchall()
            ntasks = len(result)
            ncompleted = 0
            if ntasks:
                #
                # There is work to do! Create taskqueue
                #
                q_task      = multiprocessing.Queue()
                q_result    = multiprocessing.Queue()
                for id, name,  in result:
                    if tag_file(db, id):
                        q_task.put(Task(id, name))
                    else:
                        log.error(
                            f"Could not tag and queue ID {id}, file '{name}'!"
                        )


                # Start only as many workers as there are tasks
                # or as many as there are cores, which ever is less.
                nworkers = min(
                    multiprocessing.cpu_count(),
                    ntasks
                )
                #
                # Add one Poison Pill for each worker (None value Task)
                #
                for _ in range(nworkers):
                    q_task.put(Task())


                #
                # Create and start the workers
                #
                log.info(
                    f"Creating {nworkers} workers for {ntasks} tasks"
                )
                workers = [Worker(q_task, q_result) for _ in range(nworkers)]
                for worker in workers:
                    worker.start()


                #
                # Loop until all Workers exit or we receive ABORT command.
                #
                # Worker exit is signaled by insertion of Task.result = None
                #
                # Queue can be inserted with strings as well as Task objects.
                # We use strings to signal commands.
                #
                while nworkers:
                    q_item = q_result.get()
                    if isinstance(q_item, str):
                        if q_item == 'ABORT':
                            log.debug("ABORT command received")
                            # TODO: Worker.terminate() all - but how?
                            break
                        else:
                            # log and ignore
                            log.error(
                                f"Received unsupported command '{q_item}'"
                            )
                    elif q_item.id is None:
                        # Worker exited, passing the poison pill to result queue
                        nworkers -= 1
                        ncompleted += q_item.result
                        log.debug(
                            f"Worker exited after completing {q_item.result} tasks"
                        )
                    elif q_item.result is None:
                        # Was not poison pill, and None result = failure!
                        log.error(
                            f"SHA1 for ID {q_item.id} '{q_item.filename}' failed!"
                        )
                    else:
                        # Successful SHA1 calculation
                        log.info(
                            f"File '{q_item.filename}' SHA1: {q_item.result}"
                        )
                log.info(f"{ncompleted} checksums calculated. Exiting...")
            else: # ntasks = 0
                log.info("None of the files need SHA1 to be calculated. Bye!")


    except Exception as e:
        log.exception("Process failure! Database might need manual clean-up!")
        os._exit(-1)




# EOF
