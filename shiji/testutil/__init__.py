####################################################################
# FILENAME: testutil/__init__.py
# PROJECT: Shiji API
# DESCRIPTION: Test utility lib for doing Twisted tests in 
#              Nosetests.
# 
#               Requires: TwistedWeb >= 10.0
#                         (Python 2.5 & SimpleJSON) or Python 2.6
#
#
# $Id$
####################################################################
# (C)2015 DigiTar Inc.
# Licensed under the MIT License.
####################################################################

from shiji.stats import FakeStatsDClient
from txstatsd.metrics.metrics import Metrics
from twisted.internet.defer import Deferred
from twisted.internet import address
from twisted.web.test.test_web import DummyChannel
from twisted.web.http import parse_qs
from StringIO import StringIO
from shiji import foundation
import traceback

def expect_failure(exp_exceptions):
    """(decorator) Validates that the deferred from the wrapped 
    function raises one of the specified exceptions.
    
    Arguments:
        exp_exceptions (Exception or list of Exceptions) - Exceptions
                                                expected to be raised.
    """
    
    def wrap(test_func):
        def enh_func(*args, **kwargs):
            def cb_succeeded(*args, **kwargs):
                raise Exception("FAILURE: Test succeeded when it should " + \
                                "have raised one of: %s" % repr(exp_exceptions))
            
            def eb_failed(failure):
                if not failure.check(exp_exceptions):
                    failure.raiseException()
            
            return test_func(args, kwargs).addCallback(cb_succeeded
                                         ).addErrback(eb_failed)
        return enh_func
    return wrap


def assert_equals(val1, val2):
    """Asserts that val1 is the same as val2. If val1 is a Deferred, defers 
    evaluation of the assertion until the deferred is fired.
    
    Arguments:
        val1 (object)
        val2 (object)
    
    Returns:
        True if assertion succeeds.
    """
    
    def cb_eval(value):
        assert value == val2
        return True
    
    if isinstance(val1, Deferred):
        return val1.addCallback(cb_eval)
    else:
        assert val1 == val2
        return True

class DummyRequestNew(foundation.ShijiRequest):
    """This is an attempt to replace DummyRequest with one based on ShijiRequest so
        that changes to ShijiRequest show up automatically. So far this raises issues
        in test_urldispatch based on expectations in DummyRequest. Need to clean those
        up before this can be used."""
    
    def __init__(self, channel=DummyChannel(), queued=None, api_mode="test", api_version="0.1", api_name="TestAPI", uri="",
                 method="GET", user="", password=""):
        self.client =  address.IPv4Address('TCP', "1.2.3.4", 40323)
        self.api_mode = api_mode
        self.api_version = api_version
        self.api_name = api_name
        self.save_channel = channel
        
        return foundation.ShijiRequest.__init__(self, channel, queued)
    
    def decode_content(self):
        return self.save_channel.transport.written.getvalue().split("\r\n\r\n")[1]
    
    def setHeader(self, name, value):
        self.requestHeaders.addRawHeader(name, value)
    
    def _reset_body(self):
        self.channel = DummyChannel()
        self.save_channel = self.channel

# Dummy Classes
class DummyRequest(object):
    """Dummy request object that imitates twisted.web.http.Request's
    interfaces."""
    
    finished = 0
    response_code = 200
    response_msg = None
    metrics = Metrics(FakeStatsDClient(), 'webprotectme.null')
    
    def __init__(self, api_mode="test", api_version="0.1", api_name="TestAPI", uri="",
                 method="GET", user="", password=""):
        self.headers = {}
        self.args = {}
        self.cookies = []
        self.received_cookies = {}
        self.client_ip = "4.3.2.1"
        self.content = StringIO()
        self._finishedDeferreds = []
        self.api_mode = api_mode
        self.api_version = api_version
        self.api_name = api_name
        self.uri = uri
        self.user = user
        self.password = password
        self.method = method
        self.ignore_auth = True
        self.ignore_secure_cookies = True
        
        x = self.uri.split(b'?', 1)

        if len(x) == 1:
            self.path = self.uri
        else:
            self.path, argstring = x
            self.args = parse_qs(argstring, 1)
    
    def _reset_body(self):
        self.content = StringIO()
    
    def setHeader(self, name, value):
        self.headers[name] = value
    
    def getAllHeaders(self):
        return self.headers
    
    def getHeader(self, header):
        try:
            return self.headers[header]
        except KeyError:
            return
    
    def addCookie(self, k, v, expires=None, domain=None, path=None, max_age=None, comment=None, secure=None):
        """
        Set an outgoing HTTP cookie.

        In general, you should consider using sessions instead of cookies, see
        L{twisted.web.server.Request.getSession} and the
        L{twisted.web.server.Session} class for details.
        """
        cookie = '%s=%s' % (k, v)
        if expires is not None:
            cookie = cookie +"; Expires=%s" % expires
        if domain is not None:
            cookie = cookie +"; Domain=%s" % domain
        if path is not None:
            cookie = cookie +"; Path=%s" % path
        if max_age is not None:
            cookie = cookie +"; Max-Age=%s" % max_age
        if comment is not None:
            cookie = cookie +"; Comment=%s" % comment
        if secure:
            cookie = cookie +"; Secure"
        self.cookies.append(cookie)
    
    def getCookie(self, key):
        """
        Get a cookie that was sent from the network.
        """
        return self.received_cookies.get(key)
    
    def write(self, data):
        cookie_data = ""
        for cookie in self.cookies:
            cookie_data = cookie_data + ('%s: %s\r\n' % ("Set-Cookie", cookie))
        
        if cookie_data != "":
            cookie_data = cookie_data + "\r\n"
            self.content = StringIO(cookie_data + self.content.getvalue() + data)
            self.cookies = []
        else:
            self.content = StringIO(self.content.getvalue() + data)
    
    def notifyFinish(self):
        """
        Return a L{Deferred} which is called back with C{None} when the request
        is finished.  This will probably only work if you haven't called
        C{finish} yet.
        """
        finished = Deferred()
        self._finishedDeferreds.append(finished)
        return finished
    
    def getClientIP(self, honor_xrealip=False):
        """
        Return request IP
        """
        if honor_xrealip and self.getHeader("X-Real-IP"):
            return self.getHeader("X-Real-IP")
        
        return self.client_ip
    
    def finish(self):
        self.finished = self.finished + 1
        if self._finishedDeferreds is not None:
            observers = self._finishedDeferreds
            self._finishedDeferreds = None
            for obs in observers:
                obs.callback(None)
    
    def setResponseCode(self, code, message=None):
        self.response_code = code
        self.response_msg = message
    
    def getUser(self):
        return self.user
    
    def getPassword(self):
        return self.password

    