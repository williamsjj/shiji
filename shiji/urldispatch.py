####################################################################
# FILENAME: urldispatch.py
# PROJECT: Shiji API
# DESCRIPTION: Implements an alternative URL router for Twisted Web.
#
#           * Handles routing to the appropriate API->version->call.
#           * Allows for multiple versions of the same API to exist
#             simultaneously and for the caller to select the 
#             version they want.
# $Id$
####################################################################
# (C)2015 DigiTar Inc.
# Licensed under the MIT License.
####################################################################
import re, sys, inspect, urllib, traceback
try:
    import json
except ImportError:
    import simplejson as json
from twisted.web.resource import Resource
from twisted.web.server import NOT_DONE_YET
from twisted.internet import defer
from shiji import webapi, stats, testutil

API_VERSION_HEADER = "X-DigiTar-API-Version"

### Utility Functions
def get_version(request):
    """Locates and parses the API version headers if present."""
    raw_version = request.getHeader(API_VERSION_HEADER)
    
    if not raw_version and not request.args.has_key(API_VERSION_HEADER):
        return {"api" : "",
                "version" : "",
                "mode" : ""}
    elif not raw_version:
        raw_version = request.args[API_VERSION_HEADER][0]
    
    api = raw_version.split("-")[0].lower()
    version = raw_version.split("-")[1].split("+")[0]
    mode = raw_version.split("-")[1].split("+")[1].lower()
    
    return {"api" : api,
            "version" : version,
            "mode" : mode}


### Classes
class URLMatchJSONResource(Resource):
    """Handles storage of URL matches."""
    
    premature_finish = False
    isLeaf = True
    routes = None # Replace with regex pattern string to match at end of URL (e.g. r"route_call")
                  # For multiple routes pointing to this call use a list (e.g. [r"route1_call", r"route2_call"])
    
    def __init__(self, request, url_matches, call_router=None):
        request.setHeader("Content-Type", "application/json; charset=utf-8")
        if call_router and \
           hasattr(call_router, "version_router") and \
           hasattr(call_router.version_router, "api_router"):
                if hasattr(call_router.version_router.api_router, "cross_origin_domains") and \
                   call_router.version_router.api_router.cross_origin_domains:
                    request.setHeader("Access-Control-Allow-Origin", 
                                      call_router.version_router.api_router.cross_origin_domains)
                    request.setHeader("Access-Control-Allow-Credentials", "true")
                if hasattr(call_router.version_router.api_router, "inhibit_http_caching") and \
                   call_router.version_router.api_router.inhibit_http_caching:
                    request.setHeader("Cache-Control", "no-cache")
                    request.setHeader("Pragma", "no-cache")
        self.url_matches = url_matches
        self.call_router = call_router
        Resource.__init__(self)
    
    def render(self, request):
        """
        Override render to allow the passing of a deferred instead of NOT_DONE_YET.
        """
        
        def cb_deferred_finish(result):
            "Deferred has completed. Finish the request."
            if isinstance(request, testutil.DummyRequest):
                request._reset_body()
            
            if not result:
                result = ""
            request.write(result)
            request.finish()
        
        def eb_failed(failure):
            if isinstance(request, testutil.DummyRequest):
                request._reset_body()
            
            print failure.getTraceback()
            request.write(str(webapi.UnexpectedServerError(request,
                                                           failure.getErrorMessage())))
            request.finish()
        
        try:
            res = Resource.render(self, request)
        except Exception, e:
            if isinstance(request, testutil.DummyRequest):
                request._reset_body()
            
            tb_text = traceback.format_exc()
            print tb_text
            return str(webapi.UnexpectedServerError(request,tb_text))
        
        if isinstance(res, defer.Deferred):
            res.addCallback(cb_deferred_finish)
            res.addErrback(eb_failed)
            return NOT_DONE_YET
        else:
            return res

class CORSInterrogation(Resource):
    """
    Returned for any OPTIONS request without API version headers.
    """
    isLeaf = True
    
    def __init__(self, request, api_router):
        request.setHeader("Content-Type", "application/json; charset=utf-8")
        if hasattr(api_router, "cross_origin_domains") and \
           api_router.cross_origin_domains:
            request.setHeader("Access-Control-Allow-Origin", api_router.cross_origin_domains)
        Resource.__init__(self)

    def render_OPTIONS(self, request):
        allowed_verbs = ["PUT", "GET", "DELETE",
                         "POST", "HEAD", "TRACE",
                         "CONNECT", "PROPFIND", "PROPPATCH",
                         "MKCOL", "COPY", "MOVE", 
                         "LOCK", "UNLOCK"]
        print request.getHeader("Access-Control-Request-Headers")
        if request.getHeader("Access-Control-Request-Headers"):
            allowed_headers = request.getHeader("Access-Control-Request-Headers")
        else:
            allowed_headers = ",".join(request.getAllHeaders().keys())
        
        request.setResponseCode(200)
        request.setHeader("Access-Control-Allow-Methods", ",".join(allowed_verbs))
        request.setHeader("Access-Control-Allow-Headers", allowed_headers)
        request.setHeader("Access-Control-Allow-Credentials", "true")
        return ""

