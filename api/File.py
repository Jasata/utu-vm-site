#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Turku University (2019) Department of Future Technologies
# Course Virtualization / Website
# Class for Course Virtualization site downloadables
#
# File.py - Jani Tammi <jasata@utu.fi>
#
#   0.1.0   2019.12.07  Initial version.
#   0.2.0   2019.12.28  Add prepublish(), JSONFormSchema()
#   0.3.0   2019.12.28  Add publish()
#
#
#   TODO: remove _* -columns from result sets.
#
import os
import time
import logging
import sqlite3

from flask              import g
from application        import app
from .Exception         import *
from .DataObject        import DataObject
from .OVFData           import OVFData


# Extends api.DataObject
class File(DataObject):

    class DefaultDict(dict):
        """Returns for missing key, value for key '*' is returned or raises KeyError if default has not been set."""
        def __missing__(self, key):
            """For DefaultDict[key] access, missing keys."""
            if self.get('*', None):
                return self['*']
            raise KeyError("Neither key nor default key ('*') exist!")
    # Database column file.downloadable_to <-> sso.role
    _downloadable_to = DefaultDict({
        'teacher':  ['anyone', 'student', 'teacher'],
        'student':  ['anyone', 'student'],
        '*':        ['anyone']
    })


    def __init__(self):
        """No need to parse - no request arguments supported"""
        self.cursor = g.db.cursor()
        # Init super for table name 'file'
        super().__init__(self.cursor, 'file')




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
            acl = self._downloadable_to[downloadable_to]
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
        """Extract information from the file and prepopulate 'file' table row. Returns (200, "{ 'id': <file.id> }").
        Possible responses:
        404 NotFound - Specified file not found
        409 Conflict - SQLite3 integrity error
        500 InternalError - Other error
        200 OK"""
        self.file = filepath
        self.filedir, self.filename = os.path.split(self.file)
        _, self.filesuffix = os.path.splitext(self.filename)
        if not File.file_exists(self.file):
            raise NotFound(f"File '{self.file}' does not exist!")


        # Build a dictionary where keys match 'file' -table column names
        # Populate with values either from .OVA or other
        #
        try:
            if self.filesuffix == '.ova':
                attributes = File.__ova_attributes(self.file)
            else:
                attributes = File.__img_attributes(self.file)
            # Cannot be inserted without owner
            attributes['_owner'] = owner
            # File size in bytes
            attributes['size'] = os.stat(self.file).st_size
        except Exception as e:
            app.logger.exception("Unexpected error reading file attributes!")
            raise InternalError(
                "prepublish() error while reading file attributes", str(e)
            ) from None


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
            app.logger.exception("sqlite3.IntegrityError" + str(e))
            raise Conflict("SQLite3 integrity error", str(e)) from None
        except Exception as e:
            app.logger.exception("Unexpected error!")
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




    def schema(self):
        """Retrieve 'file' table row by provided ID and return it in JSONForm Schema format.
        Possible responses:
        404 NotFound - Table 'file' does not have a row by specified id
        500 InternalError - Other processing error
        200 OK"""
        #
        # Limit and modify schema
        #
        exclude = ['sha1', 'owner']
        readonly = ['id', 'name', 'size', 'created']
        try:
            schema = super().schema(exclude)
            # Set readonly columns
            for key, val in schema.items():
                if key in readonly:
                    val['readonly'] = True
        except Exception as e:
            app.logger.exception("error creating JSON")
            raise InternalError(
                "preprocess() error while generating JSON content", str(e)
            ) from None


        #
        # Return schema
        #
        return (200, {"schema": schema})




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
                    { 'sql': this.sql }
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



    def update(self, id, request):
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
        app.logger.debug("Hello from File.update()!")
        if not request.json:
            raise InvalidArgument("API Request has no JSON payload!")

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
        except Exception as e:
            raise InvalidArgument(
                "Argument parsing error",
                {'request.json' : request.json, 'exception' : str(e)}
            ) from None


        #
        # Generate SQL
        #
        try:
            # columns list, without primary key(s)
            cols = [ c for c in data.keys() if c not in self.primarykeys ]
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

        #
        # Execute Statement
        #
        try:
            app.logger.debug(f"SQL: {self.sql}")
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
                "INSERT failed!",
                {'sql': self.sql or '', 'exception': str(e)}
            ) from None
        finally:
            g.db.commit()
            self.cursor.close()

        # Return id
        return (200, {'data': {'id' : id}})




    @staticmethod
    def file_exists(file: str) -> bool:
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