# ###################################################################
# FILENAME: ./mylogin_api/v1_0/__init__.py
# PROJECT: 
# DESCRIPTION: mylogin_api API - v1.0
#
# ###################################################################


from shiji import urldispatch
import calls

# call_router is required to be present for VersionRouter to accept
# this module

call_router = urldispatch.CallRouter(calls, auto_list_versions=True)