###############################################################################
#
# DataObject class (SQLite3 utilities)
#
#   2019-12-27  Add .enum: list into column object DotDict.
#               Extracted from SQL schema (CHECK col IN (...)).
#   2020-09-08  Added selectSQL(), insertSQL() and updateSQL() functions.
#
#
#   Every API class should derive itself from this class.
#
#   DataObject.__init__(cursor, table: str, exclude: list = [])
#       Initializes the DataObject for 'table' by reading in column metadata.
#       NOTE: You should not exclude primary keys. Intended for obsolete
#             columns that are not yet purged from the database.
#
#   DataObject().columns: list
#       All columns the 'table' that was given for the initialiaztion,
#       except the columns that were specified in 'exclude' list during
#       initialization.
#
#   DataObject().keys: list
#       List of primary key columns in the <table>.
#
#   DataObject().select_columns(exclude: list) -> str
#       Returns a string for SELECT clause where special formatting is
#       applied to datatypes that need it (namely, TIMESTAMP and DATETIME).
#       Optional exclude list may be supplied for columns that are not
#       needed among selected items.
#
#   DataObject().where_condition(column: str) -> str
#       Parse needed conversions and casts according to the datatype.
#
#   NOTE:
#   SQLite natively supports only the types TEXT, INTEGER, REAL, BLOB and NULL.
#
import re
import sqlite3

from flask          import g
from application    import app


