####################################################################
# FILENAME: auth/test_base_backend.py
# PROJECT: Shiji API
# DESCRIPTION: Tests auth.base_backend module.
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

class DummyBackend(base_backend.AuthBackend):
    def __init__(self):
        pass

class BaseAuthBackendTestCase(unittest.TestCase):
    
    def test_init(self):
        self.assertRaises(errors.AuthNoBackend, base_backend.AuthBackend)
    
    def test_perm_list(self):
        x = DummyBackend()
        self.assertRaises(errors.AuthNoBackend, x.perm_list)
    
    def test_authenticate(self):
        x = DummyBackend()
        d = x.authenticate("not a request")
        self.assertFailure(d,
                           errors.AuthNoBackend,
                           "No authentication backend configured.")
        return d