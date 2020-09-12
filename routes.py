#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Turku University (2019) Department of Future Technologies
# Course Virtualization / Website
# Flask Application routes
#
# routes.py - Jani Tammi <jasata@utu.fi>
#
#   2019-12-07  Initial version
#   2019-12-23  Add /sso endpoints
#   2019-12-25  Add /api/publish endpoint
#   2020-09-07  Add /api/file/upload
#   2020-09-09  Add /api/file/flow  (Flow.js GET, POST upload endpoint)
#   2020-09-12  Add /sse/flow-upload-status
#
#
#   This Python module only defines the routes, which the application.py
#   includes directly into itself.
#   Most of actual work is implemented in the API modules.
#
import os
import sys
import time
import json
import flask
import logging

# These are the only four items so common that they can be referred without
# the 'flask.' prefix, and reader still knows what they are.
from flask          import request
from flask          import Response
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
        f"Debug={str(app.debug)}, Auth={str(sso.is_authenticated)} :: {request.method} '{request.path}' (rule: '{request.url_rule.rule}')"
    )


###############################################################################
#
# REST API ENDPOINTS (routes)
#
###############################################################################


#
# NOTE: All access to these endpoints (made by JQuery) will have a underscore
#       ('_') query parameter. This is an anti-cache strategy by the JQuery
#       and should be ignored.
#
@app.route(
    '/api/file',
    methods=['GET'],
    strict_slashes = False
)
@app.route(
    '/api/file/<any("vm","usb"):ftype>',
    methods=['GET'],
    strict_slashes = False
)
def api_file(ftype = None):
    """List of downloadable file, with optional type filtering. Allowed types are "vm" and "usb".
    
    GET /api/file
    GET /api/file/usb
    GET /api/file/vm
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
        if ftype not in (None, "usb", "vm"):
            raise api.InvalidArgument(f"Invalid type '{ftype}'!")
        from api.File import File
        return api.response(
            File().search(
                file_type = ftype,
                downloadable_to = sso.role
            )
        )
    except Exception as e:
        return api.exception_response(e)



#
#   /api/file/<int:id>/schema
#
#   JSONForm schema for specified 'file.id' database record.
#
#
@app.route('/api/file/schema', methods=['GET'], strict_slashes = False)
def api_file_schema():
    """Create data schema JSON for client FORM creation."""
    log_request(request)
    try:
        return api.response(api.File().schema())
    except Exception as e:
        return api.exception_response(e)




@app.route(
    '/api/file/<int:id>',
    methods = ['GET','PUT'],
    strict_slashes = False
)
def api_file_id(id):
    """Database table row endpoint. Retrieve (GET) or update (PUT) record."""
    log_request(request)
    try:
        if request.method == 'PUT':
            return api.response(api.File().update(id, request, sso.uid))
        elif request.method == 'GET':
            return api.response(api.File().fetch(id))
        else:
            raise api.MethodNotAllowed(
                f"Method {request.method} not supported for this endpoint."
            )
    except Exception as e:
        return api.exception_response(e)



#
#   /api/file/owned
#
#   Return a listing of files owned by current session holder.
#
@app.route('/api/file/owned', methods=['GET'], strict_slashes = False)
def api_file_owned():
    """Return JSON listing of files owned by currently authenticated person. Slightly 'special' endpoint that accepts only GET method and no parameters of any kind. Data is returned based on the SSO session role. Specially created for Upload and Manage UI, to list user's files."""
    log_request(request)
    try:
        return api.response(api.File().search(owner = sso.uid or ''))
    except Exception as e:
        return api.exception_response(e)


#
# NOTE: This rule CANNOT be the same as the internal location
#       in the Nginx configuration file, or Nginx will not hand
#       the request over to Flask at all.
#
@app.route(
    '/download/<path:path>',
    methods = ['GET'],
    strict_slashes = False
)
def download(path = None):
    if not path:
        return "Not Found", 404
    try:
        return api.File().download(path, sso.role)
    except Exception as e:
        app.logger.exception(str(e))
        return "Internal Server Error", 500


###############################################################################
#
# Flow.js - post processing API endpoint
#

