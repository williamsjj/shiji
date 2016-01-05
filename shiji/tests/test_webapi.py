####################################################################
# FILENAME: test_webapi.py
# PROJECT: Shiji API
# DESCRIPTION: Tests webapi module.
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
import json
from shiji import webapi
from shiji.testutil import DummyRequest

## Tests

class JSONArgumentsTestCase(unittest.TestCase):
    
    def dummy_render_func(self, request):
        "Dummy render function"
        return "okey dokey"
    
    @webapi.json_arguments([("arg1", unicode)])
    def dummy_render_func2(self, request):
        "Dummy render function"
        return "okey dokey"
    
    def test_no_arg_list(self):
        "No list of arguments to validated passed in."
        self.assertRaises(Exception,
                          webapi.json_arguments,
                          webapi.json_arguments)
    
    def test_arg_not_list(self):
        "Argument is not a list."
        self.assertRaises(Exception,
                          webapi.json_arguments,
                          "hiya")
    
    def test_arg_list_not_tuples(self):
        "Argument list does not contain all tuples."
        self.assertRaises(Exception,
                          webapi.json_arguments,
                          ["yo"])
    
    def test_arg_list_tuples_no_type(self):
        "Argument list contains tuples with name and no validation type."
        self.assertRaises(Exception,
                          webapi.json_arguments,
                          [()])
                          
    def test_arg_list_tuples_too_many_elements(self):
        "Argument list contains tuples with more elements than name, validation type and optional_flag."
        self.assertRaises(Exception,
                          webapi.json_arguments,
                          [("arg1", unicode, False, "hi")])
    
    
    def test_no_content_type_set(self):
        "Request does not have a Content-Type set"
        test_request = DummyRequest()
        
        outer_wrap = webapi.json_arguments([("arg1", unicode)])
        inner_wrap = outer_wrap(self.dummy_render_func)
        self.assertEqual(str(webapi.ContentTypeError(test_request)),
                         inner_wrap(self, test_request))
    
    def test_content_type_no_charset(self):
        "Request Content-Type does not have a character set specified"
        test_request = DummyRequest()
        test_request.setHeader("Content-Type", "application/json")
        outer_wrap = webapi.json_arguments([("arg1", unicode)])
        inner_wrap = outer_wrap(self.dummy_render_func)
        self.assertEqual(str(webapi.CharsetNotUTF8Error(test_request)),
                         inner_wrap(self, test_request))
    
    def test_content_type_charset_not_utf8(self):
        "Request Content-Type characters set is not UTF-8"
        test_request = DummyRequest()
        test_request.setHeader("Content-Type", "application/json; charset=iso-1022-jp")
        outer_wrap = webapi.json_arguments([("arg1", unicode)])
        inner_wrap = outer_wrap(self.dummy_render_func)
        self.assertEqual(str(webapi.CharsetNotUTF8Error(test_request)),
                         inner_wrap(self, test_request))
    
    def test_content_type_content_type_mismatch(self):
        "Request Content-Type doesn't match expected type."
        test_request = DummyRequest()
        test_request.setHeader("Content-Type", "image/jpeg; charset=utf-8")
        outer_wrap = webapi.json_arguments([("arg1", unicode)],
                                           content_type="application/json")
        inner_wrap = outer_wrap(self.dummy_render_func)
        self.assertEqual(str(webapi.ContentTypeError(test_request)),
                         inner_wrap(self, test_request))
    
    def test_content_invalid_json(self):
        "Request content not valid JSON."
        test_request = DummyRequest()
        test_request.setHeader("Content-Type", "application/json; charset=utf-8")
        test_request.write("boingo! bad json!")
        outer_wrap = webapi.json_arguments([("arg1", unicode)])
        inner_wrap = outer_wrap(self.dummy_render_func)
        self.assertEqual(str(webapi.JSONDecodeError(test_request)),
                         inner_wrap(self, test_request))
    
    def test_content_not_dict(self):
        "Request content contained in a dictionary/hash."
        test_request = DummyRequest()
        test_request.setHeader("Content-Type", "application/json; charset=utf-8")
        test_request.write(json.dumps("not a dict"))
        outer_wrap = webapi.json_arguments([("arg1", unicode)])
        inner_wrap = outer_wrap(self.dummy_render_func)
        self.assertEqual(str(webapi.RequestNotHashError(test_request)),
                         inner_wrap(self, test_request))
    
    def test_content_arg_type_mismatch_required_arg(self):
        "Request JSON required arguments contain data which doesn't match expected type."
        test_request = DummyRequest()
        test_request.setHeader("Content-Type", "application/json; charset=utf-8")
        test_request.write(json.dumps({"arg1" : 1}))
        outer_wrap = webapi.json_arguments([("arg1", unicode)])
        inner_wrap = outer_wrap(self.dummy_render_func)
        self.assertEqual(str(webapi.ValueError(test_request, "arg1", "Must be of type unicode")),
                         inner_wrap(self, test_request))
    
    def test_content_arg_type_mismatch_optional_arg(self):
        "Request JSON optional arguments contain data which doesn't match expected type."
        test_request = DummyRequest()
        test_request.setHeader("Content-Type", "application/json; charset=utf-8")
        test_request.write(json.dumps({"arg1" : 1}))
        outer_wrap = webapi.json_arguments([("arg1", unicode, True)])
        inner_wrap = outer_wrap(self.dummy_render_func)
        self.assertEqual(str(webapi.ValueError(test_request, "arg1", "Must be of type unicode")),
                         inner_wrap(self, test_request))
    
    def test_content_required_arg_missing_no_optional_flag_present(self):
        "Request JSON arguments missing required argument."
        test_request = DummyRequest()
        test_request.setHeader("Content-Type", "application/json; charset=utf-8")
        test_request.write(json.dumps({"arg2" : 1}))
        outer_wrap = webapi.json_arguments([("arg1", unicode)])
        inner_wrap = outer_wrap(self.dummy_render_func)
        self.assertEqual(str(webapi.ValueError(test_request, "arg1", "Argument is missing.")),
                         inner_wrap(self, test_request))
    
    def test_content_required_arg_missing_optional_flag_false(self):
        "Request JSON arguments missing required argument."
        test_request = DummyRequest()
        test_request.setHeader("Content-Type", "application/json; charset=utf-8")
        test_request.write(json.dumps({"arg2" : 1}))
        outer_wrap = webapi.json_arguments([("arg1", unicode, False)])
        inner_wrap = outer_wrap(self.dummy_render_func)
        self.assertEqual(str(webapi.ValueError(test_request, "arg1", "Argument is missing.")),
                         inner_wrap(self, test_request))
    
    def test_json_validate_success(self):
        "Request JSON arguments successfully validated."
        test_request = DummyRequest()
        test_request.setHeader("Content-Type", "application/json; charset=utf-8")
        test_request.write(json.dumps({"arg1" : unicode("hi")}))
        self.dummy_render_func2(test_request)
        self.assertTrue(hasattr(test_request, "jsonArgs"))
        self.assertTrue(test_request.jsonArgs.has_key("arg1"))
        self.assertEqual(test_request.jsonArgs["arg1"], unicode("hi"))

