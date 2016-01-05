####################################################################
# FILENAME: foundation.py
# PROJECT: Shiji API
# DESCRIPTION: Implements foundational classes for HTTP requests.
#
#           * Site serving and Request handling.
# $Id$
####################################################################
# (C)2015 DigiTar Inc.
# Licensed under the MIT License.
####################################################################
from twisted.web.server import Request, Site

### Classes
class ShijiRequest(Request):
    """Twisted Request w/ metrics plumbing"""
    metrics = None
    
    def __init__(self, channel, queued):
        return Request.__init__(self, channel, queued)
    
    def getClientIP(self, **kwargs):
        """Override base getClientIP to be X-Real-IP aware.
        
        Arguments:
        
            honor_xrealip (bool)(optional) - (If present, overrides the default
                                              for honor_xrealip specified in the config file.)
                                             
                                             Whether or not to prefer the value of
                                             the X-Real-IP header if present.
        """
        if kwargs.has_key("honor_xrealip"):
            honor_xrealip = kwargs["honor_xrealip"]
        else:
            honor_xrealip = self.site.honor_xrealip
        
        if honor_xrealip and self.getHeader("X-Real-IP"):
            return self.getHeader("X-Real-IP")
        
        return Request.getClientIP(self)

class ShijiSite(Site):
    """Twisted Site server w/ metrics plumbing."""
    requestFactory = ShijiRequest
    
    def __init__(self, resource, logPath=None, timeout=60*60*12, honor_xrealip=True):
        Site.__init__(self, resource, logPath=logPath, timeout=timeout)
        self.honor_xrealip = honor_xrealip