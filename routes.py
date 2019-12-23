#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Turku University (2019) Department of Future Technologies
# Course Virtualization / Website
# Flask Application routes
#
# application.py - Jani Tammi <jasata@utu.fi>
#
#   0.1.0   2019.12.07  Initial version.
#
#   This Python module only defines the routes, which the application.py
#   includes directly into itself.
#   Any actual work is implemented in the api module.
#
import sys
import time
import json
import flask
import logging

from flask          import request
from flask          import Response
from flask          import send_from_directory
from flask          import g
from flask          import session

from application    import app, sso

# ApiException classes, data classes
import api


#
# Debug log-function
#       Store HTTP request path and the rule that triggered.
#
def log_request(request):
    app.logger.debug(
        f"Debug={str(app.debug)}, Auth={str(sso.authenticated)} :: {request.method} '{request.path}' (rule: '{request.url_rule.rule}')"
    )


###############################################################################
#
# REST API ENDPOINTS (routes)
#
###############################################################################


#
# List of VM Image Downloadables
#
@app.route('/api/vm', methods=['GET'])
def vm_file():
    """List of Virtual Machine -type downloadables (column "type" = "vm").
    
    GET /api/vm
    Query parameters:
    (none implemented)
    API returns 200 OK and:
    {
        ...,
        "data" : [
            {
                TBA
            },
            ...
        ],
        ...
    }
    """
    log_request(request)
    try:
        from api.File import File
        return api.response(File(request).search("vm", sso.authenticated))
    except Exception as e:
        return api.exception_response(e)


#
# List of USB Image Downloadables
#
@app.route('/api/usb', methods=['GET'])
def usb_file():
    """List of USB disk -type downloadables (column "type" = "usb").
    
    GET /api/usb
    Query parameters:
    (none implemented)
    API returns 200 OK and:
    {
        ...,
        "data" : [
            {
                TBA
            },
            ...
        ],
        ...
    }
    """
    log_request(request)
    try:
        from api.File import File
        return api.response(File(request).search("usb", sso.authenticated))
    except Exception as e:
        return api.exception_response(e)


#
# API endpoints for Single Sign-On implementation
#
@app.route('/sso/state', methods=['GET'])
def sso_state():
    """Returns a sigle iten JSON: { "role": "[anonymous|student|teacher]" }. This also implicitly indicates the authentication state (anonymous = not authenticated)."""
    app.logger.debug(
        f"STATE: session.UID = {session.get('UID', '(does not exist)')}, session.ROLE = {session.get('ROLE', 'does not exist')}'"
    )
    return sso.roleJSON, 200

@app.route('/sso/login', methods=['GET'])
def sso_login():
    """This is the landing URI from SSO login page. SSO REST API is re-queried and session is updated accordingly. Finally, 'destination' URL parameter is used to redirect the broser to the final location - persumably the page from where the "login" link/button was pressed."""
    sso.login(force = True)
    destination = request.args.get(
        'destination',
        default = '/index.html',
        type = str
    )
    return flask.redirect(destination, code = 302)

@app.route('/sso/logout', methods=['GET'])
def sso_logout():
    """This endpoint sets UID to None and ROLE to 'anonymous' in the session, thus effectively logging the user out."""
    app.logger.debug(
        f"BEFORE sso.logout(): session.UID = {session.get('UID', '(does not exist)')}, session.ROLE = {session.get('ROLE', 'does not exist')}'"
    )
    sso.logout()
    app.logger.debug(
        f"AFTER sso.logout(): session.UID = {session.get('UID', '(does not exist)')}, session.ROLE = {session.get('ROLE', 'does not exist')}'"
    )
    return "OK", 200




# This will be the session re-validate handler
#
#   session.UID exists is "light" test
#               Sufficient to dish out lists of images, for example
#   sso.validate() will re-query sso.utu.fi 
#
@app.route('/api/login', methods=['GET', 'POST'])
def api_login():
    # Session authentication
    if sso.authenticated:
        app.logger.debug("I am authenticated")
    else:
        app.logger.debug("I am not authenticated")
    # Expired session can be detected by trying to access a variable in it.
    if not session.get('N'):
        app.logger.debug("Session expired, OpenAM check!")
        session['N'] = 1
    else:
        session['N'] += 1
    ssoUTUauth = request.cookies.get("ssoUTUauth")
    return f"{session['N']} - {session['UID']}", 200



###############################################################################
#
# System / development URIs
#
#       These routes are to be grouped under '/sys' path, with the notable
#       exception of '/api.html', because that serves the API listing as HTML
#       and because the API documentation is very central to this particular
#       solution.
#
#

#
# Flask Application Configuration
#
@app.route('/sys/cfg', methods=['GET'])
def show_flask_config():
    """Middleware (Flask application) configuration. Sensitive entries are
    censored."""
    if not sso.authenticated or not app.debug:
        return api.response((404, {'error': 'Permission Denied'}))
    log_request(request)
    try:
        cfg = {}
        for key in app.config:
            cfg[key] = app.config[key]
        # Censor sensitive values
        for key in cfg:
            if key in ('SECRET_KEY', 'MYSQL_DATABASE_PASSWORD'):
                cfg[key] = '<CENSORED>'
        return api.response((200, cfg))
    except Exception as e:
        return api.exception_response(e)



