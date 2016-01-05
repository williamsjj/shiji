# ###################################################################
# FILENAME: ./mylogin_api/v1_0/errors.py
# PROJECT:
# DESCRIPTION: mylogin_api API Errors - v1.0
#
#
# ###################################################################

from shiji.webapi import APIError

class SampleNormalError(APIError):
    error_code = 100
    exception_class = "SampleNormalError"
    exception_text = "A sample normal error that doesn't take arguments except for 'request'."

class SampleAdvancedError(APIError):
    error_code = 101
    exception_class = "SampleAdvancedError"
    exception_text = "A sample error that takes arguments in addition to 'request'. Extra Arg Value: %s"
    
    def __init__(self, request_object, extra_arg):
        self.exception_text = self.exception_text % extra_arg
        APIError.__init__(self, request_object)