# -*- coding: utf-8-*-
# ###################################################################
# FILENAME: ./${api}/__init__.py
# PROJECT: 
# DESCRIPTION: ${api} API
#
#
# ###################################################################

from shiji import urldispatch
%for entry in version_map:
import ${entry[2]}
%endfor

# api_name, api_versions and version_router are required to be
# present for APIRouter to accept this module.

api_name = "${api}"
api_versions = {
                %for entry in version_map:
                "${entry[0]}" : (r"${entry[1]}", ${entry[2]}),
                %endfor
                }
version_router = urldispatch.VersionRouter(api_versions)
