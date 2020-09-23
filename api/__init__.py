#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Turku University (2019) Department of Future Technologies
# Course Virtualization / Website
# API module init
#
# api/__init__.py - Jani Tammi <jasata@utu.fi>
#
#   2019-12-07  Initial version.
#   2020-01-01  Moved response handlers into response.py module
#   2020-09-23  Remove Publish class
#
#
#   DOCUMENTATION
#
#
#   DataObject -class (an extended list). Initialized with:
#       - sqlite3.cursor object (usually found as g.db.cursor()).
#       - table name (str) for the database table being sourced.
#       - list of column names (str) to be excluded (ignored).
#
#   To derive DataObject class:
#
#   class MyData(DataObject):
#       def __init__(self,
#           request: Flask.request,
#           table: str,
#           exclude_columns: list = []
#       ):
#           self.cursor = g.db.cursor()
#           super().__init__(self.cursor, 'my_table_name')
#           # TODO: process Flask.request.args however you need
#
#       # TODO: implement .get() .put() etc... Remember to return tuples!
#
#
#   The main purpose for excluding columns is to allow convenient
#   parsing of the results into a JSON.
#
#   DataObject provides some basic services for parsing the SQL, which can
#   become very useful if the derived class offers an option to define the
#   columns (this, JSON fields). An example:
#
#   def get(self, include = []) -> tuple:
#       sql = "SELECT "
#       sql += self.select_columns(
#           include = include,
#           include_primarykeys = False
#       )
#       sql += f"FROM {self.table_name}"
#       try:
#           self.cursor.execute(sql)
#       except sqlite3.Error as e:
#           app.logger.exception(
#               f"SQL query failed! ({sql})"
#           )
#           # Let the caller deal with the exception
#           raise
#       else:
#           ...
#       # ALWAYS return tuple (return_code, {"data": data})!!!
#       return (200, {"data": data})
#
#   NOTE: You can add other root-level keys. api.response() does!
#
#
#
#   Derived Objects may implement following public JSON CRUD functions:
#
#   Create [POST]   .post() -> (code:int, payload:dict):tuple
#           Example: (200, {'data' : {...}}) Returns created record
#
#   Fetch [GET]     .get() -> (code:int, payload:dict):tuple
#           Example: (200, {'data' : {...}} Returns specified record
#
#   Search [GET]    .search() -> (code:int, payload:[dict]):tuple
#           Example: (200, {'data' : [{...}, ...]} Returns list of records
#
#   Update [PUT|PATCH] .patch() -> (code:int, payload:dict):tuple
#           Returns updated record
#
#   Delete [DELETE] .delete() -> (code:int, None):tuple
#           Does NOT return a record!
#
#   ---------------------------------------------------------------------------
#   AGAIN - ALL FUNCTIONS MUST RETURN A TUPLE!
#   ---------------------------------------------------------------------------
#
#       DataObjects may also implement a CSV extraction method by means of
#       .query() -> SQLite.Cursor method and
#       api.stream_result_as_csv(result:SQLite.Cursor)
#       Implementation belongs into the 'route.py':
#
#       @app.route('/csv/classifieddata', methods=['GET'])
#       def csv_classifieddata():
#           log_request(request)
#           try:
#               from api.ClassifiedData import ClassifiedData
#               return api.stream_result_as_csv(ClassifiedData(request).query())
#           except Exception as e:
#               app.logger.exception(
#                   "CSV generation failure! " + str(e)
#               )
#               raise
#
#

from .File          import File
from .Upload        import Upload
from .Flow          import Flow
from .Teacher       import Teacher
from .Exception     import *
from .response      import response, exception_response, stream_result_as_csv

# EOF
