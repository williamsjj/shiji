# -*- coding: utf-8-*-
####################################################################
# FILENAME: webapi.py
# PROJECT: Shiji API
# DESCRIPTION: Implements web API helper classes and functions
#
#
# $Id$
####################################################################
# (C)2015 DigiTar Inc.
# Licensed under the MIT License.
####################################################################
import exceptions
try:
    import json
except exceptions.ImportError:
    import simplejson as json

## CONSTANTS/ENUM
ARG_OPTIONAL = True
ARG_REQUIRED = False

## Shiji JSON Argument Parsing Decorators
def json_arguments(arg_list, content_type="application/json"):
    """Wraps a Twisted Web render_POST function, parses the body as JSON arguments, and stores them as a dictionary
       in request.jsonArgs. If the request's Content-Type is not the same as content_type, or the request body is
       not valid JSON we'll throw  an error on-behalf of our wrapped function. Also, we'll validate to ensure the
       expected request arguments & types are present.

    Arguments:

        arg_list (list of tuples) - List of tuples where each tuple represents a request argument in the format:
                                    (arg_name, arg_type) for example an argument 'port' of type 'int':
                                        ("port", int)
        content_type (string) - Expected request Content-Type. Default: application/json

    Returns:

        A function object wrapping the original function."""

    # Validate arg_list
    if not isinstance(arg_list, list):
        if isinstance(arg_list, type(json_arguments)):
            raise Exception("You must supply the arg_list argument to the json_arguments decorator.")
        else:
            raise Exception("arg_list must be a list of tuples. arg_list is of type %s" % str(type(arg_list)))
    for arg_pair in arg_list:
        if not isinstance(arg_pair, tuple):
            raise Exception("arg_list items must be tuples. Element '%s' is of type %s" % \
                            (repr(arg_pair), arg_pair.__class__.__name__))
        if len(arg_pair) < 2:
            raise Exception("arg_list items must contain both an argument name and type: %s" % repr(arg_pair))
        
        if len(arg_pair) > 3:
            raise Exception("arg_list items may only contain an argument name, type and optional_flag: %s" % repr(arg_pair))

    def jsonValidateArgWrap(render_func):
        def jsonWrappedFilet(self, request):
            """Our super-JSON argument validating wrapper that calls the original
               render_POST func when done."""

            # Only accept requests with Content-Type equal to content_type that are UTF-8 encoded
            if request.getHeader("Content-Type") == None:
                return str(ContentTypeError(request))

            try:
                sent_content_type, sent_charset = "".join(request.getHeader("Content-Type").lower().split(" ")).split(";")
            except exceptions.ValueError:
                return str(CharsetNotUTF8Error(request))

            if sent_charset != "charset=utf-8":
                return str(CharsetNotUTF8Error(request))

            if sent_content_type != content_type:
                return str(ContentTypeError(request))

            # Convert JSON body into an argument dictionary stored in the request
            try:
                request.jsonArgs = json.loads(request.content.read().decode("utf-8"))
            except Exception, e:
                print "Request Error: Could not JSON decode request body - %s %s" % (str(type(e)), str(e))
                return str(JSONDecodeError(request))

            # Make sure what we shoved into jsonArgs was a hash/dictionary
            if not isinstance(request.jsonArgs, dict):
                return str(RequestNotHashError(request))

            # Validate individual arguments & types match what the API call expects
            for arg_pair in arg_list:
                try:
                    if len(arg_pair) < 3 or arg_pair[2] == False or request.jsonArgs.has_key(arg_pair[0]):                        
                        if not isinstance(request.jsonArgs[arg_pair[0]], arg_pair[1]):
                            raise exceptions.ValueError()
                except KeyError:
                    return str(ValueError(request, arg_pair[0], "Argument is missing."))
                except exceptions.ValueError:
                    return str(ValueError(request, arg_pair[0], "Must be of type %s" % \
                                                                arg_pair[1]().__class__.__name__))

            # As you were...
            return render_func(self, request)
        jsonWrappedFilet.__doc__ = render_func.__doc__
        return jsonWrappedFilet

    return jsonValidateArgWrap

