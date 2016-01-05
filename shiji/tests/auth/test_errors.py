####################################################################
# FILENAME: auth/test_errors.py
# PROJECT: Shiji API
# DESCRIPTION: Tests auth.errors module.
# 
#               Requires: TwistedWeb >= 10.0
#                         (Python 2.5 & SimpleJSON) or Python 2.6
#
# 
#
# $Id$
####################################################################
# (C)2015 DigiTar Inc.
# Licensed under the MIT License.
####################################################################

from twisted.trial import unittest
from shiji.auth import errors, base_backend

class AuthBaseExceptionTestCase(unittest.TestCase):
    
    def test_init(self):
        exc = errors.AuthBaseException("test")
        self.assertEqual(exc.value, "test")
    
    def test_to_str(self):
        exc = errors.AuthBaseException(123)
        self.assertEqual(exc.__str__(), "123")

class ExceptionsExistTestCase(unittest.TestCase):
    
    def test_AuthBadBackend(self):
        exc = errors.AuthBadBackend("test")
        self.assertEqual(exc.value, "test")
    
    def test_AuthNoBackend(self):
        exc = errors.AuthNoBackend("test")
        self.assertEqual(exc.value, "test")
    
    def test_InvalidAuthentication(self):
        exc = errors.InvalidAuthentication("test")
        self.assertEqual(exc.value, "test")
    
    def test_NotAuthorized(self):
        exc = errors.NotAuthorized("test")
        self.assertEqual(exc.value, "test")
    
    def test_BackendWarmingUp(self):
        exc = errors.BackendWarmingUp("test")
        self.assertEqual(exc.value, "test")