class PagedResultsTestCase(unittest.TestCase):
    
    def dummy_render_func(self, request):
        "Dummy render function"
        return "okey dokey"
    
    @webapi.paged_results(default_page=0,default_page_len=250,max_page_len=500)
    def dummy_render_func2(self, request):
        "Dummy render function"
        return request.args
    
    def test_default_page_lt_zero(self):
        "default_page is less than 0"
        self.assertRaises(Exception,
                          webapi.paged_results,
                          -1,100,100)
    
    def test_default_page_len_lt_zero(self):
        "default_page_len is less than 0"
        self.assertRaises(Exception,
                          webapi.paged_results,
                          0,-1,100)
    
    def test_max_page_len_lt_zero(self):
        "max_page_len is less than 0"
        self.assertRaises(Exception,
                          webapi.paged_results,
                          0,100,-1)
    
    def test_default_page_len_gt_max_page_len(self):
        "default_page_len is greater than max_page_len"
        self.assertRaises(Exception,
                          webapi.paged_results,
                          0,100,10)
    
    def test_no_page_len_uses_default(self):
        "No page_len argument sets page_len to default."
        test_request = DummyRequest()
        test_request.args["arg1"] = ["test"]
        res = self.dummy_render_func2(test_request)
        self.assertEqual(res["page_len"][0], "250")
    
    def test_no_page_uses_default(self):
        "No page argument sets page to default."
        test_request = DummyRequest()
        test_request.args["arg1"] = ["test"]
        res = self.dummy_render_func2(test_request)
        self.assertEqual(res["page"][0], "0")
    
    def test_good_page_len_overrides_default(self):
        "Valid page_len argument overrides page_len from default."
        test_request = DummyRequest()
        test_request.args["arg1"] = ["test"]
        test_request.args["page_len"] = ["50"]
        res = self.dummy_render_func2(test_request)
        self.assertEqual(res["page_len"][0], "50")
    
    def test_good_page_overrides_default(self):
        "Valid page argument overrides page from default."
        test_request = DummyRequest()
        test_request.args["arg1"] = ["test"]
        test_request.args["page"] = ["1"]
        res = self.dummy_render_func2(test_request)
        self.assertEqual(res["page"][0], "1")
    
    def test_good_page_and_page_len_overrides_default(self):
        "Valid page & page_len arguments override page & page_len from defaults."
        test_request = DummyRequest()
        test_request.args["arg1"] = ["test"]
        test_request.args["page"] = ["1"]
        test_request.args["page_len"] = ["50"]
        res = self.dummy_render_func2(test_request)
        self.assertEqual(res["page"][0], "1")
        self.assertEqual(res["page_len"][0], "50")
    
    def test_page_len_invalid_int_fail(self):
        "page_len argument in request is not a valid integer."
        test_request = DummyRequest()
        test_request.args["arg1"] = ["test"]
        test_request.args["page_len"] = ["xyz"]
        res = self.dummy_render_func2(test_request)
        self.assertEqual(res,
                         str(webapi.ValueError(test_request, "page_len", "Argument must be an integer.")))
    
    def test_page_invalid_int_fail(self):
        "page argument in request is not a valid integer."
        test_request = DummyRequest()
        test_request.args["arg1"] = ["test"]
        test_request.args["page"] = ["xyz"]
        res = self.dummy_render_func2(test_request)
        self.assertEqual(res,
                         str(webapi.ValueError(test_request, "page", "Argument must be an integer.")))
    
    def test_page_len_lt_zero_fail(self):
        "page_len argument in request is < 0."
        test_request = DummyRequest()
        test_request.args["arg1"] = ["test"]
        test_request.args["page_len"] = ["-1"]
        res = self.dummy_render_func2(test_request)
        self.assertEqual(res,
                         str(webapi.ValueError(test_request, "page_len", "Argument must be 0 or greater.")))
    
    def test_page_lt_zero_fail(self):
        "page argument in request is < 0."
        test_request = DummyRequest()
        test_request.args["arg1"] = ["test"]
        test_request.args["page"] = ["-1"]
        res = self.dummy_render_func2(test_request)
        self.assertEqual(res,
                         str(webapi.ValueError(test_request, "page", "Argument must be 0 or greater.")))
    
    def test_page_len_gt_max_page_len_fail(self):
        "page_len argument in request is > max_page_len."
        test_request = DummyRequest()
        test_request.args["arg1"] = ["test"]
        test_request.args["page_len"] = ["501"]
        res = self.dummy_render_func2(test_request)
        self.assertEqual(res,
                         str(webapi.ValueError(test_request, "page_len", "Argument must be 500 or less.")))