###############################################################################
# ONLY to demonstrate how SSE works
# Response terminates (return) after 4 messages.
# The Javascript EventSource will reconnect again in 3-5 seconds.
# CORRECT way is to send an event, like "event: END\ndata: blah blah"
# and create an .onEND() handler which closes the stream from client end.
#
@app.route(
    '/sse/demo',
    methods=['GET'],
    strict_slashes = False
)
def dummy_sse(filename: str):
    def generator():
        val = 0
        while True:
            val += 1
            msg = f"Message #{val:03d}"
            if not val % 5:
                return "event: message\ndata: END\n\n"
            yield f"event: message\ndata: {msg}\n\n"
            #Update frequency
            time.sleep(0.5)

    log_request(request)
    return flask.Response(
        generator(),
        mimetype = "text/event-stream"
    )
# END OF DEMONSTRATION CODE ###################################################


# SSE - Events for background processing of Flow.js uploads
#
#   NONE OF THIS WORKS, unless buffering is disabled!
#   REQUIRED: Nginx site configuration parameter (uwsgi_buffering off):
#
#   location / {
#       include uwsgi_params;
#       client_max_body_size 50M;
#       uwsgi_pass unix:/run/uwsgi/app/vm.utu.fi/vm.utu.fi.socket;
#       uwsgi_buffering off; <-- IMPORTANT!!!
#   }
#
@app.route(
    '/sse/flow-upload-status',
    methods=['GET'],
    strict_slashes = False
    )
def flow_process_status() -> tuple:
    """SSE endpoint to supply data to event listener. Required URL parameters: 'filename' and 'flowid'.
RETURN CODES
200 OK              no name conflict (GET) / successful assembly (POST)
400 BadRequest      Malformed requests (no 'filename' and/or 'flowid').
401 Unauthorized    Not an active teacher
"""
    log_request(request)
    #if not sso.is_teacher:
    #    return "Active teacher privileges required", 401
    # Should raise an exception if not defined in URL parameters
    try:
        filename = request.args.get('filename', type = str)
        flowid   = request.args.get('flowid',   type = str)
    except:
        return "Both 'filename' and 'flowid' must be defined in URL parameters", 400

    try:
        app.logger.info("Prerequisites OK... opening event stream")
        # from werkzeug.datastructures import Headers
        # headers = Headers()
        # headers.add('Cache-Control', 'no-cache, no-store, must-revalidate')
        # headers.add('Pragma', 'no-cache')
        # headers.add('Expires', '0')
        # headers.add('X-Accel-Buffering', 'no')
        return flask.Response(
            api.Flow.sse_upload_status(filename, flowid),
            #headers  = headers,
            mimetype = "text/event-stream"
        )

    except Exception as e:
        app.logger.exception("Unable to generate SSE!")
        return str(e), 400


#
# Flow.js API endpoint (/api/file/flow)
#
#   HTTP Codes (inFlow.js opts)
#       successStatuses     Chunk completed OK (Default: [200, 201, 202])
#       permanentErrors     Cancel upload (Default: [404, 415, 500, 501])
#       (anything else)     Try again
#
@app.route(
    '/api/file/flow',
    methods=['GET', 'POST'],
    strict_slashes = False
)
def flow_chunk_upload():
    """Return 200 if given chunk already exists, return 204 if not."""
    log_request(request)
    if not sso.is_teacher:
        raise api.Unauthorized("Active teacher privileges required")

    flow = api.Flow(request)
    # Check for filename conflict
    if api.Flow.exists(
        os.path.join(
            api.Flow.download_dir(),
            request.form.get('flowFilename') or
            request.args.get('flowFilename')
        )
    ):
        # 409 Conflict
        return "File by specified name already exists!", 409

    if request.method == "GET":
        # GET merely checks if the chunk already exists
        if flow.chunk_exists:
            return "", 200  # OK
        return "", 204      # No Content
    else:
        if not flow.valid_chunk:
            return "", 400
        flow.save_chunk()

    if flow.file_complete:
        # All chunks uploaded, create '.job' file for cron job
        # Set owner as current user (which is an active teacher)
        flow.createJob(sso.uid)

    return "", 200



###############################################################################
#
# SSO API endpoints for Single Sign-On implementation
#
@app.route('/api/sso', methods=['GET'], strict_slashes = False)
def sso_state():
    """Returns a sigle iten JSON: { "role": "[anonymous|student|teacher]" }. This also implicitly indicates the authentication state (anonymous = not authenticated)."""
    app.logger.debug(
        f"SSO STATE QUERY: session.UID = {session.get('UID', '(does not exist)')}, session.ROLE = {session.get('ROLE', 'does not exist')}' sso.roleJSON = {sso.roleJSON}"
    )
    return sso.roleJSON, 200

