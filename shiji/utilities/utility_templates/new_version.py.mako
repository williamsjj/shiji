# -*- coding: utf-8-*-
# ###################################################################
# FILENAME: ./${api}/${version_module}/__init__.py
# PROJECT: 
# DESCRIPTION: ${api} API - v${version}
#
# ###################################################################


from shiji import urldispatch
import calls

# call_router is required to be present for VersionRouter to accept
# this module

call_router = urldispatch.CallRouter(calls, auto_list_versions=True)