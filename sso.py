#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Turku University (2019) Department of Future Technologies
# Course Virtualization / Website
# Single Sign-On module
#
# sso.py - Jani Tammi <jasata@utu.fi>
#
#   0.1.0   2019-12-22  Initial version.
#   0.2.0   2019-12-22  .authenticated and .validate().
#   0.3.0   2020-01-01  Only "enabled" teachers get teacher role.
#   0.4.0   2020-01-01  Chanced to 'active' / 'inactive' status values.
#
#
# ============================================================================
#   USING THIS MODULE
#
#
#   Has to be created during application creation and
#   needs to be updated in @app.before_request handler.
#
#   sso = SSO(
#       app.config.get('SSO_COOKIE'),
#       app.config.get('SSO_SESSION_API')
#   )
#
#   @app.before_request
#   def before_request():
#       ...
#       sso.update(request, session)
#
#
#
#   For light checking, property sso.authenticated:
#   if sso.authenticated:
#       ...
#
#
#   For important stuff, function sso.validate():
#   if sso.validate():
#       ...
#
# =============================================================================
#   END POINTS SUPPORTING THIS MODULE
#
#
# Three API endpoints are needed by the client side 'sso.js' code.
#
#
# [GET] /sso/login?destination=...
#           Calls ´sso.login(force = true)' to reload SSO session from
#           the SSO_SESSION_API. This endpoint will then redirect the
#           browser to (query parameter) 'destination' or index.html,
#           if the destination is not defined.
#
# [GET] /sso/logout
#           Calls `sso.logout()` and returns response 200 OK.
#           Client is responsible for removing privileged data from the page.
#
import sys
import json
import hashlib
import requests
import sqlite3

from flask import g


