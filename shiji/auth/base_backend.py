# -*- coding: utf-8-*-
####################################################################
# FILENAME: auth/base_backend.py
# PROJECT: Shiji API
# DESCRIPTION: Shiji Auth - Authentication backend base class.
#
# $Id$
####################################################################
# (C)2015 DigiTar Inc.
# Licensed under the MIT License.
####################################################################
from twisted.internet.defer import Deferred
from twisted.internet import reactor
import errors

class AuthBackend(object):
    """Base class API authentication backends. All Shiji auth backends
    must implement the interface defined by this class."""
    
    def __init__(self):
        """Backend-specific setup and configuration."""
        raise errors.AuthNoBackend("No authentication backend configured.")
    
    def perm_list(self):
        """Returns the current list of permissions.
        
        Arguments:
            NONE
        
        Results:
            (list of strings) - List of current permission IDs
        """
        raise errors.AuthNoBackend("No authentication backend configured.")
    
    def authenticate(self, request):
        """Authenticate the request. Returns the permissions and 
        authentication name space for the supplied credentials.
        
        Arguments:
        
            request (t.w.http.Request) - HTTP request object.
        
        Returns:
        
            Immediate Return: Twisted Deferred
            
            Eventual Return (dict):
                <auth_name_space> (list of strings) : The permission IDs the
                                validated user possesses for this authentication
                                namespace.
            
                (There's a key/value pair for each authentication namespace
                 that the user has permissions in.)
        """
        
        def cb_finish_authentication(result):
            raise errors.AuthNoBackend("No authentication backend configured.")
        
        d = Deferred().addCallback(cb_finish_authentication)
        reactor.callLater(2, d.callback, "")
        return d
