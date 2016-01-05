# ###################################################################
# FILENAME: ./mylogin_api/v1_0/calls.py
# PROJECT:
# DESCRIPTION: mylogin_api API - v1.0
#
#
# ###################################################################

from shiji import urldispatch, webapi, auth
from twisted.internet import defer, reactor
from twisted.web.client import Agent

import time

import errors

try:
    import json
except ImportError:
    import simplejson as json

class PingCall (urldispatch.URLMatchJSONResource):
    """
    Echoes back at caller.
    """
    routes = r"ping/(?P<timestamp>\d+)$"
    
    def render_GET(self, request):
        """
        Simple PING call, that echoes back the client's supplied timestamp.
        
        URL Path Arguments:
        ----------
            timestamp (int) - Client supplied UNIX timestamp.
        
        
        Returns
        ---------
        
            Success:
                (unicode) - String echoing parameters.
        
            Failure:
                Returns a JSON error dictionary.
        
        """
        timestamp =  int(self.url_matches["timestamp"])
        
        if request.api_mode == "prod":
            mode_string = "I'm production baby!"
        elif request.api_mode == "test":
            mode_string = "I'm in testing mode. :("
        else:
            mode_string = "I have no clue what mode I'm in."
        
        response = "PONG! Right back at ya. %s " % mode_string
        response = response + " (Timestamp Val: %d) " % timestamp
        response = response + "(API: %s, Version: %s, Mode: %s)" % (request.api_name,
                                                                    request.api_version,
                                                                    request.api_mode)
        webapi.write_json(request, response)
    
    @webapi.json_arguments([("client_tz", int),
                            ("client_id", unicode),
                            ("new_client", bool, webapi.ARG_OPTIONAL)])
    @webapi.url_arguments(["simple_auth_key"])
    @defer.inlineCallbacks
    def render_POST(self, request):
        """
        Calculate the latency of querying example.com.
        
        URL Path Arguments:
        ----------
            timestamp (int) - Client supplied UNIX timestamp.
        
        JSON Body Arguments:
        ----------
            client_tz (int) - Client's timezone offset from GMT.
            client_id (unicode) - Client's unique client ID string.
            new_client (bool) (optional) - Does magic if true...
            
        Returns:
        ----------
        
        Success:
                "result" : {
                    "latency" (float) - Time it took to complete example.com request in secs.
                    "client_tz" (int) - Supplied client timezone offset.
                    "client_id" (unicode) - Supplied unique client ID.
                    "new_client" (bool) - Whether magic happened...
                }
    
        Failure:
            Returns a JSON error dictionary.
        
        """
        # Make sure simple_auth_key is a good key
        auth_key = request.args["simple_auth_key"][0]
        if auth_key != "abc":
            defer.returnValue(str(webapi.ValueError(request, 
                                                    "simple_auth_key",
                                                    "Key isn't valid!")))
        
        # Test latency to request example.com
        start_time = time.time()
        web_agent = Agent(reactor)
        resp = yield web_agent.request("GET", "http://example.com")
        end_time = time.time()
        
        # new_client is an optional parameter,
        # so set a default value if it isn't present
        # in the JSON arguments
        new_client = False
        if request.jsonArgs.has_key("new_client"):
            new_client = request.jsonArgs["new_client"]
        
        # Return a JSON dictionary as the API call result.
        return_dict = {"result" : {"latency" : end_time-start_time,
                                   "client_tz" : request.jsonArgs["client_tz"],
                                   "client_id" : request.jsonArgs["client_id"],
                                   "new_client" : request.jsonArgs["new_client"]}}
        
        defer.returnValue(json.dumps(return_dict))
