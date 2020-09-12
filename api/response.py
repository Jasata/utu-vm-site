# -*- coding: utf-8 -*-
#
# Turku University (2019) Department of Future Technologies
# Course Virtualization / Website
# API response handlers
#
# api/response.py - Jani Tammi <jasata@utu.fi>
#
#   2020-01-01  Initial version.
#   2020-09-11  Add mimetype call parameter to response() and __make_response()
#
#
import time
import json

from flask          import request
from flask          import g
from application    import app

from .Exception     import *


#
# __make_response(code, payload)
#
# API internal / Generate Flask.Response from HTTP response code and data
# dictionary.
#
# Argument
#   code: int           HTTP code
#   payload: dict       Goes to json.dumps()
#   mimetype: str       Header mimetype
#
# Returns
#   Flask.Response      Object
#
def __make_response(
    code: int,
    payload: dict,
    mimetype: str = 'application/json'
) -> "Flask.response_class":
    """Generate Flask.response_class from response code and dictionary."""
    # Paranoia check
    assert(isinstance(payload, dict))
    assert(isinstance(code, int))

    try:
        #
        # Common api element for JSON responses
        #
        payload['api'] = {
            'version'   : app.apiversion,
            't_cpu'     : time.process_time() - g.t_cpu_start,
            't_real'    : time.perf_counter() - g.t_real_start
        }
        # NOTE: PLEASE remove 'indent' and 'sort_keys' when developing is done!!!
        # 'default=str' is useful setting to handle obscure data, leave it.
        # (for example; "datetime.timedelta(31) is not JSON serializable")
        # https://stackoverflow.com/questions/7907596/json-dumps-vs-flask-jsonify
        t = time.perf_counter()
        #payload = json.dumps(payload, indent=4, sort_keys=True, default=str)
        #app.logger.debug("REMOVE SORT! json.dumps(): {:.1f}ms".format((time.perf_counter() - t) * 1000))
        payload = json.dumps(payload, default=str)

        response = app.response_class(
            response    = payload,
            status      = code,
            mimetype    = mimetype
        )
        # Send list of allowed methods for this endpoint in the header
        allow = [method for method in request.url_rule.methods if method not in ('HEAD', 'OPTIONS')]
        response.headers['Allow']        = ", ".join(allow)
        response.headers['Content-Type'] = mimetype
        return response
    except Exception as e:
        # VERY IMPORTANT! Do NOT re-raise the exception!
        app.logger.exception("api.__make_response(): Internal error!")
        # We will try to offer dict instead of Flask.Response...
        #return ("api.__make_response() Internal Error!", 500)
        return app.response_class(
            response = f"api.__make_response() Internal Error: {str(e)}",
            status   = 500
        )



#
# api.response((code:int, payload:dict):tuple) -> Flask.response_class
# JSON Flask.Response create function for Flask route handlers
#
def response(response_tuple: tuple, mimetype: str = 'application/json'):
    """Create Flask.Response from provided (code:int, data:dict):tuple."""
    return __make_response(response_tuple[0], response_tuple[1], mimetype)


#
# api.exception_response(ApiException | Exception)
# Exception handling function for Flask route handlers
#
#   Generate payload dictionary from the ApiException or Exception object
#   and return through __make_response(), which generates the Flask.Response
#   object.
#
def exception_response(ex: Exception):
    """Generate JSON payload from ApiException or Exception object."""
    if not ex:
        app.logger.error("Function received argument: None!")
        return __make_response(
            500,
            {
                "error"   : "Unknown",
                "details" : "api.exception_response() received: None!"
            }
        )
    #
    try:
        if isinstance(ex, Exception):
            # Member variable '.ApiException' reveals the type
            if getattr(ex, 'ApiException', None):
                app.logger.error(
                    "ApiException: '{}'"
                    .format(str(ex))
                )
                response_code    = ex.code
                response_payload = ex.to_dict()
            else:
                # Unexpected error, log trace by using logger.exception()
                app.logger.exception(str(ex))
                from traceback import format_exception
                e = format_exception(type(ex), ex, ex.__traceback__)
                response_payload = {
                    "error" : e[-1],
                    "trace" : "".join(e[1:-1])
                }
                response_code = 500
            return __make_response(response_code, response_payload)
        else:
            return __make_response(
                500,
                {
                    "error"     : "Uknown",
                    "details"   : "api.exception_response() received unsupported argument",
                    "type"      : type(ex)
                }
            )
    except Exception as e:
        app.logger.exception("api.exception_response(): Internal Error!")
        return __make_response(
            500,
            {
                "error"     : "Internal Error",
                "details"   : "api.exception_response() internal failure!"
            }
        )


#
# UNDER TESTING (Seems to fail before streaming out 3 GB)
# https://stackoverflow.com/questions/28011341/create-and-download-a-csv-file-from-a-flask-view
#
# Takes queried cursor and streams it out as CSV file
def stream_result_as_csv(cursor):
    """Takes one argument, SQLite3 query result, which is streamed out as CSV file."""
    import io       # for StringIO
    import csv
    # Generator object for the Response() to use
    def generate(cursor):
        data = io.StringIO()
        writer = csv.writer(data)

        # Yield header
        writer.writerow(
            (key[0] for key in cursor.description)
        )
        yield data.getvalue()
        data.seek(0)
        data.truncate(0)

        # Yeild data
        for row in cursor:
            writer.writerow(row)
            yield data.getvalue()
            data.seek(0)
            data.truncate(0)

    from werkzeug.datastructures    import Headers
    from werkzeug.wrappers          import Response
    from flask                      import stream_with_context
    #
    # Response header
    #
    headers = Headers()
    headers.set(
        'Content-Disposition',
        'attachment',
        filename = time.strftime(
            "%Y-%m-%d %H.%M.%S.csv",
            time.localtime(time.time())
        )
    )

    # RFC 7111 (wich updates RFC 4180) states that the MIME type for
    # CSV is "text/csv". (Google Chrome can shut the hell up).
    #
    # Stream the response using the local generate() -generator function.
    return Response(
        stream_with_context(generate(cursor)),
        mimetype='text/csv',
        headers=headers
    )