#
# API listing
#
#       Serves two routes: '/sys/api' and 'api.html'. First returns the listing
#       in JSON format and the second serves a HTML table of the same data.
#
#   NOTES:
#           - Built-in route '/static' is ignored.
#           - Implicit methods 'HEAD' and 'OPTIONS' are hidden.
#             That's not the correct way about doing this, but since this implementation
#             does not use either of them, we can skip this issue and just hide them.
#
#   See also:
#   https://stackoverflow.com/questions/13317536/get-a-list-of-all-routes-defined-in-the-app
#
@app.route('/api.html', methods=['GET'])
@app.route('/sys/api', methods=['GET'])
def api_doc():
    """JSON API Documentation.
    Generates API document from the available endpoints. This functionality
    replies on PEP 257 (https://www.python.org/dev/peps/pep-0257/) convention
    for docstrings and Flask micro framework route ('rule') mapping to
    generate basic information listing on all the available REST API functions.
    This call takes no arguments.
    
    GET /sys/api
    
    List of API endpoints is returned in JSON.
    
    GET /api.html
    
    The README.md from /api is prefixed to HTML content. List of API endpoints
    is included as a table."""
    def htmldoc(docstring):
        """Some HTML formatting for docstrings."""
        result = None
        if docstring:
            docstring = docstring.replace('<', '&lt;').replace('>', '&gt;')
            result = "<br/>".join(docstring.split('\n')) + "<br/>"
        return result
    try:
        log_request(request)
        eplist = []
        for rule in app.url_map.iter_rules():
            if rule.endpoint != 'static':
                allowed = [method for method in rule.methods if method not in ('HEAD', 'OPTIONS')]
                methods = ','.join(allowed)

                eplist.append({
                    'service'   : rule.endpoint,
                    'methods'   : methods,
                    'endpoint'  : str(rule),
                    'doc'       : app.view_functions[rule.endpoint].__doc__
                })


        #
        # Sort eplist based on 'endpoint'
        #
        eplist = sorted(eplist, key=lambda k: k['endpoint'])


        if 'api.html' in request.url_rule.rule:
            try:
                from ext.markdown2 import markdown
                with open('api/README.md') as f:
                    readme = markdown(f.read())
            except:
                app.logger.exception("Unable to process 'api/README.md'")
                readme = ''
            html =  "<!DOCTYPE html><html><head><title>API Listing</title>"
            html += "<link rel='stylesheet' href='/css/api.css'></head><body>"
            html += readme
            html += "<table><tr><th>Service</th><th>Methods</th><th>Endpoint</th><th>Documentation</th></tr>"
            for row in eplist:
                html += "<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>" \
                        .format(
                            row['service'],
                            row['methods'],
                            row['endpoint'].replace('<', '&lt;').replace('>', '&gt;'),
                            htmldoc(row['doc'])
                        )
            html += "</table></body></html>"
            # Create Request object
            response = app.response_class(
                response    = html,
                status      = 200,
                mimetype    = 'text/html'
            )
            return response
        else:
            return api.response((200, {'endpoints': eplist}))
    except Exception as e:
        return api.exception_response(e)




###############################################################################
#
# Catch-all for non-existent API requests
#
@app.route('/api', methods=['GET', 'POST', 'PATCH', 'PUT', 'DELETE'])
@app.route('/api/', methods=['GET', 'POST', 'PATCH', 'PUT', 'DELETE'])
@app.route('/api/<path:path>', methods=['GET', 'POST', 'PATCH', 'PUT', 'DELETE'])
def api_not_implemented(path = ''):
    """Catch-all route for '/api*' access attempts that do not match any defined routes.
    "405 Method Not Allowed" JSON reply is returned."""
    log_request(request)
    try:
        raise api.MethodNotAllowed(
            "Requested API endpoint ('{}') does not exist!"
            .format("/api/" + path)
        )
    except Exception as e:
        return api.exception_response(e)




###############################################################################
#
# Static content
#
#   NOTE:   Nginx can be configured (see /etc/nginx/nginx.conf) to serve
#           files of certain suffixes (images, css, js) which are deemed to
#           be always static.
#
#           Nginx file suffix configuration would be a never ending chase after
#           new files suffixes. It's not worth it in this application -
#           performance is not a vital concern.
#
#   This is an alternative (albeit little less efficient) approach:
#
#           Certain routes are setup to contain only static files and
#           'send_from_directory()' is used to simply hand out the content.
#           The function is designed to solve a security problems where
#           an attacker would try to use this to dig up .py files.
#           It will raise an error if the path leads to outside of a
#           particular directory.
#

#
# Catch-all for other paths (UI HTML files)
#
@app.route('/<path:path>', methods=['GET'])
# No-path case
@app.route('/', methods=['GET'])
def send_ui(path = 'index.html'):
    """Send static HTML/CSS/JS/images/... content."""
    log_request(request)
    return send_from_directory('html', path)



# EOF