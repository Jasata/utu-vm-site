#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
#   2020-09-27  Initial version
#
#   Primarily intended to be executed by 'setup.py', but an be run manually.
#
import sqlite3

print(f"dbfilepath: '{dbfilepath}'")

events = [
   ( "CREATE",   "00 00:00:00", "test.ova", 123173, 'vm', 'jasata' ),
   ( "DOWNLOAD", "00 00:02:14", "test.ova", 0 ),
   ( "DOWNLOAD", "00 03:41:30", "test.ova", 0 ),
   ( "CREATE",   "00 03:42:41", "DTEK0068.ova", 1273611, 'vm', 'jasata')
   ( "DELETE",   "01 23:21:11", "test.ova" ),
   ( "DOWNLOAD", "02 03:02:53", "DTEK0068.ova", 0 )
]

class File():

    def __init__(
        self,
        dbfile,
        fname: str,
        fsize: int,
        ftype: str  = 'vm',
        owner: str  = 'jasta'
    ):
        self.dbfile = dbfile
        self.fname  = fname
        self.fsize  = fsize
        self.ftype  = ftype
        self.owner  = owner


    def create(self):
        #with sqlite3.connect(dbfile) as db:
        pass



    def delete(self):
        pass


    def update(self):
        pass


    def download(self):
        pass


#
# Scripts executed with exec() are in their own '__main__'
#
if __name__ == '__main__':

    with sqlite3.connect(dbfilepath) as db:


# EOF