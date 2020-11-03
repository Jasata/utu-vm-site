#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
#
#
import os
import sqlite3
from datetime import datetime, timedelta

LOGFILE     = "vm.utu.fi.access.log"
DATABASE    = "../application.sqlite3"
files = {}

class DLFile:
    def __init__(self, fsize, dt):
        self.fsize  = int(fsize, 10)
        self.dt     = dt
        self.count  = 1
    def update(self, fsize, dt):
        """Record largest size and earliest datetime."""
        fsize = int(fsize, 10)
        if fsize > self.fsize:
            self.fsize = fsize
        if dt < self.dt:
            self.dt = dt
        self.count += 1
    @property
    def downloads(self):
        return self.count
    def __repr__(self):
        return f"{self.dt} {self.count:4} {self.fsize:7}"
    @staticmethod
    def ftype(fname: str) -> str:
        if fname.lower().endswith('.ova'):
            return "vm"
        else:
            return "usb"

#
# Clear existin data
#
print("Deleting existing data...", end="", flush=True)
with sqlite3.connect(DATABASE) as db:
    cursor = db.cursor()
    cursor.execute("DELETE FROM download")
    cursor.execute("DELETE FROM downloadable")
    cursor.execute("DELETE FROM file")
print("done!")

#
# Find downloaded files. Earliest download event and largest size
#
print(f"Reading logfile '{LOGFILE}'...", end="", flush=True)
with open(LOGFILE, "r") as log:
    for n, line in enumerate(log, start=1):
        try:
            item = line.split()
            if item[5] == '"GET' and item[6].startswith('/download'):
                fname = os.path.split(item[6])[1]
                if fname.lower().endswith(('.iso', '.ova', '.img', '.zip')):
                    dt   = datetime.strptime(item[3][1:],'%d/%b/%Y:%H:%M:%S')
                    size = item[9]
                    if fname in files.keys():
                        files[fname].update(size, dt)
                    else:
                        files[fname] = DLFile(size, dt)
        except Exception as e:
            print(f"Line {n}: Unpalatable log row encountered!")
            raise
    #
    # Remove those with less than 3 downloads
    #
    files = {k:v for k, v in files.items() if v.downloads > 2}
    print(f"Found {len(files)} files!")


#
# Create 'file' records
#
print("Inserting 'file' records...", end="", flush=True)
with sqlite3.connect(DATABASE) as db:
    sql  = "INSERT INTO file (name, size, type, label, owner, created) "
    sql += "VALUES (?, ?, ?, ?, ?, ?)"
    cursor = db.cursor()
    for f, o in files.items():
        try:
            cursor.execute(
                sql,
                (
                    f,
                    o.fsize,
                    o.ftype(f),
                    f,
                    'jasata',
                    o.dt - timedelta(days = 1)
                )
            )
        except:
            db.rollback()
            raise
        else:
            db.commit()
    print("done!")


#
# Insert download events
#
print("Inserting download events...", end="", flush=True)
flist = files.keys()
counter = 0
with sqlite3.connect(DATABASE) as db, \
     open(LOGFILE, "r") as log:
    cursor = db.cursor()
    sql  = "INSERT INTO dlevent (filename, datetime, size) "
    sql += "VALUES (?, ?, ?)"

    for line in log:
        try:
            item = line.split()
            fname = os.path.split(item[6])[1]
            if  item[5] == '"GET' and \
                item[6].startswith('/download') and \
                fname in flist:

                dt = datetime.strptime(item[3][1:],'%d/%b/%Y:%H:%M:%S')
                size = item[9]
                cursor.execute(sql, (fname, dt, size))
                db.commit()
                counter += 1

        except Exception as e:
            print(f"Line {n}: Unpalatable log row encountered!")

print(f"{counter} inserted!")


#
# Print found files
#
for f, o in files.items():
    print(f"{f:60} {o}")

# EOF
