# -*- coding: utf-8 -*-
#
# Turku University (2019) Department of Future Technologies
# Course Virtualization / Website
# Class for Course Virtualization site image/.OVA Publishing
#
# Publish.py - Jani Tammi <jasata@utu.fi>
#
#   0.1.0   2019.12.25  Initial version.
#
#
#
import os
import sqlite3

from flask          import g
from application    import app
from .Exception     import *
from .DataObject    import DataObject
from .OVFData       import OVFData



class Publish(DataObject):

    def __init__(self, request):
        self.cursor = g.db.cursor()
        super().__init__(self.cursor, 'file')


    def preprocess(self, filepath, owner) -> tuple:
        """Extract information from the file and prepopulate 'file' table row. Returns (200, "{ 'id': <file.id> }")"""
        self.file = filepath
        self.filedir, self.filename = os.path.split(self.file)
        _, self.filesuffix = os.path.splitext(self.filename)
        if not Publish.file_exists(self.file):
            raise NotFound(f"File '{self.file}' does not exist!")

        # Build a dictionary where keys match 'file' -table column names
        # Populate with values either from .OVA or other
        #
        if self.filesuffix == '.ova':
            attributes = Publish.__ova_attributes(self.file)
        else:
            attributes = Publish.__img_attributes(self.file)
        # Cannot be inserted without owner
        attributes['_owner'] = owner
        # File size in bytes
        attributes['size'] = os.stat(self.file).st_size

        #
        # Data collected, insert a row
        #
        try:
            self.sql =   f"INSERT INTO file ({','.join(attributes.keys())}) "
            self.sql +=  f"VALUES (:{',:'.join(attributes.keys())})"
            self.cursor.execute(self.sql, attributes)
            attributes['sql'] = self.sql # remove later
            # Get AUTOINCREMENT PK
            file_id = self.cursor.lastrowid
            attributes['id']  = self.cursor.lastrowid # remove later
            self.cursor.connection.commit()
        except sqlite3.IntegrityError as e:
            app.logger.exception("sqlite3.IntegrityError" + str(e))
            raise Conflict("SQLite3 integrity error", str(e)) from None
        except Exception as e:
            app.logger.exception("Unexpected error!")
            raise InternalError(
                "preprocess() error while inserting", str(e)
            ) from None


        #
        # Retrieve inserted row and send it to client
        #
        try:
            # Query All columns that do not begin with '_'
            self.sql = f"SELECT {','.join([c for c in self.columns if c[:1] !='_'])} FROM file WHERE id = :id"
            self.cursor.execute(self.sql, {'id': file_id})
            # Create { 'col_1': 'value', ... } result dictionary
            result = dict(
                zip(
                    [c[0] for c in self.cursor.description],
                    self.cursor.fetchone()
                )
            )
            if len(result) < 1:
                raise InternalError(
                    f"Row by ID '{file_id}' not found!",
                    "The row was just inserted, so this should be impossible."
                )
            #
            # Create JSONForm schema
            #
            # Map SQLite3 datatypes to JSONForm datatypes
            # (No, we support only SQLite3 native datatypes)
            typeMap = {
                'TEXT':     'string',
                'INTEGER':  'integer',
                'REAL':     'number'
            }
            readOnly = ['id', 'name', 'sha1']
            # ColumnObject [ .name .datatype .nullable .default .primarykey ]
            cols = self.get_column_objects()
            schema = {}
            for c in cols:
                # Skip columns with names starting with '_' character
                if c.name[:1] != '_':
                    schema[c.name] = {
                        'type':         typeMap[c.datatype],
                        'required':     not c.nullable,
                        'default':      result[c.name],
                        'readOnly':     c.name in readOnly
                    }
                    if c.enum:
                        schema[c.name]['enum'] = c.enum
            attributes['schema'] = schema
        except Exception as e:
            app.logger.exception("error creating JSON")
            raise InternalError(
                "preprocess() error while generating JSON content", str(e)
            ) from None
        return (200, attributes)


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



    @staticmethod
    def __sha1(file: str) -> str:
        """THIS IS HORRIBLE IDEA! Takes too much time. Better solution would be to have a cron.job that checks which files do not have SHA1, and launches a process for them separately (with very low priority)"""
        import hashlib

        # BUF_SIZE is totally arbitrary, change for your app!
        BUF_SIZE = 65536  # lets read stuff in 64kb chunks!
        sha1 = hashlib.sha1()

        with open(file, 'rb') as f:
            while True:
                data = f.read(BUF_SIZE)
                if not data:
                    break
                sha1.update(data)
        return sha1.hexdigest()



# EOF