class URLArgumentsTestCase(unittest.TestCase):
    
    def dummy_render_func(self, request):
        "Dummy render function"
        return "okey dokey"
    
    @webapi.url_arguments(["arg1"])
    def dummy_render_func2(self, request):
        "Dummy render function"
        return "okey dokey"
    
    def test_no_arg_list(self):
        "No list of arguments to validated passed in."
        self.assertRaises(Exception,
                          webapi.url_arguments,
                          webapi.url_arguments)
    
    def test_arg_not_list(self):
        "Argument is not a list."
        self.assertRaises(Exception,
                          webapi.url_arguments,
                          "hiya")
    
    def test_arg_list_not_string(self):
        "Argument list does not contain all strings."
        self.assertRaises(Exception,
                          webapi.url_arguments,
                          [123])
    
    def test_no_content_type_set(self):
        "Request does not have a Content-Type set"
        test_request = DummyRequest()
        
        outer_wrap = webapi.url_arguments(["arg1"], "application/json")
        inner_wrap = outer_wrap(self.dummy_render_func)
        self.assertEqual(str(webapi.ContentTypeError(test_request)),
                         inner_wrap(self, test_request))
    
    def test_request_missing_argument(self):
        "Request does not have a Content-Type set"
        test_request = DummyRequest()
        
        outer_wrap = webapi.url_arguments(["arg1"])
        inner_wrap = outer_wrap(self.dummy_render_func)
        self.assertEqual(str(webapi.ValueError(test_request, "arg1", "Argument is missing.")),
                         inner_wrap(self, test_request))
    
    def test_content_type_no_charset(self):
        "Request Content-Type does not have a character set specified"
        test_request = DummyRequest()
        test_request.setHeader("Content-Type", "application/json")
        outer_wrap = webapi.url_arguments(["arg1"], "application/json")
        inner_wrap = outer_wrap(self.dummy_render_func)
        self.assertEqual(str(webapi.CharsetNotUTF8Error(test_request)),
                         inner_wrap(self, test_request))
    
    def test_content_type_charset_not_utf8(self):
        "Request Content-Type characters set is not UTF-8"
        test_request = DummyRequest()
        test_request.setHeader("Content-Type", "application/json; charset=iso-1022-jp")
        outer_wrap = webapi.url_arguments(["arg1"], "application/json")
        inner_wrap = outer_wrap(self.dummy_render_func)
        self.assertEqual(str(webapi.CharsetNotUTF8Error(test_request)),
                         inner_wrap(self, test_request))
    
    def test_content_type_content_type_mismatch(self):
        "Request Content-Type doesn't match expected type."
        test_request = DummyRequest()
        test_request.setHeader("Content-Type", "image/jpeg; charset=utf-8")
        outer_wrap = webapi.url_arguments(["arg1"],
                                           content_type="application/json")
        inner_wrap = outer_wrap(self.dummy_render_func)
        self.assertEqual(str(webapi.ContentTypeError(test_request)),
                         inner_wrap(self, test_request))
    
    def test_json_validate_success(self):
        "Request URL arguments successfully validated."
        test_request = DummyRequest()
        test_request.setHeader("Content-Type", "application/json; charset=utf-8")
        test_request.args["arg1"] = "test"
        res = self.dummy_render_func2(test_request)
        self.assertEqual(res, "okey dokey")

