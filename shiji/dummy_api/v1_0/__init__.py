# -*- coding: utf-8-*-
####################################################################
# FILENAME: ./dummy_api/v1_0/__init__.py
# PROJECT: Shiji API
# DESCRIPTION: Dummy API v1.0
#
#
# $Id$
####################################################################
# (C)2015 DigiTar Inc.
# Licensed under the MIT License.
####################################################################


from shiji import urldispatch
import calls

# call_router is required to be present for VersionRouter to accept
# this module

call_router = urldispatch.CallRouter(calls, auto_list_versions=True)