class UnknownAPI(Resource):
    """
    Returned for any unknown API.
    """
    isLeaf = True

    def render_GET(self, request):
        print "UnknownAPI: Unknown API %s" % request.uri
        request.setResponseCode(404)
        request.setHeader("Content-Type", "application/json; charset=utf-8")
        return str(webapi.UnknownAPIError(request, request.uri.split("/")[1]))
                           
    def render_POST(self, request):
        return self.render_GET(request)

class UnknownCall(Resource):
    """
    Returned for any unknown API call.
    """
    isLeaf = True

    def render_GET(self, request):
        print "UnknownAPI: Unknown API call %s" % request.uri
        request.setResponseCode(404)
        request.setHeader("Content-Type", "application/json; charset=utf-8")
        return str(webapi.UnknownAPICallError(request, request.uri.split("/")[-1]))
                           
    def render_POST(self, request):
        return self.render_GET(request)


class UnknownVersion(Resource):
    """
    Returned for any unknown API version.
    """
    isLeaf = True

    def render_GET(self, request):
        version_header = request.getHeader(API_VERSION_HEADER) if request.getHeader(API_VERSION_HEADER) != None else ""
        print ("UnknownVersion: %s is missing, invalid or specifies " % API_VERSION_HEADER) + \
               "an API/version that does not exist. %s" % version_header
        request.setResponseCode(406)
        request.setHeader("Content-Type", "application/json; charset=utf-8")
        return str(webapi.UnknownAPIVersionError(request, version_header))
                           
    def render_POST(self, request):
        return self.render_GET(request)

class ListVersionsCall (URLMatchJSONResource):
    """
    Returns a list of available versions for the current API.
    """
    routes = r"list_versions"
    
    def render_GET(self, request):
        
        versions = sorted(self.call_router.version_router.get_version_map().keys())
        
        webapi.write_json(request, {"all_versions" : versions,
                                    "curr_version" : request.api_version })

class CallRouter(Resource):
    """
    Dispatches the request to the appropriate API call handler based
    on the first 'route' match against the URL.
    
        ** If no route match is made the verb is dispatched to the 
           unknown verb handler.
    """
    
    def __init__(self, calls_module, version_router=None, auto_list_versions=False):
        """Sets up the twisted.web.Resource and loads the route map.
        
        Arguments:
            
            self - Reference to the object instance.
            calls_module (module) - Module containing API classes. Each URLMatchJSONResource 
                        class will be introspected for it's route.                               
            auto_list_versions (boolean) - If True, add an API call 'list_versions' that will
                                           list the available versions of the current API.
        """
        self.version_router=version_router
        self._createRouteMap(calls_module)
        
        if auto_list_versions:
            self.route_map.append((re.compile(r"list_versions$"), ListVersionsCall))
        
        Resource.__init__(self)
    
    def _createRouteMap(self, calls_module):
        """Introspects 'calls_module' to find URLMatchJSONResource classes and builds
        the internal route map.
        
        Arguments:
        
            calls_module (module) - Module to introspect for routes.
        
        Returns:
        
            Nothing.
        """
        
        self.route_map = []
        
        for cur_class in inspect.getmembers(sys.modules[calls_module.__name__], inspect.isclass):
            if issubclass(cur_class[1], URLMatchJSONResource):
                if cur_class[1].routes != None:
                    if isinstance(cur_class[1].routes, (str, unicode)):
                        self.route_map.append( (re.compile(cur_class[1].routes + "$"), cur_class[1]) )
                    if isinstance(cur_class[1].routes, list):
                        for route in cur_class[1].routes:
                            self.route_map.append( (re.compile(route + "$"), cur_class[1]) )
    
    def getChild(self, name, request):
        """
        Dispatches based on the route table. Named groups are passed to the called
            Resource object as a dictionary via the url_matches parameter.
        """
        
        # If no API version is attached to the request, we were called directly.
        # ...so NULL string the api_version so it doesn't break folks who expect it.
        try:
            api_mode = get_version(request)["mode"]
        except IndexError:
            return UnknownVersion()
        
        if not api_mode in ("test", "prod"):
            return UnknownVersion()
        else:
            request.api_mode = api_mode
        
        request.api_config = self.version_router.api_router.config
        for route in self.route_map:
            route_match = route[0].match("/".join(request.uri.split("?")[0].split("/")[2:]))
            if route_match:
                match_dict = route_match.groupdict()
                for key in match_dict:
                    match_dict[key] = urllib.unquote(match_dict[key])
                return route[1](request, url_matches=match_dict, call_router=self)
        
        return UnknownCall()