def auth_test(username, password):
    if username == "user" and password == "pass":
        return True
    else:
        return False

class AuthHTTPBasicTestCase(unittest.TestCase):
    
    def dummy_render_func(self, request):
        "Dummy render function"
        return "okey dokey"
    
    @webapi.auth_http_basic(auth_test)
    def dummy_render_func2(self, request):
        "Dummy render function"
        return "okey dokey"
    
    def test_invalid_credentials(self):
        "Invalid HTTP BasicAuth credentials."
        test_request = DummyRequest(user="baduser", password="badpass")
        outer_wrap = webapi.auth_http_basic(auth_test)
        inner_wrap = outer_wrap(self.dummy_render_func)
        inner_wrap(self, test_request)
        self.assertEqual(test_request.response_code, 401)
        self.assertEqual(test_request.getHeader("WWW-Authenticate"),
                         'Basic realm="Shiji"')
        self.assertEqual(str(webapi.AccessDeniedError(test_request)),
                         test_request.content.getvalue())
    
    def test_valid_credentials(self):
        "Invalid HTTP BasicAuth credentials."
        test_request = DummyRequest(user="user", password="pass")
        self.dummy_render_func2(test_request)
        self.assertEqual(test_request.response_code, 200)

class WriteJSONTestCase(unittest.TestCase):
    
    def test_write_json(self):
        "Validate write_json outputs JSON & sets content length"
    
        test_request = DummyRequest()
        test_obj = {"test_key": "test_value"}
        webapi.write_json(test_request, test_obj)
    
        self.assertEquals(test_request.getAllHeaders()["Content-Length"], len(json.dumps(test_obj)))
        self.assertEquals(test_request.content.getvalue(), json.dumps(test_obj))

