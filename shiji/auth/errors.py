# -*- coding: utf-8-*-
####################################################################
# FILENAME: auth/errors_.py
# PROJECT: Shiji API
# DESCRIPTION: Shiji Auth exceptions
#
#
# $Id$
####################################################################
# (C)2015 DigiTar Inc.
# Licensed under the MIT License.
####################################################################

### Auth Exceptions
class AuthBaseException(Exception):
    
    def __init__(self, value):
        self.value = value
    
    def __str__(self):
        return str(self.value)


class AuthBadBackend(AuthBaseException):
    """An authentication backend was supplied that does 
     not implement the AuthBackend interfaces."""
    
class AuthNoBackend(AuthBaseException):
    """No authentication backend is setup for Shiji Auth."""

class InvalidAuthentication(AuthBaseException):
    """Authentication information is invalidly formed and/or missing required elements."""

class NotAuthorized(AuthBaseException):
    """Supplied credentials are not authorized to access the requested resource."""
    
class BackendWarmingUp(AuthBaseException):
    """Backend is warming up and not yet ready for requests."""