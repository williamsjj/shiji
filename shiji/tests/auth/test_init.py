####################################################################
# FILENAME: auth/test_init.py
# PROJECT: Shiji API
# DESCRIPTION: Tests auth.__init__ module.
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

from twisted.trial import unittest
from shiji import auth
from shiji import webapi
from shiji.testutil import DummyRequest
from shiji.auth import errors, base_backend
import base64, datetime, email.utils

class BadBackend(object):
    
    def __init__(self):
        pass

class DummyBackend(base_backend.AuthBackend):
    def __init__(self):
        pass

class InstallAuthTestCase(unittest.TestCase):
    
   def test_backend_obj_not_authbackend(self):
       "Validate backend installation fails if not AuthBackend"
       obj = BadBackend()
       self.assertRaises(errors.AuthBadBackend, auth.install_auth, obj)
   
   def test_backend_installed(self):
       "Validate backend installation fails if not object."
       backend = DummyBackend()
       auth.install_auth(backend)
       self.assertEqual(auth.auth_backend, backend)

class SecureCookiesTestCase(unittest.TestCase):
    
    def test_secure_cookies_installed(self):
        "Validate installation of secure cookies secret."
        auth.install_secure_cookies(["supersecret"])
        self.assertEqual(auth.cookie_secrets, ["supersecret"])
    
    def test_set_secure_cookie(self):
        "Validate setting a secure cookie."
        request = DummyRequest()
        
        auth.install_secure_cookies(["supersecret"])
        auth.set_secure_cookie(request, "testkey", "testvalue")
        
        self.assertEqual(1, len(request.cookies))
        key, value = request.cookies[0].split("=", 1)
        value, expires, path = value.split(";")
        path = path.split("=")[1]
        expires = (datetime.datetime(*email.utils.parsedate(expires.split("=")[1])[:6])-datetime.datetime.utcnow()).days
        value, timestamp, signature = value.split("|")
        
        self.assertEqual("/", path)
        self.assertEqual(29, expires)
        self.assertEqual("testkey", key)
        self.assertEqual(base64.b64encode("testvalue"), value)
        self.assertTrue(timestamp > 0)
        
        expected_signature = auth._cookie_signature(value, timestamp)[0]
        self.assertEqual(expected_signature, signature)
    
    def test_get_secure_cookie_ok(self):
        "Validate retrieving a secure cookie."
        auth.install_secure_cookies(["supersecret"])
        raw_value = "testvalue"
        timestamp = "1360023531"
        signature = "e90904d67de2fd6e4d4f3c9a736e3b8c457526f9"
        secure_cookie_val = "%s|%s|%s" % (base64.b64encode(raw_value), timestamp, signature)
        request = DummyRequest()
        request.received_cookies["testkey"] = secure_cookie_val
        value = auth.get_secure_cookie(request, "testkey", expiry_days=36500)
        self.assertEqual(value, raw_value)
    
    def test_get_secure_cookie_invalid(self):
        "Test retrieving an invalid secure cookie."
        auth.install_secure_cookies(["supersecret"])
        raw_value = "testvalue"
        timestamp = "1360023531"
        signature = "badsig"
        secure_cookie_val = "%s|%s|%s" % (base64.b64encode(raw_value), timestamp, signature)
        request = DummyRequest()
        request.received_cookies["testkey"] = secure_cookie_val
        value = auth.get_secure_cookie(request, "testkey")
        self.assertTrue(isinstance(value, webapi.InvalidSecureCookieError))
    
    def test_get_secure_cookie_expired(self):
        "Test retrieving an invalid secure cookie."
        auth.install_secure_cookies(["supersecret"])
        raw_value = "testvalue"
        timestamp = "1357260056"
        signature = "d304db1dbf1bc2fcb4eb6bc71bfd22cae4e74b74"
        secure_cookie_val = "%s|%s|%s" % (base64.b64encode(raw_value), timestamp, signature)
        request = DummyRequest()
        request.received_cookies["testkey"] = secure_cookie_val
        value = auth.get_secure_cookie(request, "testkey")
        self.assertTrue(isinstance(value, webapi.ExpiredSecureCookieError))
    
    def test_cookie_signature(self):
        "Test that secure cookie algorithm is outputting correct signatures."
        auth.install_secure_cookies(["supersecret"])
        value = base64.b64encode("testvalue")
        timestamp = "1360023531"
        expected_signature = ["e90904d67de2fd6e4d4f3c9a736e3b8c457526f9"]
        
        self.assertEqual(expected_signature,
                         auth._cookie_signature(value, timestamp))
    
    def test_get_secure_cookie_ok_multiple_secrets(self):
        "Validate retrieving a secure cookie with multiple secrets installed."
        auth.install_secure_cookies(["supersecret","supersecret1"])
        raw_value = "testvalue"
        timestamp = "1360023531"
        signature = "e90904d67de2fd6e4d4f3c9a736e3b8c457526f9"
        secure_cookie_val = "%s|%s|%s" % (base64.b64encode(raw_value), timestamp, signature)
        request = DummyRequest()
        request.received_cookies["testkey"] = secure_cookie_val
        value = auth.get_secure_cookie(request, "testkey", expiry_days=36500)
        self.assertEqual(value, raw_value)
    
    def test_get_secure_cookie_invalid_multiple_secrets(self):
        "Test retrieving an invalid secure cookie with multiple secrets installed."
        auth.install_secure_cookies(["supersecret1","supersecret"])
        raw_value = "testvalue"
        timestamp = "1360023531"
        signature = "badsig"
        secure_cookie_val = "%s|%s|%s" % (base64.b64encode(raw_value), timestamp, signature)
        request = DummyRequest()
        request.received_cookies["testkey"] = secure_cookie_val
        value = auth.get_secure_cookie(request, "testkey")
        self.assertTrue(isinstance(value, webapi.InvalidSecureCookieError))
    
    def test_get_secure_cookie_expired_multiple_secrets(self):
        "Test retrieving an invalid secure cookie with multiple secrets installed."
        auth.install_secure_cookies(["supersecret1","supersecret"])
        raw_value = "testvalue"
        timestamp = "1357260056"
        signature = "d304db1dbf1bc2fcb4eb6bc71bfd22cae4e74b74"
        secure_cookie_val = "%s|%s|%s" % (base64.b64encode(raw_value), timestamp, signature)
        request = DummyRequest()
        request.received_cookies["testkey"] = secure_cookie_val
        value = auth.get_secure_cookie(request, "testkey")
        self.assertTrue(isinstance(value, webapi.ExpiredSecureCookieError))
        
