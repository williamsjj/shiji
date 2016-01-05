# -*- coding: utf-8-*-
####################################################################
# FILENAME: auth/__init__.py
# PROJECT: Shiji API
# DESCRIPTION: Shiji Auth - API authentication
#
# $Id$
####################################################################
# (C)2015 DigiTar Inc.
# Licensed under the MIT License.
####################################################################
from twisted.web.server import NOT_DONE_YET
from shiji.webapi import AccessDeniedError, InvalidAuthenticationError, ExpiredSecureCookieError, InvalidSecureCookieError, UnexpectedServerError
import base64, hashlib, time, hmac, datetime, locale
import errors, base_backend

auth_backend = None
cookie_secrets = None

def install_secure_cookies(secrets):
    """Sets up the secure cookie secret.
    
    Argumetns:
    
        secrets (list of strings) - List of valid secrets to use for secure cookies.
    
    Returns:
    
        Success: True
        Failure: Raises an exception"""
    
    global cookie_secrets
    
    if not isinstance(secrets, list):
        raise Exception("Cookie secrets must be a list not %s." % str(type(secrets)))
        
    cookie_secrets = secrets
    
    return True

def install_auth(backend):
    """Installs an authentication backend.
    
    Arguments:
    
        backend (base_backend.AuthBackend) - Authentication backend 
                    to use to authenticate clients. Must be 
                    subclassed from base_backend.AuthBackend.
    
    Returns:
    
        Success: True
        Failure: Raises an exeption.
    """
    global auth_backend
    
    # Make sure supplied backend is derived from AuthBackend
    try:
        if not issubclass(backend.__class__, base_backend.AuthBackend):
            raise errors.AuthBadBackend("Supplied backend must be a subclass of AuthBackend.")
    except TypeError:
        raise errors.AuthBadBackend("Supplied backend must be a subclass of AuthBackend.")
    auth_backend = backend


def access(auth_ns_var, all_required=False, *args):
    """
    When decorating the render_X of a URLMatchJSONResource, validates that the
    caller's authentication credentials are valid and provide at least one of
    the permissions in args. Also adds the user's authentication namespace
    onto the Request object, so that API calls can restrict access to only 
    records within the user's auth namespace (e.g. their organization).
    
    Arguments:
        auth_ns_var (string) - HTTP variable name in the request that contains
                               the authentication namespace the request wants
                               to operate in. For example if "domain=digitar.com",
                               is passed in the request and that means do the 
                               operation inside the customer "digitar.com" then
                               'auth_ns_var' would be set to "domain".
        
        all_required (bool) - Whether authenticated caller must satisfy ALL of
                              the specified permissions.
                              
        *args (list of strings) - permissions that must be satisfied (if all_required is False,
                                  first permission match wins and permission matching stops)
    """
    
    def accessWrap(render_func):
        
        def eb_auth_error(failure, request):
            if failure.check(errors.InvalidAuthentication):
                error_text = str(InvalidAuthenticationError(request))
            if failure.check(errors.NotAuthorized):
                error_text = str(AccessDeniedError(request))
            else:
                failure.printTraceback()
                error_text = str(UnexpectedServerError(request,
                                                       failure.getErrorMessage()))
            request.write(error_text)
            request.finish()
        
        def cb_validate_perms(auth_return, self, request):
            """Called by the authentication backend when authentication succeeds.
            
            Arguments:
                auth_return (dict of lists) : Dictionary containing a key for each
                                              authentication namespace the user
                                              possesses permissions in. The value of
                                              each key is the list of permission IDs
                                              (strings) that the user possesses in that
                                              authentication namespace.
                self (object) : Reference to the object instance that the method we're
                                decorating belongs to.
                request (t.w.h.Request) - Request object for the HTTP request being
                                          authenticated.
            """
            # Acquire the authentication namespace of the current request
            # (prefer jsonArgs over args)
            if hasattr(request, "jsonArgs") and request.jsonArgs.has_key(auth_ns_var):
                    auth_ns = request.jsonArgs[auth_ns_var]
            elif hasattr(request, "url_matches") and request.url_matches.has_key(auth_ns_var):
                    auth_ns = request.url_matches[auth_ns_var]
            else:
                try:
                    auth_ns = request.args[auth_ns_var][0]
                except AttributeError:
                    raise errors.InvalidAuthentication("Request does not possess any arguments.")
                except KeyError:
                    raise errors.InvalidAuthentication("Request is missing required variable %s" % auth_ns_var)
            
            # Validate permissions
            possessed_perms = 0
            try:
                for permission in auth_return[auth_ns]:
                    if permission in args:
                        possessed_perms = possessed_perms + 1
            except KeyError:
                raise errors.NotAuthorized("Insufficient permissions")
            
            if all_required and (possessed_perms < len(args)):
                raise errors.NotAuthorized("Insufficient permissions")
            elif not possessed_perms:
                raise errors.NotAuthorized("Insufficient permissions")
            
            # Attach permissions and namespace to the request
            request.permissions = auth_return[auth_ns]
            request.auth_namespace = auth_ns
            
            # Permissions validated call original render
            result = render_func(self, request)
            if result != NOT_DONE_YET:
                request.write(result)
                request.finish()
            
            return
        
        def newRenderFunc(self, request):
            
            # Make sure auth backend has been initialized
            if auth_backend == None:
                raise errors.AuthNoBackend("No authentication backend has been setup.")
            
            # Authenticate request & process result
            auth_backend.authenticate(request).addCallback(cb_validate_perms, self, request
                                             ).addErrback(eb_auth_error, request)
            
            return NOT_DONE_YET
        
        return newRenderFunc
    
    return accessWrap


### SECURE COOKIE FUNCTIONS (modified from Tornado for use with Twisted Web)
def set_secure_cookie(request, name, value, expires_days=30, path="/", **kwargs):
    """Signs and timestamps a cookie so it cannot be forged.

    You must specify the 'cookie_secrets' setting in your Shiji Auth config.
    Set secure cookie always uses the first secret.

    To read a cookie set with this method, use get_secure_cookie().
    """
    timestamp = str(int(time.time()))
    value = base64.b64encode(value)
    signature = _cookie_signature(value, timestamp)[0]
    value = "|".join([value, timestamp, signature])
    locale.setlocale(locale.LC_TIME, 'en_US.UTF-8')
    expiry = (datetime.datetime.utcnow() + datetime.timedelta(days=expires_days)).strftime('%a, %d %b %Y %H:%M:%S GMT')
    request.addCookie(name, value, expires=expiry, path=path, **kwargs)

def get_secure_cookie(request, name, expiry_days=31):
    """Returns the given signed cookie if it validates, or None."""
    value = request.getCookie(name)
    if not value: return None
    parts = value.split("|")
    if len(parts) != 3: return None
    
    # Iterate through possible cookie signatures for validation
    for valid_sig in _cookie_signature(parts[0], parts[1]):
        if valid_sig == parts[2]:
            timestamp = int(parts[1])
            if timestamp < time.time() - (expiry_days * 86400):
                return ExpiredSecureCookieError(request, name)
            else:
                return base64.b64decode(parts[0])
    
    # ...didn't match any valid signatures
    return InvalidSecureCookieError(request, name, parts[2])
    
def _cookie_signature(*parts):
    global cookie_secrets
    
    # Calculate the signature for every
    # cookie secret in play...
    signatures = []
    for secret in cookie_secrets:
        hash = hmac.new(secret, digestmod=hashlib.sha1)
        for part in parts: hash.update(part)
        signatures.append(hash.hexdigest())
    
    return signatures