class SSO:

    def __init__(
        self,
        sso_hash_cookie,
        sso_session_api
    ):
        """Created ONCE as the Flask application initializes."""
        self.sso_cookie     = sso_hash_cookie
        self.session_api    = sso_session_api
        self.request        = None      # set in .before_request()
        self.session        = None      # set in .before_request()



    def before_request(self, request, session):
        """Call this on @app.before_request to update with current state. Quarantees that session['UID'] will always exist, containing either None or the SSO UID."""
        self.request = request
        self.session = session
        # Only on KeyError (entire variable does not exist) do login
        # THis constitutes as the "arrival" to the site or expired session
        try:
            _ = session['UID']
        except KeyError:
            self.login()



    def login(self, force: bool = False):
        """Query SSO REST API and set UID and ROLE in session accordingly. If 'force = True' is defined, pre-existing UID/ROLE are discarded."""
        if force:
            # Remove UID so that it is re-queried
            self.session.pop('UID', None)
        if not self.session.get('UID'):
            # Remove session.role so that it gets re-queried
            self.session.pop('ROLE', None)
            # Setting None will quarantee that UID will exist, even if
            # the get_hashed_uid() raises an exception
            self.session['UID'] = None
            # Let exceptions from below to propagate up
            self.session['UID'] = self.__get_uid()
            # session cookie is hashed already!
            #session['UID'] = self.__get_hashed_uid(request)
        # Query DB to determine teacher/student role
        if self.session['UID'] is not None and not self.session.get('ROLE'):
            sql = f"SELECT * FROM teacher WHERE uid = '{self.session['UID']}' "
            sql += "AND status = 'active'"
            try:
                cursor = g.db.cursor()
                cursor.execute(sql)
                result = cursor.fetchone()
            except sqlite3.Error as e:
                raise ValueError(
                    f"SSO role query failed! ({sql})\n" + str(e)
                ) from None
            else:
                if result is None:
                    self.session['ROLE'] = 'student'
                else:
                    self.session['ROLE'] = 'teacher'
            finally:
                cursor.close()
        elif not self.session.get('ROLE'):
            # session UID is None - set role to 'anonymous'
            self.session['ROLE'] = 'anonymous'
        # else: both exist, don't touch



    def logout(self):
        """Simply remove UID and ROLE from the session."""
        # MUST NOT .pop() the values out of existence
        # This will make .update() re-querty and this relogin
        #self.session.pop("UID", None)
        #self.session.pop("ROLE", None)
        self.session['UID']  = None
        self.session['ROLE'] = 'anonymous'



    #
    # Use this where it is IMPORTANT to make sure that the user actually has
    # authenticated SSO session - like before allowing a download of restricted
    # file to commence.
    #
    def validate(self) -> bool:
        """NOTE: .update() MUST be called in @app.before_request for this to work. Use this to check the validity session['UID']. SSO API endpoint will be queried again and session UID hash and the hash acquired by querying the SSO API are compared for validity. Return True if UID hash values match."""
        if not self.session.get('UID'):
            # If session UID is None
            return False
        try:
            if self.__get_uid() != self.session.get('UID'):
                return False
        except:
            return False
        return True



    #
    # SSO AUTHENTICATION STATUS PROPERTIES
    #
    #   Use these property-functions to check SSO session state.
    #
    #       PROPERTY            ANONYMOUS   STUDENT     TEACHER
    #       .is_authenticated   False       True        True
    #       .is_anonymous       True        False       False
    #       .is_student         False       True        False
    #       .is_teacher         False       False       True
    #
    @property
    def is_authenticated(self) -> bool:
        if self.session.get('UID', None):
            return True
        return False


    @property
    def is_anonymous(self) -> bool:
        if 'anonymous' == self.session.get('ROLE', None):
            return True
        return False


    @property
    def is_student(self) -> bool:
        if 'student' == self.session.get('ROLE', None):
            return True
        return False


    @property
    def is_teacher(self) -> bool:
        if 'teacher' == self.session.get('ROLE', None):
            return True
        return False


    """ To be removed
    # Use this for trivial session check (does session['UID'] exist?)
    # - usable for retrieving lists and other data that is not restricted,
    #   but rather only filtered based on authorized session, to provide
    #   better UI experience.
    # If someone forges the session cookie in the browser, this will merely
    # let him or her to see items that cannot be accessed. There is no need
    # to ensure proper UI experience for persons tampering with session data.
    #
    @property
    def authenticated(self) -> bool:
        if self.session.get('UID'):
            return True
        return False
    """


    @property
    def uid(self) -> str:
        return self.session.get("UID")


    @property
    def role(self) -> str:
        """Returns the role associated with the uid of this SSO session."""
        if self.session.get("UID") and self.session.get("ROLE"):
            return self.session['ROLE']
        else:
            return "anonymous"


    @property
    def roleJSON(self) -> str:
        """Returns a JSON containing the SSO role."""
        if self.session.get("UID") and self.session.get("ROLE"):
            return """{{ "role": "{}" }}""".format(self.session['ROLE'])
        else:
            return """{ "role": "anonymous" }"""





    def __get_uid(self) -> str:
        sso_hash = self.request.cookies.get(self.sso_cookie)
        if not sso_hash:
            return None
        try:
            response = requests.post(
                self.session_api + sso_hash,
                params = {
                    '_action':           'validate'
                },
                headers = {
                    'Content-Type':     'application/json'
                },
                timeout = 3
            )
        except Exception as e:
            raise ValueError(
                "request.post() failure!\n" + 
                f"URI: {self.session_api + sso_hash}\n" +
                str(e)
            ) from None
        if response.status_code == 200:
            # Retrieve JSON body
            try:
                # Raises ValueError if no JSON in body
                data = response.json()
            except Exception as e:
                raise ValueError(
                    "There is no JSON in the response body?" + str(e)
                ) from None
            # Read JSON key-value
            try:
                if data['valid']:
                    return data['uid']
                else:
                    return None
            except:
                return None
        else:
            raise ValueError(
                "Single Sign-On session validation query failure!\n" +
                f"Response code: {response.status_code}\n" +
                f"Response text: '{response.text}'"
            )


    def __repr__(self) -> str:
        return f"{self.__class__}({self.__dict__})"



# EOF