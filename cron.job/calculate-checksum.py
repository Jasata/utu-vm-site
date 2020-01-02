#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Turku University (2020) Department of Future Technologies
# Course Virtualization / Website
# Backend cron Job - Calculate SHA1 Checksums for VM Images
#
#   calculate-checksum.py - Jani Tammi <jasata@utu.fi>
#
#   0.1.0   2020-01-02  Initial version
#   0.2.0   2020-01-02  Parallerized processing
#
#
import os
import sys
import logging
import logging.handlers
import sqlite3

import multiprocessing
from multiprocessing import Process



FILEFOLDER  = '/var/www/files'
DATABASE    = '/var/www/vm.utu.fi/application.sqlite3'
TABLE       = 'file'
PKCOLUMN    = 'id'
SHA1COLUMN  = 'sha1'
NAMECOLUMN  = 'name'        # has to be UNIQUE!

SCRIPTNAME  = os.path.basename(__file__)



#
# Task is to calculate SHA1 for one file and nothing else.
# Poison pill method (strategy where NULL work data
# triggers the Task to exit ("die"), is used.
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
        # Use worker's database connection
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
            cursor = db.cursor()
            self.result = sha1(FILEFOLDER + '/' + self.filename)
            # Update with actual SHA1 value
            cursor.execute(update, [self.result, self.id])
            if cursor.rowcount != 1:
                raise ValueError("None or too many rows updated!")
        except Exception as e:
            db.rollback()
            log.exception(f"Subprocess failure for file '{self.filename}'")
            try:
                # Restore NULL so that another process will do this
                cursor.execute(update, [None, self.id])
            except Exception:
                pass
        finally:
            db.commit()
            cursor.close()
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
                self.qResult.put(task)
                break # end while-loop (terminate this worker)
            # perform the task, using Worker's DB connection
            r = task(self.db)
            log.debug(f"{self.name}: {str(task)}")
            self.qResult.put(task)
        # Breaks here to exit
        return


def tag_file(db, id: int):
    """Write a message into 'sha1' column so that the same row will not be picked up as a task by the next cron job starting."""
    import datetime
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
    finally:
        cursor.close()



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

    # UPDATE file SET sha1 = NULL WHERE id in (5,11,12,13,14,15,16)
    # NOTE: Column 'name' is unique
    select = f"SELECT {PKCOLUMN}, {NAMECOLUMN} FROM {TABLE} "
    select += f"WHERE {SHA1COLUMN} IS NULL"
    try:
        with sqlite3.connect(DATABASE) as db:
            selcur = db.cursor()
            result = selcur.execute(select).fetchall()
            ntasks = len(result)
            if ntasks:
                #
                # There is work to do! Create taskqueue
                #
                q_task      = multiprocessing.Queue()
                q_result    = multiprocessing.Queue()
                for id, name,  in result:
                    tag_file(db, id)
                    q_task.put(Task(id, name))


                # Start only as many workers as there are tasks
                # or as many as there are cores, which ever is less.
                nworkers = min(
                    multiprocessing.cpu_count(),
                    ntasks
                )
                #
                # Add one Poison Pill for each worker
                #
                for _ in range(nworkers):
                    q_task.put(Task())


                #
                # Create and start the workers
                #
                log.info(
                    f"Creating {nworkers} workers for {ntasks} tasks")
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
                    elif q_item.result is None:
                        # Worker exited, leaving empty task item into queue
                        nworkers -= 1
                        log.debug("Worker exited after completing tasks")
                    else:
                        log.info(
                            f"File '{q_item.filename}' SHA1: {q_item.result}"
                        )

    except Exception as e:
        log.exception("Process failure")
        os._exit(-1)




# EOF