class VersionRouter(Resource):
    """
    Dispatches the request to the appropriate API version based
    on the first match of X-DigiTar-API-Version header against
    version map.
    """
    def __init__(self, version_map, api_router=None):
        """Sets up the twisted.web.Resource and loads the version map.
        
        Arguments:
        
            self - Reference to the object instance
            version_map (dictionary) - Dictionary of mapping tuples containing a version pattern to match, and
                                       the module to handle that version:
                                 
                                 { "0.8" : (r"0.8", v0_8"), 
                                   "1.0" : (r"1.0", v1_0") }
        """
        self.api_router = api_router
        temp_version_map = {}
        for version in version_map.keys():
            temp_version_map[version]= (re.compile(version_map[version][0] + "$"), version_map[version][1])
        self.version_map = temp_version_map
        Resource.__init__(self)
    
    def getChild(self, name, request):
        """
        Dispatches based on the version table.
        """
        
        try:
            header_version = get_version(request)["version"]
        except IndexError:
            return UnknownVersion()
        
        for version in sorted(self.version_map.keys()):
            version_match = self.version_map[version][0].match(header_version)
            if version_match:
                request.api_version = version
                self.version_map[version][1].call_router.version_router = self
                return self.version_map[version][1].call_router.getChild(name, request)
        
        return UnknownVersion()
    
    def get_version_map(self):
        """Returns the current API's version map.
        
        Arguments:
        
            NONE
        
        Returns:
        
            version_map (dict) - Dictionary where the keys are the API version numbers and
                                 the values are tuples of the format:
                                 
                                    (version_regex, module_reference)
                                
                                version_regex (raw string) - RegEx used to match against the version number
                                                             passed in the request.
                                
                                module_reference (module literal) - Module containing API.
                                
                                Ex: { "0.8" : (r"0.8", v0_8) }
        """
        
        return self.version_map

class APIRouter(Resource):
    """
    Dispatches the request to the appropriate 'API' module based
    on the first 'route' match against the URL.
    
        ** If not route match is made the verb is dispatched to the 
           unknown verb handler.
    """
    def __init__(self, route_map, config={}, cross_origin_domains=None, inhibit_http_caching=True):
        """Sets up the twisted.web.Resource and loads the route map.
        
        Arguments:
            
            self - Reference to the object instance.
            route_map (list) - List of mapping tuples containing a URL regex string to match, and
                               the module to handle the API call. Module must implement 
                               version_router member.
                               
                               (r"^/example/auth/", AuthAPI)
            config (dict) - Dictionary of optional configuration settings needed for your API.
        """
        self.cross_origin_domains = cross_origin_domains
        self.inhibit_http_caching = inhibit_http_caching
        for i in range(len(route_map)):
            route_map[i] = (re.compile(route_map[i][0] + "$"), route_map[i][1])
        self.route_map = route_map
        self.config = config
        Resource.__init__(self)
    
    def getChild(self, name, request):
        """
        Dispatches based on the route table. Named groups are passed to the called
            Resource object as a dictionary via the url_matches parameter.
        """
        request.metrics = stats.metrics
        
        if request.method.upper() == "OPTIONS":
            return CORSInterrogation(request, api_router=self)
        
        try:
            header_version = get_version(request)
        except IndexError:
            return UnknownVersion()
        
        for route in self.route_map:
            route_match = route[0].match(name)
            if route_match:
                request.api_name = route[1].api_name.lower()
                if header_version["api"] != request.api_name:
                    return UnknownVersion()
                else:
                    route[1].version_router.api_router = self
                    return route[1].version_router
        
        return UnknownAPI()
    
    def get_route_map(self):
        """Returns the API map of API names to API modules."
        
        Arguments:
        
            None
        
        Returns:
        
            route_map (dict) - Dictionary where the keys are the API names and the values 
                               are the API module literals.
                                
                                Ex: { "utilities" : utils }
        """
        
        return self.route_map


## DEPRECATED: Use CallRouter. Maintained for backwards compatibility.
class URLRouter(Resource):
    """
    Dispatches the request to the appropriate 'API' handler based
    on the first 'route' match against the URL.
    
        ** If not route match is made the verb is dispatched to the 
           unknown verb handler.
    """
    def __init__(self, route_map):
        """Sets up the twisted.web.Resource and loads the route map.
        
        Arguments:
            
            self - Reference to the object instance.
            route_map (list) - List of mapping tuples containing a URL regex string to match, and
                               the Resource object to handle the API call. ?P<arg_name> regex 
                               groups are converted to elements in a the argument dictionary passed
                               to the API call handler:
                               
                               (r"^/example/auth/(?P<auth_call>.+)", AuthAPI)
        """
        self.route_map = route_map
        Resource.__init__(self)
    
    def getChild(self, name, request):
        """
        Dispatches based on the route table. Named groups are passed to the called
            Resource object as a dictionary via the url_matches parameter.
        """
        
        for route in self.route_map:
            route_match = re.match(route[0], request.uri)
            if route_match:
                return route[1](request, url_matches=route_match.groupdict())
        
        return UnknownAPI()

