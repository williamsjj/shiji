# -*- coding: utf-8-*-
####################################################################
# FILENAME: ./dummy_api/v1_0/calls.py
# PROJECT: Shiji API
# DESCRIPTION: Dummy API Call Logic (list of routes)
#
#
# $Id$
####################################################################
# (C)2015 DigiTar Inc.
# Licensed under the MIT License.
####################################################################


from shiji import urldispatch, webapi
try:
    import json
except ImportError:
    import simplejson as json

class PingCall (urldispatch.URLMatchJSONResource):
    """
    Echoes back at caller.
    """
    routes = [r"ping(?P<group1>.*)", r"me"]
    
    def render_GET(self, request):
        
        if request.api_mode == "prod":
            mode_string = "I'm production baby!"
        elif request.api_mode == "test":
            mode_string = "I'm in testing mode. :("
        else:
            mode_string = "I have no clue what mode I'm in."
        webapi.write_json(request, "POLLS PONG! Right back at ya. %s (API: %s, Version: %s, Mode: %s)" % (mode_string,
                                                                                                          request.api_name,
                                                                                                          request.api_version,
                                                                                                          request.api_mode))
                                                                                                          
                                                                                                          
                                                                                                    
