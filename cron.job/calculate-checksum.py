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
#
#
import os
import logging
import logging.handlers
import sqlite3

from multiprocessing import Process



FILEFOLDER  = '/var/www/files'
DATABASE    = '/var/www/vm.utu.fi/application.sqlite3'
TABLE       = 'file'
PKCOLUMN    = 'id'
SHA1COLUMN  = 'sha1'
NAMECOLUMN  = 'name'        # has to be UNIQUE!

SCRIPTNAME  = os.path.basename(__file__)





def calculate_checksum(id, filename):
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
    import datetime
    update = f"UPDATE {TABLE} SET {SHA1COLUMN} = ? WHERE {PKCOLUMN} = ?"
    try:
        with sqlite3.connect(DATABASE) as db:
            updcur = db.cursor()
            # Tag the row with PID to "protect" it against
            # other cron job instances
            msg = f"Process ({os.getpid()}) begun calculating SHA1 checksum "
            msg += f"on {datetime.datetime.now().isoformat()}"
            updcur.execute(update, [msg, id])
            if updcur.rowcount != 1:
                raise ValueError("None or too many rows updated!")
            db.commit()
            sha1 = sha1(FILEFOLDER + '/' + filename)
            # Update with actual SHA1 value
            updcur.execute(update, [sha1, id])
            if updcur.rowcount != 1:
                raise ValueError("None or too many rows updated!")
    except Exception as e:
        db.rollback()
        log.exception(f"Subprocess failure for file '{filename}'")




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
            if len(result):
                log.info(f"{len(result)} files need SHA1")
                proclist = []
                for id, name,  in result:
                    proc = Process(
                        target  = calculate_checksum,
                        args    = (id, name)
                    )
                    proclist.append(proc)
                    proc.start()
                    calculate_checksum(id, name)
                # complete the processes
                for proc in proclist:
                    proc.join()

    except Exception as e:
        log.exception("Process failure")
        os._exit(-1)




# EOF
