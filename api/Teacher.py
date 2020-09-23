#
#   Teacher - Object based on table 'teacher'
#
#   Teacher.py - Modifications by Jani Tammi <jasata@utu.fi>
#   0.1.0   2020-09-05  Initial version.
#
#   Retrieves table 'teacher' data, or raises and exception for not-found.
#   (2020-09-23 Used only by File.py:prepublish() ...)
#
#
#     .uid: str             UTU UID (primary key)
#     .created: int         Timestamp
#     .status: str          ['active' | 'inactive']
#     .active: bool         true for 'active', otherwise false
#
#   USAGE
#       teacher = Teacher('jasata')
#       if not teacher.active:
#           raise ValueError("Teacher not active")
#
import sqlite3

from flask          import g

class Teacher():

    def __init__(self, uid: str):
        if not uid:
            raise ValueError("Not a teacher!")
        self.__uid      = None
        self.__created  = None
        self.__status   = None
        self.cursor = g.db.cursor()
        self.sql = f"SELECT * FROM teacher WHERE uid = ?"
        self.cursor.execute(self.sql, [uid])
        rows = self.cursor.fetchall()
        if not rows:
            raise ValueError(f"Teach by UID '{uid}' not found!")
        if len(rows) != 1:
            raise ValueError("Query returned less or more than exactly one row!")
        # Extract values
        self.__uid      = rows[0][0]
        self.__created  = rows[0][1]
        self.__status   = rows[0][2]


    @property
    def uid(self) -> str:
        return self.__uid
    @uid.setter
    def uid(self, val: str):
        raise ValueError("Cannot change Primary Key!")


    @property
    def created(self) -> int:
        return self.__created
    @created.setter
    def created(self, value: int):
        raise ValueError("Changing created datatime is not allowed!")


    @property
    def status(self) -> str:
        return self.__status
    @status.setter
    def status(self, value: str):
        if value in ('active', 'inactive'):
            self.__update_status(value)
        else:
            raise ValueError("Acceptable status values are 'active' and 'inactive'!")


    @property
    def active(self) -> bool:
        return (self.__status == 'active')
    @active.setter
    def active(self, value: bool):
        self.__update_status(('inactive', 'active')[int(value)])


    def __update_status(self, value: str):
        self.sql = f"UPDATE teacher SET status = ? WHERE uid = ?"
        self.cursor.execute(self.sql, [value, uid])
        self.cursor.connection.commit()
        self.__status = value

# EOF