def paged_results(default_page=0,default_page_len=50,max_page_len=100):
    """Wraps a Twisted Web render_* function. Checks for the URL query string for
       presence of 'page' and 'page_len' arguments:
                * Validates page and page_len are valid integers.
                * Validates page is > -1.
                * Validates page_len is > 0 and < max_page_len.
    Arguments:
    
          default_page (int) - page argument is set to this value if
                               page wasn't specified in the URL query string.
          default_page_len (int) - page_len argument is set to this value if
                                   page_len wasn't specified in the URL query string.
          max_page_len (int) - Maximum allowed size of result set. Any
                               page_len setting > max_page_len will trigger
                               a ValueError."""
    
    if default_page_len > max_page_len:
        raise Exception("paged_results: Default page length (%d) cannot be greater than maximum page length (%d)." % (default_page_len, max_page_len))
    
    if default_page < 0:
        raise Exception("paged_results: Default page (%d) cannot be < 0." % default_page)
    
    if default_page_len < 0:
        raise Exception("paged_results: Default page length (%d) cannot be < 0." % default_page)
    
    if max_page_len < 0:
        raise Exception("paged_results: Max page length (%d) cannot be < 0." % default_page)
    
    def pageValidateWrap(render_func):
        def wrappedFunction(self, request):
            """Wrapped render_* function. Validates result paging arguments."""
            if request.args.has_key("page_len"):
                try:
                    page_len = int(request.args["page_len"][0])
                except exceptions.ValueError:
                    return str(ValueError(request, "page_len", "Argument must be an integer."))
                
                if page_len < 0:
                    return str(ValueError(request, "page_len", "Argument must be 0 or greater."))
                if page_len > max_page_len:
                    return str(ValueError(request, "page_len", "Argument must be %d or less." % max_page_len))
            else:
                request.args["page_len"] = [str(default_page_len)]
            
            if request.args.has_key("page"):
                try:
                    page = int(request.args["page"][0])
                except exceptions.ValueError:
                    return str(ValueError(request, "page", "Argument must be an integer."))
                
                if page < 0:
                    return str(ValueError(request, "page", "Argument must be 0 or greater."))
            else:
                request.args["page"] = [str(default_page)]
            
            # As you were...
            return render_func(self, request)
        wrappedFunction.__doc__ = render_func.__doc__
        return wrappedFunction
    return pageValidateWrap
    

def url_arguments(arg_list, content_type=""):
    """Wraps a Twisted Web render_GET function. If the request's Content-Type is not the same as content_type (if
       content_type is speicfied), we'll throw  an error on-behalf of our wrapped function. Also, we'll validate
       to ensure the expected request arguments are present.

    Arguments:

        arg_list (list of strings) - List of strings, where each argument is an expected argument name.
        content_type (string) - Expected request Content-Type. Default: ""

    Returns:

        A function object wrapping the original function."""
    # Validate arg_list
    if not isinstance(arg_list, list):
        if isinstance(arg_list, type(url_arguments)):
            raise Exception("You must supply the arg_list argument to the url_arguments decorator.")
        else:
            raise Exception("arg_list must be a list. arg_list is of type %s" % str(type(arg_list)))
    for arg_pair in arg_list:
        if not isinstance(arg_pair, (str, unicode)):
            raise Exception("arg_list items must be strings. Element '%s' is of type %s" % \
                            (repr(arg_pair), arg_pair.__class__.__name__))
    
    def urlValidateArgWrap(render_func):
        def urlWrappedFilet(self, request):
            """Our super-url argument validating wrapper that calls the original
               render_GET func when done."""
            # Only accept requests with Content-Type equal to content_type that are UTF-8 encoded
            if content_type != "":
                if request.getHeader("Content-Type") == None:
                    return str(ContentTypeError(request))
                
                try:
                    sent_content_type, sent_charset = "".join(request.getHeader("Content-Type").lower().split(" ")).split(";")
                except exceptions.ValueError:
                    return str(CharsetNotUTF8Error(request))
                
                if sent_charset != "charset=utf-8":
                    return str(CharsetNotUTF8Error(request))
                
                if sent_content_type != content_type:
                    return str(ContentTypeError(request))
            
            # Validate individual arguments & types match what the API call expects
            for arg in arg_list:
                if not request.args.has_key(arg):
                    return str(ValueError(request, arg, "Argument is missing."))
            
            # As you were...
            return render_func(self, request)
        urlWrappedFilet.__doc__ = render_func.__doc__
        return urlWrappedFilet
    return urlValidateArgWrap