@app.route('/api/sso/login', methods=['GET'], strict_slashes = False)
def sso_login():
    """This is the landing URI from SSO login page. SSO REST API is re-queried and session is updated accordingly. Finally, 'destination' URL parameter is used to redirect the broser to the final location - persumably the page from where the "login" link/button was pressed."""
    sso.login(force = True)
    destination = request.args.get(
        'destination',
        default = '/index.html',
        type = str
    )
    return flask.redirect(destination, code = 302)

@app.route('/api/sso/logout', methods=['GET'], strict_slashes = False)
def sso_logout():
    """This endpoint sets UID to None and ROLE to 'anonymous' in the session, thus effectively logging the user out."""
    app.logger.debug(
        f"BEFORE sso.logout(): session.UID = {session.get('UID', '(does not exist)')}, session.ROLE = {session.get('ROLE', 'does not exist')}"
    )
    sso.logout()
    app.logger.debug(
        f"AFTER sso.logout(): session.UID = {session.get('UID', '(does not exist)')}, session.ROLE = {session.get('ROLE', 'does not exist')}"
    )
    return "OK", 200


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
# /sys
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
    # Allow output only when debugging AND when the user is authenticated
    if not sso.is_authenticated or not app.debug:
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
#             That's not the correct way about doing this, but since this
#             implementation does not use either of them, we can skip this
#             issue and just hide them.
#
#   See also:
#   https://stackoverflow.com/questions/13317536/get-a-list-of-all-routes-defined-in-the-app
#
@app.route('/api.html', methods=['GET'])
@app.route('/sys/api', methods=['GET'])
def api_doc():
    """JSON API Documentation.
    Generates API document from the available endpoints. This functionality
    relies on PEP 257 (https://www.python.org/dev/peps/pep-0257/) convention
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
                    readme = markdown(f.read(), extras=["tables"])
            except:
                app.logger.exception("Unable to process 'api/README.md'")
                readme = ''
            html =  "<!DOCTYPE html><html><head><title>API Listing</title>"
            html += "<link rel='stylesheet' href='/css/api.css'>"
            # substitute for favicon
            html += "<link rel='icon' href='data:;base64,iVBORw0KGgo='>"
            html += "</head><body>"
            html += readme
            html += "<h2>List of Flask routes and Endpoints</h2>"
            html += "<table class='endpointTable'><tr><th>Service</th><th>Methods</th><th>Endpoint</th><th>Documentation</th></tr>"
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






#
# Very bad file upload implementation - simply for getting the site published
# on time on January 2020. HTML5 File API based, chunk'ed and checksum'ed
# solution will be completed later.
#

@app.route('/upload/', methods=['POST'])
def upload_file():
    def allowed_file(fname):
        return '.' in fname and \
            fname.rsplit('.', 1)[1].lower() in app.config['UPLOAD_ALLOWED_EXT']
    # Log request
    log_request(request)
    # Is there a 'file' part in this Request
    if 'file' not in request.files:
        app.logger.error('No file part')
        return "Request has no file part", 406
    file = request.files['file']
    if not file:
        app.logger.error("file part is empty")
        return "File part is empty!", 406
    # if user did not not select a file, the browser can
    # submit an empty part without filename
    if file.filename == '':
        app.logger.error(f"file.filename: '{file.filename or 'None'}'")
        return "File has no name!", 406 # flask.redirect(request.url)
    # And is it allowed file (based on file suffix)?
    if not allowed_file(file.filename):
        app.logger.error('File not of allowed type!')
        return "File type not in the allowed list! ({})".format(
            app.config['UPLOAD_ALLOWED_EXT'].join(', ')
        ), 406 # 406 = "Not acceptable"
    #
    # Everything is fine! Process file
    #
    # Save to upload folder
    from werkzeug.utils import secure_filename
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    app.logger.debug(f"File saved to '{os.path.join(app.config['UPLOAD_FOLDER'], filename)}'")

    # Generate 'file' table row
    from api.File import File
    try:
        app.logger.debug(f"Prepublish '{filepath}'")
        return api.response(File().prepublish(filepath, sso.uid))
    except Exception as e:
        app.logger.error("Publishing error: " + str(e))
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
    """Send static content (HTML/CSS/JS/images/...)."""
    log_request(request)
    return flask.send_from_directory('html', path)



# EOF