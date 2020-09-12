#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Turku University (2020) Department of Future Technologies
# Course Virtualization / Website
# Class for Course Virtualization site upload handling
#
# Upload.py - Jani Tammi <jasata@utu.fi>
#
#   2020-09-06  Initial version.
#   2020-09-07  Permission response now includes 'lastchunk'.
#   2020-09-12  Development frozen for now...
#
#   SEE /js/vmupload.js (the counter part for this development)
#   ALTERNATIVE APPROACH: Fast allocate and write to index * chunksize locations
#
#   When upload permission is given:
#       - 'upload' record is INSERT'ed
#       - "{UPLOAD_FOLDER}/{upid}" directory is created
#
#   When last chunk is accepted:
#       - Chunks are joined. (If not written-in-place)
#       - File is "prepublished()", 'file' row is written
#       - IMAGE NAME CONFLICT RESOLVING NEEDED
#       - VM file is moved to {DOWNLOAD_FOLDER}
#
import logging
import sqlite3

from flask              import g
from application        import app
from .Exception         import *
from .DataObject        import DataObject
from .Teacher           import Teacher


# DEFAULT VALUES
# 
# app.config.get('UPLOAD_ALLOWED_EXT', ['ova', 'img', 'zip'])
# app.config.get('UPLOAD_CHUNK_SIZE', 10485760)
# app.config.get('UPLOAD_MAX_SIZE', 3221225472)


# Extends api.DataObject
class Upload(DataObject):


    def __init__(self):
        self.cursor = g.db.cursor()
        # Init super for table name 'upload'
        super().__init__(self.cursor, 'upload')



    def get_permission(self, request, uid: str) -> tuple:
        """uid (owner) must identify an active teacher. Expects Request to contain query parameters; 'filename' and 'filesize'. uid argument is expected to be an active teacher. If 'upload' record already exists for {owner, filename} AND the size matches, the existing permission is returned. If filesize does not match, Conflict error is returned. If no 'upload' record exists for {owner, filename}, new record is created and permission for the new upid is returned."""
        required = ("filename", "filesize")


        #
        # uid must be an active Teacher
        #
        try:
            teacher = Teacher(uid)
        except Exception as e:
            raise InvalidArgument(
                "Upload().get_permission(): Not a teacher!" + str(e)
            ) from None
        if not teacher.active:
            raise InvalidArgument(
                "Upload().get_permission(): Teacher is not active!"
            )


        #
        # Request query parameters
        #
        if not request.args:
            raise InvalidArgument(
                "Upload().get_permission(): Request has no query parameters!"
            )
        try:
            # Only required items
            upreq = { k: v for k, v in request.args.items() if k in required }
            upreq['filesize'] = int(upreq['filesize'])
        except Exception as e:
            app.logger.exception(
                "Upload().get_permission(): Error getting query parameters"
            )
            raise InvalidArgument(
                "Argument parsing error",
                {'request.args' : request.args, 'exception' : str(e)}
            ) from None
        """
        if not request.json:
            raise InvalidArgument(
                "Upload().get_permission(): Request has no JSON payload!"
            )
        try:
            # Get JSON data as dictionary
            data = json.loads(request.json)
        except Exception as e:
            app.logger.exception(
                "Upload().get_permission(): Error getting JSON data"
            )
            raise InvalidArgument(
                "Argument parsing error",
                {'request.json' : request.json, 'exception' : str(e)}
            ) from None
        # Check that all required keys exist
        """
        if not all (key in upreq for key in required):
            raise InvalidArgument("Request does not contain required data!")


        #
        # Filesize limit check
        #
        if upreq['filesize'] > app.config.get('UPLOAD_MAX_SIZE', 3221225472):
            raise InvalidArgument("File size exceeds maximum allowed!")


        #
        # Query if this upload already exists
        #
        upreq['owner']     = uid
        assert(len(upreq) == 3)
        upload = self.__getUploadRecord(upreq)
        if not upload:
            chunksize = app.config.get('UPLOAD_CHUNK_SIZE', 10485760)
            chunks = -(-upreq['filesize'] // chunksize) # same as math.ceil(a/b)
            # When creating new, 'chunksize' and 'chunklist' are also needed
            upreq.update(
                {
                    'chunksize': chunksize,
                    'chunklist': [False] * chunks
                }
            )
            upload = self.__createUploadRecord(upreq)
        else:
            # { 'filename' , 'owner' } key exists - file sizes must match
            if upload['filesize'] != upreq['filesize']:
                msg =   f"Permission for '{upreq['filename']}' " + \
                        "already exists, but is for a different file size!"
                app.logging.error(msg)
                raise InvalidArgument(msg)

        #
        # Return permission response
        #
        if app.config.get("DEBUG", False):
            # Debug mode response
            return (
                200,
                {
                    "upid"          : upload['upid'],
                    "chunksize"     : upload['chunksize'],
                    "lastchunk"     : upload['lastchunk']
                }
            )
        else:
            return (
                200,
                {
                    "upid"          : upload['upid'],
                    "chunksize"     : upload['chunksize'],
                    "lastchunk"     : upload['lastchunk']
                }
            )



    def __getUploadRecord(self, where: dict) -> dict:
        """Return 'upload' record based on where dict criteria. Return the record dictionary or None if no record found."""
        app.logger.debug(self.selectSQL(where))
        try:
            self.cursor.execute(
                self.selectSQL(where),
                where
            )
        except sqlite3.Error as e:
            app.logger.exception("upload -table SELECT failed!")
            raise
        else:
            result = self.cursor.fetchall()
            if len(result) < 1:
                return None
            else:
                return dict(zip([c[0] for c in self.cursor.description], result[0]))
        #finally:
        #    self.cursor.close()



    def __createUploadRecord(self, data: dict) -> dict:
        """Insert 'data' dictionary, returns the entire record."""
        try:
            cursor = g.db.cursor()
            cursor.execute(
                self.insertSQL(data),
                data
            )
            upid = cursor.lastrowid
        except Exception as e:
            cursor.connection.rollback()
            app.logger.exception("upload -table INSERT failed!")
            raise
        else:
            return self.__getUploadRecord({'upid': upid})
        finally:
            g.db.commit()
            cursor.close()



    def __updateUploadRecord(self, data: dict) -> dict:
        """Used to update 'lastchunk' mostly..."""
        raise ValueError("Not yet implemented!")


# EOF