class DataObject(list):

    # Default Dot Dict (DDD)
    class DDD(dict):
        """Dot-notation access dict with default key '*'. Returns value for key '*' for missing missing keys, or None if '*' value has not been set."""
        def __custom_get__(self, key):
            """For all DDD.key access, missing or otherwise."""
            return self.get(key, self.get('*', None))
        __getattr__ = __custom_get__
        __setattr__ = dict.__setitem__
        __delattr__ = dict.__delitem__
        def __missing__(self, key):
            """For DDD[key] access, missing keys."""
            return self.get('*', None)

    class DotDict(dict):
        """dot.notation access to dictionary attributes"""
        __getattr__ = dict.get
        __setattr__ = dict.__setitem__
        __delattr__ = dict.__delitem__
        def __missing__(self, key):
            """Return None if non-existing key is accessed"""
            return None
        def __str__(self):
            return self.getattr('name', '(null)')

    # Class variable
    table_name = ''

    def __init__(
        self,
        cursor: "sqlite3.cursor",
        table: str,
        exclude: list = []
    ):
        """Load self (=list) with DDD(dict)'s of non-excluded columns and their meta data."""
        self.table_name = table
        # pragma_table_info() columns:
        # cid           Column ID number
        # name          Column name
        # type          INTEGER | DATETIME | ...
        # notnull       1 = NOT NULL, 0 = NULL
        # dflt_value    Default value
        # pk            1 = PRIMARY KEY, 0 = not
        cursor.execute("SELECT * FROM pragma_table_info('{}')".format(table))
        for row in cursor:
            if row[1] not in exclude:
                self.append(
                    self.DDD(
                        name        = row[1],
                        datatype    = row[2],
                        nullable    = True if row[3] == 0 else False,
                        default     = row[4],
                        primarykey  = True if row[5] == 1 else False,
                        enum        = None
                    )
                )
        #
        # Collect CHECK (column IN (...)) lists as 'enum'
        #
        cursor.execute(
            "SELECT sql FROM sqlite_master "
            f"WHERE type = 'table' AND name = '{table}'"
        )
        schema = cursor.fetchone()[0]
        # Create generator object
        checks = (
            m.groups() for m in re.finditer(
                r"CHECK\s+\((\w+)\s+IN\s+\(\s*(.*?)\s*\)\s*\)",
                schema
            )
        )
        for column, checklist in checks:
            for colObj in self:
                if colObj.name == column:
                    colObj.enum = eval('[' + checklist + ']')



    @property
    def columns(self):
        """Returns a list of column names (list of strings)."""
        return [col.name for col in self]


    @property
    def primarykeys(self):
        """Returns a list of primary key columns."""
        return [col.name for col in self if col.primarykey]


    def missing_columns(self, columns: list) -> list:
        """Accepts a list of colunm names and returns a subset (list) of those that do not exist in the database table. NOTE: if specified column name in the argument is one of the excluded column names, it is included in the result list of 'missing' columns, although it is merely excluded."""
        if not columns:
            return []
        existing = self.columns
        missing = []
        for column in columns:
            if column not in existing:
                missing.append(column)
        return missing


    def get_column_objects(
        self,
        include = [],
        exclude = [],
        include_primarykeys = True
    ) -> list:
        """Get a list of DDD column objects.
        All arguments are optional.
        include - list of column names to include
        exclude - list of column names to exlude
        include_primarykeys - True | False if primary keys are to be included
        If optional 'include' list can be provided, the result list to specified. However, if 'include_primary_keys' is True, the parsed string will always contain also the primary key columns - even if they are not defined in the 'include' and excluded in the 'exclude' list.
        
        If a column is defined in both 'include' and 'exclude', exclude list will take precedence and column is not included. Only exception to this rule are primary key columns (when 'include_primarykeys' is True)."""
        # Purge primary keys from exclude list, if 'include_primarykeys'
        if exclude and include_primarykeys:
            exclude = [col for col in exclude if col not in self.primarykeys]
        # Compile list of column objects/dicts
        if not include:
            # empty 'include' equals ALL fields (except 'excluded')
            flist = [col for col in self if col.name not in exclude]
        else:
            flist = []
            for col in self:
                app.logger.debug(col.name)
                if col.primarykey and include_primarykeys:
                    # Forced inclusion for pk
                    flist.append(col)
                elif col.name in include and col.name not in exclude:
                    flist.append(col)
        return flist


    def get_column_names(
        self,
        include = [],
        exclude = [],
        include_primarykeys = True
    ):
        """See get_column_objects() for documentation. This function returns a list of names (strings)."""
        lst = self.get_column_objects(include, exclude, include_primarykeys)
        return [c.name for c in lst]


    def select_typecast(self, column: DDD) -> str:
        """Take column object argument and return string representation of the column name, with datatype specific typecasting, if necessary."""
        if column.datatype == 'TIMESTAMP':
            return "CAST(strftime('%s', {0}) as integer) AS {0}".format(column.name)
        elif column.datatype == 'DATETIME':
            return "datetime({0}) AS {0}".format(column.name)
        else:
            return column.name


    def select_columns(
        self,
        include = [],
        exclude = [],
        include_primarykeys = True
    ):
        """Provide datatype specific formatting for SQL queries. Optional 'include' list can be provided, limiting the parsing to specified. However, if 'include_primary_keys' is True, the parsed string will always contain also the primary key columns - even if they are not defined in the 'include' and excluded in the 'exclude' list.
        
        If a column is defined in both 'include' and 'exclude', exclude list will take precedence and column is not included. Only exception to this rule are primary key columns (when 'include_primarykeys' is True)."""
        # Purge primary keys from exclude list, if 'include_primarykeys'
        if exclude and include_primarykeys:
            exclude = [col for col in exclude if col not in self.primarykeys]
        # Compile list of column objects/dicts
        if not include:
            # empty 'include' equals ALL fields (except 'excluded')
            flist = [col for col in self if col.name not in exclude]
        else:
            flist = []
            for col in self:
                if col.primarykey and include_primarykeys:
                    flist.append(col)
                elif col.name in include and col.name not in exclude:
                    flist.append(col)

        slist = []
        # NOTE: Fractional timestamp (Warning - fractional inaccuracy!)
        # SELECT (julianday(timestamp) - 2440587.5) * 86400.0
        # 1541695244 (exact) becomes: 1541695244.00001
        for col in flist:
            if col.datatype == 'TIMESTAMP':
                slist.append(
                    "CAST(strftime('%s', {0}) as integer) AS {0}"
                    .format(col.name)
                )
            elif col.datatype == 'DATETIME':
                slist.append(
                    "datetime({0}) AS {0}"
                    .format(col.name)
                )
            else:
                slist.append(col.name)
        return ", ".join(slist)


    def where_condition(self, column: DDD) -> str:
        """Return formatting for condition column based on datatype."""
        col = None
        for c in self:
            if c.name == column:
                col = c
                break
        if not col:
            raise ValueError("Non-existent column specified")
        # return suitable conversion
        if col.datatype == 'TIMESTAMP':
            return "CAST(strftime('%s', {}) as integer)".format(col.name)
        elif col.datatype == 'DATETIME':
            return "datetime({})".format(col.name)
        else:
            return "{}".format(col.name)


    def schema(self, exclude: list = []) -> dict:
        """Data Schema dictionary. Caller needs to set 'readonly' values as necessary, before converting to JSON and sending the schema out."""
        #
        # NOTE: .default is set to None, because some defaults make no sense to
        #       the receiving JavaScript components (such as strftime() calls).
        #

        # Map SQLite3 datatypes to JavaScript types
        typeMap = self.DDD(
            {
                'TEXT':         'string',
                'INTEGER':      'integer',
                'REAL':         'number',
                'BLOB':         'string',
                'NUMERIC':      'number',
                'BOOLEAN':      'boolean',
                'DATETIME':     'string',
                '*':            'string'
            }
        )
        schema = {}
        for col in self:
            if col.name not in exclude:
                # Nothing is 'readonly' because such information is specific to
                # the implementation - caller should set the value as necessary,
                # before converting into JSON and sending to client.
                schema[col.name] = {
                    'type':     typeMap[col.datatype],
                    'required': not col.nullable,
                    'default':  None,
                    'enum':     col.enum,
                    'readonly': False
                }
                # If you don't want enum field when there is no enum...
                #if col.enum:
                #    schema[col.name]['enum'] = col.enum
        return schema



    def __str__(self):
        return "\n".join([str(c) for c in self])



    def insertSQL(self, data: dict) -> str:
        """Generate INSERT statement to match 'data' dictionary."""
        try:
            sql = f"INSERT INTO {self.table_name} "
            sql += f"({','.join(data.keys())}) "
            sql += f"VALUES (:{',:'.join(data.keys())})"
            #app.logger.debug("DataObject.insertSQL(): " + sql)
            return sql
        except Exception as e:
            app.logger.exception("DataObject.insertSQL(): Error parsing SQL")
            raise InternalError(
                "Error parsing SQL",
                {'sql': sql or '', 'exception' : str(e)}
            )



    def updateSQL(self, data: dict, pkeys: list, ro: list = []) -> str:
        """Generate UPDATE statement to match 'data' dictionary. For correct syntax, 'pkeys' list must be specified with all primary keys and optionally, 'ro' (read-only) list should contain column names that must not be updated."""
        try:
            # columns list, without primary key(s)
            cols = [ c for c in data.keys() if c not in pkeys ]
            # Remove read-only columns, in case someone injected them
            cols = [ c for c in cols if c not in ro ]
            app.logger.debug(f"DataObject.updateSQL(): Columns: {','.join(cols)}")
            sql = f"UPDATE {self.table_name} SET "
            sql += ",".join([ c + ' = :' + c for c in cols ])
            sql += " WHERE "
            sql += " AND ".join([k + ' = :' + k for k in pkeys])
            #app.logger.debug("DataObject.updateSQL(): " + sql)
            return sql
        except Exception as e:
            app.logger.exception("DataObject.updateSQL(): Error parsing SQL")
            raise InternalError(
                "SQL parsing error",
                {'sql' : sql or '', 'exception' : str(e)}
            ) from None



    def selectSQL(self, where: dict, columns: list = None) -> str:
        """TBA"""
        try:
            if not columns:
                cols = '*'
            elif isinstance(columns, list):
                cols = ", ".join(columns)
            else:
                cols = columns
            sql = f"SELECT {cols} FROM {self.table_name} WHERE "
            sql += " AND ".join([ f"{k} = :{k}" for k in where ])
            #app.logger.debug("DataObject.selectSQL(): " + sql)
            return sql
        except Exception as e:
            app.logger.exception("DataObject.selectSQL(): Error parsing SQL")
            raise InternalError(
                "Error parsing SQL",
                {'sql': sql or '', 'exception' : str(e)}
            )


# EOF
