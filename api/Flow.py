#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Turku University (2020) Department of Future Technologies
# Course Virtualization / Website
# Class for Course Virtualization site / Flow.js upload handling
#
# Flow.py - Jani Tammi <jasata@utu.fi>
#
#   2020-09-07  Initial version. Basic file-per-chunk implementation.
#   2020-09-12  Add .progress_events(), SSE implementation.
#
#
import os
import time
import json
import errno
import logging
import flask
import sqlite3
from pathlib    import Path


from flask              import g
from application        import app
from .Exception         import *


class Flow():

    def __init__(self, request):
        """Request must be Flow.js request with 'flow*' parameters."""
        # Download directory
        self.downdir = Flow.download_dir()
        # Upload directory
        self.updir = Flow.upload_dir()
        # Retrieve request values
        try:
            if request.method == 'POST':
                mdict = request.form
            else:
                mdict = request.args
            self.flowChunkNumber        = int(mdict.get('flowChunkNumber'))
            self.flowChunkSize          = int(mdict.get('flowChunkSize'))
            self.flowCurrentChunkSize   = int(mdict.get('flowCurrentChunkSize'))
            self.flowTotalSize          = int(mdict.get('flowTotalSize'))
            self.flowIdentifier         = mdict.get('flowIdentifier')
            self.flowFilename           = mdict.get('flowFilename')
            self.flowRelativePath       = mdict.get('flowRelativePath')
            self.flowTotalChunks        = int(mdict.get('flowTotalChunks'))
            self.checksum               = mdict.get('sha1', None)
        except Exception as e:
            # For debugging purposes, dump request.args and regquest.form
            for k, v in request.args.items():
                app.logger.debug(f"args '{k}' = '{v}'")
            for k, v in request.form.items():
                app.logger.debug(f"form '{k}' = '{v}'")
            app.logger.exception("Request MultiDict extraction failed!")
            raise
        # Save request for save_chunk()
        self.request = request


    @property
    def chunk_exists(self) -> bool:
        chunkfile = Path(self.__chunk_filepath())
        # app.logger.debug(
        #     f"Chunk '{self.__chunk_filepath()}' {('does not exist', 'exists')[int(chunkfile.exists())]}"
        # )
        return chunkfile.exists() and chunkfile.is_file()


    @property
    def file_exists(self) -> bool:
        """Checks for a name conflict in the DOWNLOAD_DIR."""
        flowfilepath = os.path.join(self.downdir, self.flowFilename)
        if os.path.exists(flowfilepath):
            # Still a conflict even if the existing name is not a file
            return True
        return False


    @property
    def upload_completed(self) -> bool:
        for i in range (1, self.flowTotalChunks + 1):
            if not Path(self.__chunk_filepath(i)).exists():
                return False 
        return True


    @property
    def chunk_validated(self) -> bool:
        """Assuming that client sent checksums are SHA1."""
        if not self.checksum:
            app.logger.info("No checksum! Accepted without validation...")
            return True

        # Each value in request.files[<n>] is a Werkzeug FileStorage
        # This is supposedly a thing wrapper and thus /SHOULD/ also provide
        # the standard methods such as .read() etc.
        chunk = self.request.files["file"]
        if not chunk:
            raise api.BadRequest(
                f"Cannot validate! Request does not contain 'file' (aka. 'chunk')!"
            )

        import hashlib
        # BUF_SIZE is totally arbitrary. Anywhere between 64kB and 1MB ??
        BUF_SIZE = 1024 * 1024
        sha1 = hashlib.sha1()
        try:
            while True:
                data = chunk.read(BUF_SIZE)
                if not data:
                    break
                sha1.update(data)
        finally:
            # We MUST "rewind", or chunk.save() will same zero bytes!
            chunk.seek(0)
        # Compare to client sent checksum
        if sha1.hexdigest() != self.checksum:
            app.logger.error(
                f"SHA1 ERROR: '{self.flowFilename}' chunk {self.flowChunkNumber} (client) '{self.checksum}' <> '{sha1.hexdigest()}' (server)"
            )
            return False

        app.logger.debug(
            f"SHA1: '{self.flowFilename}' chunk {self.flowChunkNumber} (client) '{self.checksum}' == '{sha1.hexdigest()}' (server)"
        )
        return True


    def save_chunk(self):
        if not self.request.method == 'POST':
            raise BadRequest("Not a POST request, cannot save a chunk!")
        # FileStorage object wrapper
        chunk = self.request.files["file"]
        if not chunk:
            raise BadRequest("Request contains no file part!")
        # Blindly write over
        chunk.save(self.__chunk_filepath())


    def __chunk_filepath(self, n = None) -> str:
        n = n or self.flowChunkNumber
        return os.path.join(
            self.updir,
            f"{self.flowIdentifier}.{n:04d}"
        )


    def create_job(self, owner: str) -> str:
        """Creates a '.job' file into the upload directory for uploaded chunks. File will contain a JSON string with the necessary parameters for a cron job to assemble the uploads and create the database entry."""
        import json
        jobfilename = os.path.join(self.updir, f"{self.flowIdentifier}.job")
        with open(jobfilename, 'w') as jobfile:
            json.dump({
                'owner':        owner,
                'filename':     self.flowFilename,
                'size':         self.flowTotalSize,
                'chunks':       self.flowTotalChunks,
                'flowid':       self.flowIdentifier
                },
                jobfile
            )


    @staticmethod
    def upload_dir() -> str:
        """Resolve, check and return upload directory for Flow"""
        # os.getcwd() resolves based on where this Flask appliation was
        # started in. All app config paths are relative to that.
        updir = app.config.get(
            'UPLOAD_FOLDER',
            os.path.join(os.getcwd(), "flow_upload")
        )
        if not (
            os.path.isdir(updir) and
            os.access(updir, os.R_OK | os.W_OK | os.X_OK)
        ):
            raise FileNotFoundError(
                errno.ENOENT,
                os.strerror(errno.ENOENT) + \
                f"Upload directory '{updir}' does not exist or not accessible?",
                updir
            )
        return updir


    @staticmethod
    def download_dir() -> str:
        """Download directory is where the VM image files are stored in."""
        downdir = app.config.get(
            'DOWNLOAD_FOLDER',
            os.path.join(os.getcwd(), "downloads")
        )
        if not (
            os.path.isdir(downdir) and
            os.access(downdir, os.R_OK | os.W_OK | os.X_OK)
        ):
            raise FileNotFoundError(
                errno.ENOENT,
                os.strerror(errno.ENOENT) + \
                f"VM Directory '{downdir}' does not exist or not accessible?",
                downdir
            )
        return downdir


    #
    # SSE - Server-Sent Events
    #
    #   Despite the disabled UWSGI buffering, the last event never seems to
    #   get sent out. Better option is to yield all events and let the client
    #   work out which event means it is time to stop listening....
    #
    @staticmethod
    def sse_upload_status(filename: str, flowid: str) -> str:
        """event: ["STATUS", "ERROR", "DONE"]
        data: {JSON}

        """
        def get_file_id(filename: str) -> int:
            with app.app_context():
                with sqlite3.connect(app.config.get('SQLITE3_DATABASE_FILE')) as db:
                    retries = 3
                    while retries:
                        try:
                            sql = "SELECT id FROM file WHERE name = :filename"
                            cursor = db.cursor()
                            result = cursor.execute(sql, locals()).fetchall()
                        except sqlite3.OperationalError:
                            retries -= 1
                            time.sleep(0.2)
                        else:
                            retries = 0
                            if len(result) > 1:
                                raise ValueError(
                                    f"Multiple results for '{filename}'!"
                                )
                            if len(result) < 1:
                                return None
                            return result[0][0]
        def exists(filepath: str) -> bool:
            if os.path.exists(filepath):
                if os.path.isfile(filepath):
                    return True
            return False
        def older(filepath: str, min: float) -> bool:
            return os.path.getmtime(filepath) < (time.time() - (min * 60))
        def event(evtType: str, payload: dict) -> str:
            return f"event: {evtType}\ndata: {json.dumps(payload)}\n\n"
        def evterror(msg: str) -> str:
            return event("ERROR", {'message': msg})
        def evtstatus(msg: str) -> str:
            return event("STATUS", {'message': msg})
        def evtdone(id: int) -> str:
            return event("DONE", {'id': id})
        import glob
        updir       = Flow.upload_dir()
        downdir     = Flow.download_dir()
        imgfilepath = os.path.join(downdir, filename)
        jobfilepath = os.path.join(updir, f"{flowid}.job")
        errfilepath = os.path.join(updir, f"{flowid}.error")
        chunkfilenamepattern = os.path.join(updir, f"{flowid}.*")
        taggedjobfilenamepattern = os.path.join(updir, f"{flowid}.job.[0-9]*")
        while True:
            if len(glob.glob(chunkfilenamepattern)) > 0:
                # We have chunks!
                if exists(jobfilepath):
                    # .job file exists
                    if older(jobfilepath, 5):
                        # ...but is older than 5 minutes
                        yield evterror(
                            "Background task is not running"
                        )
                    else:
                        # Not old enough, so we wait for the background task
                        yield evtstatus(
                            "Waiting for background task to start"
                        )
                else:
                    # No '.job' file
                    if len(glob.glob(taggedjobfilenamepattern)) > 0:
                        # Tagged job file exists
                        if exists(errfilepath):
                            # Error file found!
                            yield evterror(
                                "File prosessing has failed! Contact administration!"
                            )
                        else:
                            # if older(f"{flowid}.job.[0-9]*"), 5):
                            #    return evterror("VM image assembly overdue! Contact administration!")
                            # else:
                            #    yield evtstatus("VM image is being assembled...")
                            yield evtstatus("VM image is being assembled...")
                    else:
                        yield evterror(
                            "Incomplete download! .job file has not been created!"
                        )
            else:
                # No chunks!
                if exists(imgfilepath):
                    # image file exists!
                    file_id = get_file_id(filename)
                    if file_id:
                        # ...and it has a database record. It's done!
                        yield evtdone(file_id)
                    else:
                        # ..but no database record
                        if older(imgfilepath, 5):
                            # its too old!
                            yield evterror(
                                "Post-assembly error? Contact Administrator!"
                            )
                        else:
                            # "its perfectly natural"
                            yield evtstatus(
                                "Information being extracted from the VM image."
                            )
                else:
                    # imagefile does not exist
                    yield evterror("Invalid 'filename' and 'flowid'?")
            # delay before next loop
            time.sleep(0.3)


# EOF
