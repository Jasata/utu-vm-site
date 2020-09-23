#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Turku University (2019) Department of Future Technologies
# Course Virtualization / Website
# Class for Course Virtualization site downloadables
#
# File.py - Jani Tammi <jasata@utu.fi>
#
#   2019-12-07  Initial version.
#   2019-12-28  Add prepublish(), JSONFormSchema()
#   2019-12-28  Add publish()
#   2020-08-30  Fix owner check in update()
#   2020-09-23  Add decode_bytemultiple()
#
#
#   TODO: remove _* -columns from result sets.
#
import os
import json
import time
import logging
import sqlite3
import flask

from flask              import g
from application        import app
from .Exception         import *
from .DataObject        import DataObject
from .OVFData           import OVFData
from .Teacher           import Teacher

# Pylint doesn't understand app.logger ...so we disable all these warnings
# pylint: disable=maybe-no-member

# Extends api.DataObject
class File(DataObject):


    class DefaultDict(dict):
        """Returns for missing key, value for key '*' is returned or raises KeyError if default has not been set."""
        def __missing__(self, key):
            if key == '*':
                raise KeyError("Key not found and default ('*') not set!")
            else:
                return self['*']
    # Translate file.downloadable_to <-> sso.role ACL
    # (who can access if file.downloadable_to says...)
    # Default value '*' is downloadable to noone.
    _downloadable_to2acl = DefaultDict({
        'teacher':  ['teacher'],
        'student':  ['student', 'teacher'],
        'anyone':   ['anonymous', 'student', 'teacher'],
        '*':        []
    })
    # Translate current sso.role into a list of file.downloadable_to -values
    # (what can I access with my role...)
    _role2acl = DefaultDict({
        'teacher':      ['anyone', 'student', 'teacher'],
        'student':      ['anyone', 'student'],
        '*':            ['anyone']
    })
    # Columns that must not be updated (by client)
    _readOnly = ['id', 'name', 'size', 'sha1', 'created']




    def __init__(self):
        self.cursor = g.db.cursor()
        # Init super for table name 'file'
        super().__init__(self.cursor, 'file')




    def schema(self):
        """Return file -table database schema in JSON.
        Possible responses:
        500 InternalError - Other processing error
        200 OK"""
        try:
            # Do not send owner data to client
            schema = super().schema(['owner'])
            # Set readonly columns
            for col, attribute in schema.items():
                if col in self._readOnly:
                    attribute['readonly'] = True
        except Exception as e:
            app.logger.exception("error creating JSON")
            raise InternalError(
                "schema() error while generating schema JSON", str(e)
            ) from None
        #
        # Return schema
        #
        return (200, {"schema": schema})




    def search(
        self,
        file_type: str = None,
        downloadable_to: str = None,
        owner: str = None
    ):
        """Argument 'file_type' as per column file.type, 'role' as column file.downloadable_to, 'owner' as per column file.owner."""
        app.logger.debug(
            f"search(type='{file_type}', downloadable_to='{downloadable_to}', owner='{owner}')"
        )
        self.sql = f"SELECT * FROM {self.table_name}"
        where = []  # SQL WHERE conditions and bind symbols ('?')
        bvars = []  # list of bind variables to match the above
        if file_type is not None:
            where.append("type = ?")
            bvars.append(file_type)
        if downloadable_to is not None:
            acl = self._role2acl[downloadable_to]
            where.append(
                f"downloadable_to IN ({','.join(['?'] * len(acl))})"
            )
            bvars.extend(acl)
        if owner is not None:
            where.append("owner = ?")
            bvars.append(owner)
        #
        # Create WHERE clause
        #
        if where:
            self.sql += " WHERE " + " AND ".join(where)
        app.logger.debug("SQL: " + self.sql)
        try:
            self.cursor.execute(self.sql, bvars)
        except sqlite3.Error as e:
            app.logger.exception(
                f"'{self.table_name}' -table query failed! ({self.sql})"
            )
            raise
        else:
            cursor = self.cursor
            data = [dict(zip([key[0] for key in cursor.description], row)) for row in cursor]
        finally:
            self.cursor.close()

        if app.config.get("DEBUG", False):
            return (
                200,
                {
                    "data"          : data,
                    "query" : {
                        "sql"       : self.sql,
                        "variables" : bvars
                    }
                }
            )
        else:
            return (200, {"data": data})




    def prepublish(self, filepath, owner) -> tuple:
        """Arguments 'filepath' must be an absolute path to the VM image and 'owner' must be an /active/ UID in the 'teacher' table.
        Extract information from the file and prepopulate 'file' table row. On success, returns the 'file' table ID value.
        Returns:
        (200, "{ 'id': <file.id> }")
        Exceptions:
        404, "Not Found"                NotFound()
        406, "Not Acceptable"           InvalidArgument()
        409, "Conflict"                 Conflict()
        500, "Internal Server Error")   InternalError()
        """
        self.filepath = filepath
        self.filedir, self.filename = os.path.split(self.filepath)
        _, self.filesuffix = os.path.splitext(self.filename)
        # Specified file must exist
        if not File.exists(self.filepath):
            raise NotFound(f"File '{self.filepath}' does not exist!")

        # Check that the teacher is active
        if not Teacher(owner).active:
            raise InvalidArgument(f"Teacher '{owner}' is not active!")
        app.logger.debug("File and owner checks completed!")


        # Build a dictionary where keys match 'file' -table column names
        # Populate with values either from .OVA or other
        #
        try:
            if self.filesuffix == '.ova':
                attributes = File.__ova_attributes(self.filepath)
            else:
                attributes = File.__img_attributes(self.filepath)
            # Cannot be inserted without owner
            attributes['owner'] = owner
            # File size in bytes
            attributes['size'] = os.stat(self.filepath).st_size
        except Exception as e:
            app.logger.exception("Unexpected error reading file attributes!")
            raise InternalError(
                "prepublish() error while reading file attributes", str(e)
            ) from None
        app.logger.debug("OVA/IMG attribute collection successful!")


        #
        # Data collected, insert a row
        #
        try:
            self.sql =   f"INSERT INTO file ({','.join(attributes.keys())}) "
            self.sql +=  f"VALUES (:{',:'.join(attributes.keys())})"
            self.cursor.execute(self.sql, attributes)
            # Get AUTOINCREMENT PK
            file_id = self.cursor.lastrowid
            self.cursor.connection.commit()
        except sqlite3.IntegrityError as e:
            self.cursor.connection.rollback()
            app.logger.exception("sqlite3.IntegrityError" + self.sql + str(e))
            raise Conflict("SQLite3 integrity error", str(e)) from None
        except Exception as e:
            self.cursor.connection.rollback()
            app.logger.exception("Unexpected error while inserting 'file' row!" + str(e))
            raise InternalError(
                "prepublish() error while inserting", str(e)
            ) from None


        #
        # Return with ID
        #
        if app.config.get("DEBUG", False):
            return (
                200,
                {
                    "id"            : file_id,
                    "query" : {
                        "sql"       : self.sql,
                        "variables" : attributes
                    }
                }
            )
        else:
            return (200, {"id": file_id})




    # TODO ####################################################################
    def publish(self, file_id: int) -> tuple:
        """Moves a file from uload folder to download folder and makes it accessible/downloadable."""
        return (200, { "data": "OK" })





    # TODO!! ##################################################################
    def create(self, request) -> tuple:
        """POST method handler - INSERT new row."""
        if not request.json:
            raise InvalidArgument("API Request has no JSON payload!")
        try:
            # Get JSON data as dictionary
            data = json.loads(request.json)
        except Exception as e:
            app.logger.exception("Error getting JSON data")
            raise InvalidArgument(
                "Argument parsing error",
                {'request.json' : request.json, 'exception' : str(e)}
            ) from None
        try:
            self.sql = f"INSERT INTO {self.table_name} "
            self.sql += f"({','.join(data.keys())}) "
            self.sql += f"VALUES (:{',:'.join(data.keys())})"
        except Exception as e:
            app.logger.exception("Error parsing SQL")
            raise InternalError(
                "Error parsing SQL",
                {'sql': self.sql or '', 'exception' : str(e)}
            )
        # TO BE COMPLETED!!!! #################################################




    def fetch(self, id):
        """Retrieve and return a table row. There are no restrictions for retrieving and viewing file data (but update() and create() methods do require a role)."""
        self.sql = f"SELECT * FROM {self.table_name} WHERE id = ?"
        try:
            # ? bind vars want a list argument
            self.cursor.execute(self.sql, [id])
        except sqlite3.Error as e:
            app.logger.exception(
                "psu -table query failed! ({})".format(self.sql)
            )
            raise
        else:
            # list of tuples
            result = self.cursor.fetchall()
            if len(result) < 1:
                raise NotFound(
                    f"File (ID: {id}) not found!",
                    { 'sql': self.sql }
                )
            # Create data dictionary from result
            data = dict(zip([c[0] for c in self.cursor.description], result[0]))
        finally:
            self.cursor.close()

        if app.config.get("DEBUG", False):
            return (
                200,
                {
                    "data"          : data,
                    "query" : {
                        "sql"       : self.sql,
                        "variables" : {'id': id}
                    }
                }
            )
        else:
            return (200, {"data": data})




    def update(self, id, request, owner):
        # 2nd argument must be the URI Parameter /api/file/<int:id>.
        # Second copy is expected to be found within the request data
        # and it has to match with the URI parameter.
        """
        PATCH method routine - UPDATE record
        Possible results:
        404 Not Found           raise NotFound()
        406 Not Acceptable      raise InvalidArgument()
        200 OK
        {
            'id' : <int>
        }
        """
        app.logger.debug("this.primarykeys: " + str(self.primarykeys))
        app.logger.debug("fnc arg id: " + str(id))
        if not request.json:
            raise InvalidArgument("API Request has no JSON payload!")
        else:
            data = request.json # json.loads(request.json)
        # This is horrible solution - client code should take care of this!
        data['id'] = int(data['id'])
        app.logger.debug(data)


        # Extract POST data into dict
        try:
            #
            # Primary key checking
            #
            if not data[self.primarykeys[0]]:
                raise ValueError(
                    f"Primary key '{self.primarykeys[0]}' not in dataset!"
                )
            if not id:
                raise ValueError(
                    f"Primary key value for '{self.primarykeys[0]}' cannot be None!"
                )
            if data[self.primarykeys[0]] != id:
                raise ValueError(
                    "Primary key '{self.primarykeys[0]}' values do not match! One provided as URI parameter, one included in the data set."
                )
            #
            # Check ownership
            #
            result = self.cursor.execute(
                "SELECT owner FROM file WHERE id = ?",
                [id]
            ).fetchall()
            if len(result) != 1:
                raise ValueError(
                    f"File (id: {id}) does not exist!"
                )
            else:
                if result[0][0] != owner:
                    raise ValueError(
                        f"User '{owner}' not the owner of file {id}, user '{result[0][0]}' is!"
                    )
        except Exception as e:
            app.logger.exception("Prerequisite failure!")
            raise InvalidArgument(
                "Argument parsing error",
                {'request.json' : request.json, 'exception' : str(e)}
            ) from None
        app.logger.debug("Prerequisites OK!")


        #
        # Handle byte-size variables ('disksize' and 'ram')
        # "2 GB" (etc) -> 2147483648 and so on... except when the string makes
        # no sense. Then it is used as-is instad.
        #
        if "ram" in data:
            data['ram']         = File.decode_bytemultiple(data['ram'])
        if "disksize" in data:
            data['disksize']    = File.decode_bytemultiple(data['disksize'])


        #
        # Generate SQL
        #
        try:
            # columns list, without primary key(s)
            cols = [ c for c in data.keys() if c not in self.primarykeys ]
            # Remove read-only columns, in case someone injected them
            cols = [ c for c in cols if c not in self._readOnly ]
            app.logger.debug(f"Columns: {','.join(cols)}")
            self.sql = f"UPDATE {self.table_name} SET "
            self.sql += ",".join([ c + ' = :' + c for c in cols ])
            self.sql += " WHERE "
            self.sql += " AND ".join([k + ' = :' + k for k in self.primarykeys])
        except Exception as e:
            raise InternalError(
                "SQL parsing error",
                {'sql' : self.sql or '', 'exception' : str(e)}
            ) from None
        app.logger.debug("SQL: " + self.sql)


        #
        # Execute Statement
        #
        try:
            self.cursor.execute(self.sql, data)
            #
            # Number of updated rows must be one
            #
            if self.cursor.rowcount != 1:
                nrows = self.cursor.rowcount
                g.db.rollback()
                if nrows > 1:
                    raise InternalError(
                        "Error! Update affected more than one row!",
                        {'sql': self.sql or '', 'data': data}
                    )
                else:
                    raise NotFound(
                        "Entity not found - nothing was updated!",
                        {'sql': self.sql or '', 'data': data}
                    )
        except sqlite3.Error as e:
            # TODO: Check what actually caused the issue
            raise InvalidArgument(
                "UPDATE failed!",
                {'sql': self.sql or '', 'exception': str(e)}
            ) from None
        finally:
            g.db.commit()
            self.cursor.close()

        # Return id
        return (200, {'data': {'id' : id}})



    def download(self, filename: str, role: str) -> tuple:
        """Checks that the file exists, has a database record and can be downloaded by the specified role.
        Possible return values:
        200: OK (Download started by Nginx/X-Accel-Redirect)
        401: Role not allowed to download the file
        404: Specified file does not exist
        404: Database record not found
        500: An exception ocurred (and was logged)"""
        #
        # Check that the file exists
        #
        try:
            folder = app.config.get("DOWNLOAD_FOLDER")
            filepath = os.path.join(folder, filename)
            if not File.exists(filepath):
                app.logger.error(
                    f"File '{filepath}' does not exist!"
                )
                return "File not found", 404
        except Exception as e:
            app.logger.exception(
                f"Exception while checking if '{filepath}' exists!"
            )
            return "Internal Server Error", 500
        #
        # Retrieve information on to whom is it downloadable to
        #
        self.sql = "SELECT downloadable_to FROM file WHERE name = ?"
        try:
            self.cursor.execute(self.sql, [filename])
            # list of tuples
            result = self.cursor.fetchone()
            if len(result) < 1:
                app.logger.error(
                    f"No database record for existing file '{filepath}'"
                )
                return "File Not Found", 404
        except Exception as e:
            # All other exceptions
            app.logger.exception("Error executing a query!")
            return "Internal Server Error", 500
        #
        # Send file
        #
        #   'X-Accel-Redirect' (header directive) is Nginx feature that is
        #   intercepted by Nginx and the pointed to by that directive is
        #   then streamed to the client, freeing Flask thread next request.
        #
        #   More important is the fact that this header allows serving files
        #   that are not in the request pointed location (URL), letting the
        #   application code verify access privileges and/or change the
        #   content (specify a different file in X-Accel-Redirect).
        #
        try:
            # Filepath for X-Accel-Redirect
            abs_url_path = os.path.join(
                app.config.get("DOWNLOAD_URLPATH"),
                filename
            )
            allowlist = self._downloadable_to2acl[result[0]]
            if role in allowlist:
                response = flask.Response("")
                response.headers['Content-Type'] = ""
                response.headers['X-Accel-Redirect'] = abs_url_path
                app.logger.debug(
                    f"Returning response with header X-Accel-Redirect = {response.headers['X-Accel-Redirect']}"
                )
                return response
            else:
                app.logger.info(
                    f"User with role '{role}' attempted to download '{filepath}' that is downloadable to '{allowlist}' (file.doanloadable_to: '{result[0]}') (DENIED!)"
                )
                return "Unauthorized!", 401
        except Exception as e:
            app.logger.exception(
                f"Exception while permission checking role '{role}' (downloadable_to:) '{result[0]}' and/or sending download"
            )
            return "Intermal Server Error", 500


    @staticmethod
    def decode_bytemultiple(value: str):
        mult = {
            "KB"    : 1024,
            "MB"    : 1048576,
            "GB"    : 1073741824,
            "TB"    : 1099511627776,
            "PB"    : 2214416418340864
        }
        try:
            # Assume bytes first
            return int(value, 10)
        except:
            for k, v in mult.items():
                if value.strip().upper().endswith(k):
                    try:
                        return int(float(value[:-2].replace(',', '.')) * v)
                        #return int(value[:-2], 10) * v
                    except:
                        app.logger.debug(f"Unable to convert '{value}'")
                        return value
            # multiple not found, return as-is
            return value



    @staticmethod
    def exists(file: str) -> bool:
        """Accepts path/file or file and tests if it exists (as a file)."""
        if os.path.exists(file):
            if os.path.isfile(file):
                return True
        return False




    @staticmethod
    def __ova_attributes(file: str) -> dict:
        # Establish defaults
        filedir, filename = os.path.split(file)
        attributes = {
            'name':     filename,
            'label':    filename,
            'size':     0,
            'type':     'vm'
        }
        #
        # Extract XML from .OVF -file from inside the .OVA tar-archive
        # into variable 'xmlstring'
        #
        try:
            import tarfile
            # Extract .OVF - exactly one should exist
            with tarfile.open(file, "r") as ova:
                for tarinfo in ova.getmembers():
                    if os.path.splitext(tarinfo.name)[1].lower() == '.ovf':
                        ovf = tarinfo
                        break
                if not ovf:
                    raise ValueError(".OVF file not found!!")
                xmlstring = ova.extractfile(ovf).read().decode("utf-8")
        except Exception as e:
            app.logger.exception(f"Error extracting .OVF from '{filename}'")
            return attributes
        #
        # Read OVF XML
        #
        try:
            ovfdata = OVFData(xmlstring, app.logger)
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
            app.logger.exception("Error reading OVF XML!")
        return attributes




    @staticmethod
    def __img_attributes(file: str) -> dict:
        # Images and .ZIP archives (for pendrives)
        filedir, filename = os.path.split(file)
        # Establish defaults
        attributes = {
            'name':     filename,
            'label':    filename,
            'size':     0,
            'type':     'vm'
        }
        return attributes





# EOF