class APIErrorsTestCase(unittest.TestCase):
    "Validate APIError"
    
    request = DummyRequest()
    error_code = 409
    exception_class = "RandomError"
    exception_text = "Random error occurred."
    
    ref_err_dict = {"result" : None,
                    "error" : {"error_code" : error_code,
                               "exception_class" : exception_class,
                               "exception_text" : exception_text}}
    
    obj_error = webapi.APIError(request,
                                error_code,
                                exception_class,
                                exception_text)
    
    def test_api_error(self):
        "Test initializing APIError object"
        self.obj_error = webapi.APIError(self.request,
                                         self.error_code,
                                         self.exception_class,
                                         self.exception_text)
        
        self.assertEquals(self.obj_error.error_code , self.error_code)
        self.assertEquals(self.obj_error.exception_class , self.exception_class)
        self.assertEquals(self.obj_error.exception_text , self.exception_text)
    
    def test_bad_error_code(self):
        "Test initializing APIError object"
        self.obj_error = webapi.APIError(self.request,
                                         self.error_code,
                                         self.exception_class,
                                         self.exception_text)
        self.assertRaises(Exception,
                          self.obj_error.__init__,
                          self.request,
                          str("invalid error code"),
                          self.exception_class,
                          self.exception_text)
    
    def test_no_error_code_init(self):
        "Test initializing APIError without an error code."
        
        def err_init():
            webapi.APIError(self.request)
        
        self.assertRaises(ValueError,
                          err_init)
    
    def test_no_exception_class_init(self):
        "Test initializing APIError without an exception class."
        def err_init():
            webapi.APIError(self.request,
                            error_code=100)
        
        self.assertRaises(ValueError,
                          err_init)
    
    def test_no_exception_text_init(self):
        "Test initializing APIError without exception text."
        def err_init():
            webapi.APIError(self.request,
                            error_code=100,
                            exception_class=self.exception_class)
        
        self.assertRaises(ValueError,
                          err_init)
    
    def test_obj_err(self):
        "Validate APIError generates a Shiji error dictionary"
        self.assertEquals(self.obj_error.obj_err() , self.ref_err_dict)
    
    def test_json_err(self):
        "Validate APIError generates JSON'd copy of error dictionary"
        self.assertEquals(self.obj_error.json_err() , json.dumps(self.ref_err_dict))
    
    def test_to_string(self):
        "Validate __str__ returns JSON'd copy of error dictionary"
        self.assertEquals(str(self.obj_error) , json.dumps(self.ref_err_dict))


    def test_unknown_api_error(self):
        "Validate UnknownAPIError"
        request = DummyRequest()
        obj_error = webapi.UnknownAPIError(request, "test_api")
        
        self.assertEquals(obj_error.error_code , 208)
        self.assertEquals(obj_error.exception_class , "UnknownAPIError")
        self.assertEquals(obj_error.exception_text , "The requested API 'test_api' is unknown.")
        self.assertEquals(request.response_code , 404)

    def test_unknown_api_version_error(self):
        "Validate UnknownAPIVersionError"
        request = DummyRequest()
        obj_error = webapi.UnknownAPIVersionError(request, "0.1")
        
        self.assertEquals(obj_error.error_code , 207)
        self.assertEquals(obj_error.exception_class , "UnknownAPIVersionError")
        self.assertEquals(obj_error.exception_text , "API version '0.1' is invalid or specifies an API/version that does not exist.")
        self.assertEquals(request.response_code , 406)

    def test_unknown_api_call_error(self):
        "Validate UnknownAPICallError"
        request = DummyRequest()
        obj_error = webapi.UnknownAPICallError(request, "test_call")
        
        self.assertEquals(obj_error.error_code , 203)
        self.assertEquals(obj_error.exception_class , "UnknownAPICallError")
        self.assertEquals(obj_error.exception_text , "The requested API call 'test_call' is unknown.")
        self.assertEquals(request.response_code , 404)

    def test_json_encode_error(self):
        "Validate JSONEncodeError"
        request = DummyRequest()
        obj_error = webapi.JSONEncodeError(request)
        
        self.assertEquals(obj_error.error_code , 204)
        self.assertEquals(obj_error.exception_class , "JSONEncodeError")
        self.assertEquals(obj_error.exception_text , "An unrecoverable error has occurred JSON-encoding the API call result.")
        self.assertEquals(request.response_code , 409)

    def test_json_decode_error(self):
        "Validate JSONDecodeError"
        request = DummyRequest()
        obj_error = webapi.JSONDecodeError(request)
        
        self.assertEquals(obj_error.error_code , 205)
        self.assertEquals(obj_error.exception_class , "JSONDecodeError")
        self.assertEquals(obj_error.exception_text , "Arguments passed in API call request are not validly formed JSON.")
        self.assertEquals(request.response_code , 409)


    def test_request_not_hash_error(self):
        "Validate RequestNotHashError"
        request = DummyRequest()
        obj_error = webapi.RequestNotHashError(request)
        
        self.assertEquals(obj_error.error_code , 206)
        self.assertEquals(obj_error.exception_class , "RequestNotHashError")
        self.assertEquals(obj_error.exception_text , "Request body must be a JSON-encoded hash table/dictionary.")
        self.assertEquals(request.response_code , 409)

    def test_access_denied_error(self):
        "Validate AccessDeniedError"
        request = DummyRequest()
        obj_error = webapi.AccessDeniedError(request)
        
        self.assertEquals(obj_error.error_code , 501)
        self.assertEquals(obj_error.exception_class , "AccessDeniedError")
        self.assertEquals(obj_error.exception_text , "Insufficient permission to perform the requested action.")
        self.assertEquals(request.response_code , 409)

    def test_value_error(self):
        "Validate ValueError"
        request = DummyRequest()
        obj_error = webapi.ValueError(request, "arg_name", "extra description")
        
        self.assertEquals(obj_error.error_code , 502)
        self.assertEquals(obj_error.exception_class , "ValueError")
        self.assertEquals(obj_error.exception_text , "Invalid value for argument 'arg_name'. extra description")
        self.assertEquals(request.response_code , 409)

    def test_content_type_error(self):
        "Validate ContentTypeError"
        request = DummyRequest()
        obj_error = webapi.ContentTypeError(request)
        
        self.assertEquals(obj_error.error_code , 503)
        self.assertEquals(obj_error.exception_class , "ContentTypeError")
        self.assertEquals(obj_error.exception_text , "The Content-Type of the API request was not of the expected " + \
                                        "format...or the API/version requested does not exist.")
        self.assertEquals(request.response_code , 406)

    def test_charset_not_utf8_error(self):
        "Validate CharsetNOtUTF8Error"
        request = DummyRequest()
        obj_error = webapi.CharsetNotUTF8Error(request)
        
        self.assertEquals(obj_error.error_code , 504)
        self.assertEquals(obj_error.exception_class , "CharsetNotUTF8Error")
        self.assertEquals(obj_error.exception_text , "The Content-Type of the API request did not specify a charset, " \
                                        "or the charset specified was not UTF-8.")
        self.assertEquals(request.response_code , 409)

    def test_unexpected_server_error(self):
        "Validate UnexpectedServerError"
        request = DummyRequest()
        obj_error = webapi.UnexpectedServerError(request, "what error?")
        
        self.assertEquals(obj_error.error_code , 505)
        self.assertEquals(obj_error.exception_class , "UnexpectedServerError")
        self.assertEquals(obj_error.exception_text , "An unexpected error has occurred processing the request. " \
                                        "Error: 'what error?'")
        self.assertEquals(request.response_code , 409)

    def test_invalid_authentication_error(self):
        "Validate CharsetNOtUTF8Error"
        request = DummyRequest()
        obj_error = webapi.InvalidAuthenticationError(request)
        
        self.assertEquals(obj_error.error_code , 506)
        self.assertEquals(obj_error.exception_class , "InvalidAuthenticationError")
        self.assertEquals(obj_error.exception_text , "Authentication information is invalidly formed and/or missing required elements.")
        self.assertEquals(request.response_code , 409)
    
    def test_invalid_secure_cookie_error(self):
        "Validate InvalidSecureCookieError"
        request = DummyRequest()
        obj_error = webapi.InvalidSecureCookieError(request, "mycookie", "mysig")
        
        self.assertEquals(obj_error.error_code , 507)
        self.assertEquals(obj_error.exception_class , "InvalidSecureCookieError")
        self.assertEquals(obj_error.exception_text , "Secure cookie 'mycookie' signature 'mysig' is invalid.")
        self.assertEquals(request.response_code , 409)
    
    def test_expired_secure_cookie_error(self):
        "Validate ExpiredSecureCookieError"
        request = DummyRequest()
        obj_error = webapi.ExpiredSecureCookieError(request, "mycookie")
        
        self.assertEquals(obj_error.error_code , 508)
        self.assertEquals(obj_error.exception_class , "ExpiredSecureCookieError")
        self.assertEquals(obj_error.exception_text , "Secure cookie 'mycookie' is expired.")
        self.assertEquals(request.response_code , 409)