def auth_http_basic(auth_func, realm="Shiji"):
    """Wraps a Twisted Web render_POST function to validate a username/pass received over 
       HTTP Basic Authentication.
       
       Arguments:
       
            auth_func (function) - Function that will authenticate the username/password of the caller. 
                                   The function supplied should expect only two args: username, password."""
    
    
    def authValidateCallerWrap(render_func):
        def authWrappedFilet(self, request):
            """HTTP Basic Auth validation wrapper that calls the original render_POST
               func when done."""
            
            # Validate User
            if not auth_func(username=request.getUser(), password=request.getPassword()):
                error = AccessDeniedError(request).obj_err()
                request.setResponseCode(401)
                request.setHeader("WWW-Authenticate", 'Basic realm="%s"' % realm)
                write_json(request, error)
                return
            
            # As you were...
            return render_func(self, request)
        
        return authWrappedFilet
    
    return authValidateCallerWrap

## Shiji Output Utility Functions
def write_json(request, obj):
    """Writes the spec'd object out the HTTP request in JSON notation. Handles setting Content-Length header.
    
    Arguments:
    
        request (Twisted.web.http.Request) - HTTP request object
        obj - Object/data to JSON encode and write to the client.
    
    Returns:
    
        Success: Nothing
        Failure: Raises exception"""
    
    json_output = json.dumps(obj, ensure_ascii=False)
    request.setHeader("Content-Length", len(json_output))
    request.write(json_output.encode("utf-8"))
    
    return

## Shiji API Errors
class APIError(BaseException):
    """Generic stub for API errors. Generates JSON-encoded error dictionaries 
       for Shiji API calls.
    """
    error_code = None
    exception_class = None
    exception_text = None
    
    def __init__(self, request_object, error_code=None, exception_class=None, exception_text=None):
        """Initializes error with code, exc. class and descriptor text.
        
        Arguments:
            
            request_object (twisted.web.server.Request) - Object for current request.
            error_code (integer) - Numeric code for error.
            exception_class (string) - Camel-cased unique name for the error.
            exception_text (string) - Explanation text of what went wrong.
        
        Returns:
        
            Nothing
        """
        # Set our default HTTP Error Code to 409...this is our standard for API errors
        request_object.setResponseCode(409)
        
        if error_code != None:
            try:
                self.error_code = int(error_code)
            except Exception, e:
                raise Exception("Error code must be an integer.")
        else:
            if self.error_code == None:
                raise exceptions.ValueError("Error code must be initialized.")
        
        
        if exception_class != None:
            self.exception_class = exception_class
        elif self.exception_class == None:
            raise exceptions.ValueError("Exception class must be initialized.")
        
        if exception_text != None:
            self.exception_text = exception_text
        elif self.exception_text == None:
            raise exceptions.ValueError("Exception text must be initialized.")
        
        # If StatsD in place, log a metric point.
        if request_object.metrics:
            if hasattr(request_object, "api_name"):
                api_name = request_object.api_name
            else:
                api_name = "unknown_api"
            request_object.metrics.increment("%s.error.%s" % (api_name, exception_class))
    
    def obj_err(self):
        """Returns the Shiji API error dictionary."""
        return {"result" : None,
                "error" : {"error_code" : self.error_code,
                           "exception_class" : self.exception_class,
                           "exception_text" : self.exception_text}}
    
    def json_err(self):
        """Returns a JSON-encoded string containing a Shiji API error dictionary."""
        return json.dumps(self.obj_err(),
                          ensure_ascii=False)
    
    def __str__(self):
        return self.json_err()

class UnknownAPIError(APIError):
    """API Error: The requested API '<api_name>' is unknown."""
    error_code = 208
    exception_class = "UnknownAPIError"
    exception_text = "The requested API '%s' is unknown."
    def __init__(self, request_object, api_name):
        self.exception_text = self.exception_text % api_name
        APIError.__init__(self, request_object)
        # One of the few errors we don't use HTTP Response code 409 for...use 404
        request_object.setResponseCode(404)


