####################################################################
# FILENAME: __init__.py
# PROJECT: Shiji API
# DESCRIPTION: Implements Shiji web API framework.
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

from twisted.web import server

# Shiji Framework Version
__version__ = "0.5.4.2"


# Default Server Identifying Info
server_ident = { "server_name" : "Shiji",
                 "server_version" : "" }

def change_server_ident(name, version=None):
    """
    Changes the 'Server' HTTP header globally.
    
    Arguments:
        name (string) - Name of the server app.
        version (string) (optional) - Version of the server app.
    """
    global server_ident
    
    server_ident["server_name"] = name
    
    if version != None and len(version) > 0:
        server_ident["server_version"] = str(version)
        version_text = "/%s" % server_ident["server_version"]
    else:
        version_text = ""
    
    server.version = server_ident["server_name"] + version_text

change_server_ident(server_ident["server_name"], server_ident["server_version"])