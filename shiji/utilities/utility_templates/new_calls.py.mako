# -*- coding: utf-8-*-
# ###################################################################
# FILENAME: ./${api}/${version_module}/calls.py
# PROJECT:
# DESCRIPTION: ${api} API - v${version}
#
#
# ###################################################################

from shiji import urldispatch, webapi, auth

import errors

try:
    import json
except ImportError:
    import simplejson as json

class PingCall (urldispatch.URLMatchJSONResource):
    """
    Echoes back at caller.
    """
    routes = r"ping[^/]*$"
    
    def render_GET(self, request):
        
        if request.api_mode == "prod":
            mode_string = "I'm production baby!"
        elif request.api_mode == "test":
            mode_string = "I'm in testing mode. :("
        else:
            mode_string = "I have no clue what mode I'm in."
        
        response = "PONG! Right back at ya. %s " % mode_string
        response = response + "(API: %s, Version: %s, Mode: %s)" % (request.api_name,
                                                                    request.api_version,
                                                                    request.api_mode)
        webapi.write_json(request, response)
