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
#
#
#   TODO: remove _* -columns from result sets.
#
import time
import logging
import sqlite3

from flask              import g
from application        import app
from .                  import InvalidArgument, Timeout, NotFound
from .                  import DataObject

# Extends api.DataObject
class File(DataObject):

    class DotDict(dict):
        """dot.notation access to dictionary attributes"""
        __getattr__ = dict.get
        __setattr__ = dict.__setitem__
        __delattr__ = dict.__delitem__
        def __missing__(self, key):
            """Return None if non-existing key is accessed"""
            return None


    def __init__(self, request):
        """No need to parse - no request arguments supported"""
        self.cursor = g.db.cursor()
        # Init super for table name 'file'
        super().__init__(self.cursor, 'file')


    def search(self, type: str = None, include_restricted: bool = False):
        """Argument 'type' as per column file.type, 'restricted' as column file.restricted."""
        app.logger.debug(
            f"Query will {('not ', '')[int(include_restricted)]}include restricted {type} images"
        )
        self.sql = f"SELECT * FROM {self.table_name}"
        where = []
        if type is not None:
            where.append(f" type = '{type}' ")
        if not include_restricted:
            where.append(f" _restricted = 'no' ")
        if where:
            self.sql += " WHERE " + " and ".join(where)
        app.logger.debug("SQL: " + self.sql)
        try:
            self.cursor.execute(self.sql)
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
                        "variables" : None,
                        "fields"    : "ALL"
                    }
                }
            )
        else:
            return (200, {"data": data})


    def get(self, include=[]):
        """Retrieve and return 'file' table row. The table either has no rows (backend is not running) or there is only one row."""

        try:
            self.sql = "SELECT "
            self.sql += self.select_columns(
                include=self.args.fields or include,
                exclude=["id"],
                include_primarykeys = False
            )
            self.sql += " FROM psu"
            try:
                self.cursor.execute(self.sql)
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
                        "No data in table 'psu'!",
                        "Most likely cause is that the OBC emulator is not running."
                    )
            # Create data dictionary from result
            data = dict(zip([c[0] for c in self.cursor.description], result[0]))
        finally:
            self.cursor.close()

        fields = self.args.pop('fields', None)
        if app.config.get("DEBUG", False):
            return (
                200,
                {
                    "data"          : data,
                    "query" : {
                        "sql"       : self.sql,
                        "variables" : None,
                        "fields"    : fields or "ALL"
                    }
                }
            )
        else:
            return (200, {"data": data})



    def post(self, request):
        """Support three PSU commands; 'voltage', 'limit' and 'power'. Voltage and current limit commands need to define one float argument. Power command gives either 'ON' or 'OFF' string as an argument.
        Values are accepted with three decimal accuracy and decimals beyond those are simply truncated away.
        Middleware communicates to backend through the database's command table. This is asyncronous by definition and therefore this method shall poll the command table for an update that tells it if the command was successful or not. For obvious reasons, this activity has a timeout.
        Possible results:
        (406 Not Acceptable) raise InvalidArgument()
        (202 Accepted)
        {
            'command_id' : <int>
        }
        """
        try:
            if not request.json:
                raise InvalidArgument(
                    "API Request has no JSON payload!",
                    "This service requires 'function' and 'value' arguments."
                )
            # Extract parameters
            try:
                fnc     = request.json.get('function', None)
                val     = request.json.get('value',    None)
            except Exception as e:
                raise InvalidArgument(
                    "Argument parsing error",
                    {'request' : request.json, 'exception' : str(e)}
                )
            if not fnc or not val:
                raise InvalidArgument(
                    "Missing argument(s) 'function' and/or 'value'",
                    {'request' : request.json}
                )
            app.logger.debug("fnc='{}', val='{}'".format(fnc, val))

            #
            # Check parameters
            #
            if fnc in ("SET_VOLTAGE", "SET_CURRENT_LIMIT"):
                try:
                    val = float(val)
                except Exception as e:
                    raise InvalidArgument(
                        "Invalid 'value' argument!",
                        {'request' : request.json, 'exception' : str(e)}
                    )

            elif fnc == "SET_POWER":
                if val not in ("ON", "OFF"):
                    raise InvalidArgument(
                        "Invalid 'value', use 'ON' or 'OFF'!",
                        {'request' : request.json}
                    )

            else:
                raise InvalidArgument(
                    "Unrecognized 'function'!",
                    {'request' : request.json}
                )

            #
            # Execute function
            #
            sql = """
            INSERT INTO command
            (
                session_id,
                interface,
                command,
                value
            )
            VALUES
            (
                :session_id,
                'PSU',
                :command,
                :value
            )
            """
            try:
                cursor = g.db.cursor()
                # TODO: Solve testing session ID issue
                # Now just hardcoded for 1
                app.logger.critical("FIX SESSION ID ISSUE!!")
                bvars = {
                    'session_id'    : 1,
                    'command'       : fnc,
                    'value'         : str(val)
                }
                cursor.execute(sql, bvars)
                command_id = cursor.lastrowid
            except Exception as e:
                app.logger.exception(
                    "command -table INSERT failed! (sql='{}', bvars='{}')"
                    .format(sql, str(bvars))
                )
                raise
            app.logger.debug("command_id: '{}'".format(command_id))

            #
            # Command has been placed, poll for a result for timeout seconds
            #
            # NOTE: application.py makes sure these configuration values exist
            timeout  = app.config['COMMAND_TIMEOUT']
            interval = app.config['COMMAND_POLL_INTERVAL']

            result_sql = """
            SELECT  result
            FROM    command
            WHERE   id = {}
                    AND
                    result IS NOT NULL
            """.format(command_id)
            result = None
            end_time = time.time() + timeout
            while not result:
                result = cursor.execute(result_sql).fetchone()
                if time.time() > end_time:
                    break
            try:
                cursor.close()
            except:
                pass

            # Timeout?
            if not result:
                raise Timeout(
                    "PSU command timeout!",
                    {
                        'command.id' : command_id,
                        'sql' : sql,
                        'bvars' : bvars,
                        'request' : request.json,
                        'command_timeout' : timeout,
                        'command_poll_interval' : interval
                    }
                )
            # We have a result!
            return (200, {'result' : result})
        except Exception as e:
            app.logger.exception(
                "Error while processing PSU command!"
            )
            raise

# EOF