class UnknownAPIVersionError(APIError):
    """API Error: API version '<api_version>' is invalid or specifies an API/version that does not exist."""
    error_code = 207
    exception_class = "UnknownAPIVersionError"
    exception_text = "API version '%s' is invalid or specifies an API/version that does not exist."
    def __init__(self, request_object, api_version):
        self.exception_text = self.exception_text % api_version
        APIError.__init__(self, request_object)
        # One of the few errors we don't use HTTP Response code 409 for...use 404
        request_object.setResponseCode(406)

class UnknownAPICallError(APIError):
    """API Error: The requested API call '<call_name>' is unknown."""
    error_code = 203
    exception_class = "UnknownAPICallError"
    exception_text = "The requested API call '%s' is unknown."
    def __init__(self, request_object, call_name):
        self.exception_text = self.exception_text % call_name
        APIError.__init__(self, request_object)
        # One of the few errors we don't use HTTP Response code 409 for...use 404
        request_object.setResponseCode(404)

class JSONEncodeError(APIError):
    """API Error: An unrecoverable error has occurred JSON-encoding the API call result."""
    error_code = 204
    exception_class = "JSONEncodeError"
    exception_text = "An unrecoverable error has occurred JSON-encoding the API call result."

class JSONDecodeError(APIError):
    """API Error: An unrecoverable error has occurred JSON-decoding the API call request."""
    error_code = 205
    exception_class = "JSONDecodeError"
    exception_text = "Arguments passed in API call request are not validly formed JSON."

class RequestNotHashError(APIError):
    """API Error: Request body was not a JSON-encoded dictionary...it's some other datatype."""
    error_code = 206
    exception_class= "RequestNotHashError"
    exception_text = "Request body must be a JSON-encoded hash table/dictionary."

class AccessDeniedError(APIError):
    """API Error: Insufficient permission to perform the requested action."""
    error_code = 501
    exception_class = "AccessDeniedError"
    exception_text = "Insufficient permission to perform the requested action."

class ValueError(APIError):
    """API Error: The specified argument was invalid."""
    error_code = 502
    exception_class = "ValueError"
    exception_text = "Invalid value for argument '%s'. %s"
    def __init__(self, request_object, arg_name, extra_desc):
        self.exception_text = self.exception_text % (arg_name, extra_desc)
        APIError.__init__(self, request_object)

class ContentTypeError(APIError):
    """API Error: The API request specified a Content-Type other than 'application/json'."""
    error_code = 503
    exception_class = "ContentTypeError"
    exception_text = "The Content-Type of the API request was not of the expected " + \
                     "format...or the API/version requested does not exist."
    def __init__(self, request_object):
        APIError.__init__(self, request_object)
        # One of the few errors we don't use HTTP Response code 409 for...use 406
        request_object.setResponseCode(406)

class CharsetNotUTF8Error(APIError):
    """API Error: The API request specified a Content-Type without a charset, or spec'd charset other than UTF-8."""
    error_code = 504
    exception_class = "CharsetNotUTF8Error"
    exception_text = "The Content-Type of the API request did not specify a charset," + \
                     " or the charset specified was not UTF-8."

class UnexpectedServerError(APIError):
    """API Error: An unexpected server error has occurred processing the API request."""
    error_code = 505
    exception_class = "UnexpectedServerError"
    exception_text = "An unexpected error has occurred processing the request. Error: '%s'"
    def __init__(self, request_object, error_msg):
        self.exception_text = self.exception_text % error_msg
        APIError.__init__(self, request_object)

class InvalidAuthenticationError(APIError):
    """API Error: Authentication information is invalidly formed and/or missing required elements."""
    error_code = 506
    exception_class = "InvalidAuthenticationError"
    exception_text = "Authentication information is invalidly formed and/or missing required elements."

class InvalidSecureCookieError(APIError):
    """API Error: Secure cookie signature is invalid."""
    error_code = 507
    exception_class = "InvalidSecureCookieError"
    exception_text = "Secure cookie '%s' signature '%s' is invalid."
    def __init__(self, request_object, name, signature):
        self.exception_text = self.exception_text % (name, signature)
        APIError.__init__(self, request_object)

class ExpiredSecureCookieError(APIError):
    """API Error: Secure cookie is expired."""
    error_code = 508
    exception_class = "ExpiredSecureCookieError"
    exception_text = "Secure cookie '%s' is expired."
    def __init__(self, request_object, name):
        self.exception_text = self.exception_text % name
        APIError.__init__(self, request_object)