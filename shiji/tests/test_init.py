####################################################################
# FILENAME: test_init.py
# PROJECT: Shiji API
# DESCRIPTION: Tests __init__ module.
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
from twisted.web import server
import shiji

class ChangeServerIdentTestCase(unittest.TestCase):
    
    def test_change_ident(self):
        new_name = "Bongo"
        new_version = "1.91"
        
        shiji.change_server_ident(new_name, new_version)
        self.assertEqual(shiji.server_ident["server_name"], new_name)
        self.assertEqual(shiji.server_ident["server_version"], new_version)
        self.assertEqual(server.version, "Bongo/1.91")