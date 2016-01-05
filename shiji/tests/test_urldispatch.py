####################################################################
# FILENAME: test_urldispatch.py
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
from twisted.internet import defer, address
from twisted.web.server import NOT_DONE_YET
from twisted.python.failure import Failure
from twisted.web.test.test_web import DummyChannel
import json, types
from shiji import urldispatch, webapi, foundation
from shiji.testutil import DummyRequest, DummyRequestNew
from shiji import dummy_api
from shiji.dummy_api.v1_0 import calls, calls_list, calls_unicode
from shiji.dummy_api import v1_0

class ShijiRequestTestCase(unittest.TestCase):
    
    def setUp(self):
         self.request = foundation.ShijiRequest(DummyChannel(), None)
         self.request.site = foundation.ShijiSite(None)
         self.request.client = address.IPv4Address('TCP', "1.2.3.4", 40323)
    
    def test_get_client_ip_dishonor_xrealip(self):
        self.request.site.honor_xrealip = False
        self.request.requestHeaders.addRawHeader("X-Real-IP", "5.6.7.8")
        self.assertEqual(self.request.getClientIP(), "1.2.3.4")
    
    def test_get_client_ip_honor_xrealip_xrealip_present(self):
        self.request.requestHeaders.addRawHeader("X-Real-IP", "5.6.7.8")
        self.assertEqual(self.request.getClientIP(), "5.6.7.8")
    
    def test_get_client_ip_honor_xrealip_xrealip_override_present(self):
        self.request.site.honor_xrealip = True
        self.request.requestHeaders.addRawHeader("X-Real-IP", "5.6.7.8")
        self.assertEqual(self.request.getClientIP(honor_xrealip=False), "1.2.3.4")
    
    def test_get_client_ip_honor_xrealip_xrealip_present_dishonor(self):
        self.request.site.honor_xrealip = False
        self.request.requestHeaders.addRawHeader("X-Real-IP", "5.6.7.8")
        self.assertEqual(self.request.getClientIP(honor_xrealip=True), "5.6.7.8")
    
    def test_get_client_ip_honor_xrealip_xrealip_missing(self):
        self.assertEqual(self.request.getClientIP(), "1.2.3.4")

class URLMatchJSONResourceTestCase(unittest.TestCase):
    
    def setUp(self):
        self.request = DummyRequest(api_mode="", api_version="", api_name="")
        self.route_map = [("^/test/me/(?P<group1>.+)", object())]
    
    def test_init_resource(self):
        "Verify URLMatchJSONResource is correctly initialized."
        phony_call_router = object()
        res = urldispatch.URLMatchJSONResource(self.request,
                                               url_matches=self.route_map,
                                               call_router=phony_call_router)
        self.assertEquals(self.route_map,
                          res.url_matches)
        self.assertEquals(phony_call_router,
                          res.call_router)
    
    def test_render_no_deferred(self):
        "Render function w/ non-deferred return."
        
        def render_GET(request):
            return "test123"
        
        phony_call_router = object()
        res = urldispatch.URLMatchJSONResource(self.request,
                                               url_matches=self.route_map,
                                               call_router=phony_call_router)
        res.render_GET = render_GET
        ret_res = res.render(self.request)
        self.assertEqual("test123", ret_res)
    
    def test_render_no_deferred_failed(self):
        "Render function w/ failed non-deferred return."
        
        def render_GET(request):
            raise Exception("Unexpected catastrophe!")
            return "test123"
        
        phony_call_router = object()
        res = urldispatch.URLMatchJSONResource(self.request,
                                               url_matches=self.route_map,
                                               call_router=phony_call_router)
        res.render_GET = render_GET
        ret_res = res.render(self.request)
        
        actual_response = json.loads(ret_res)
        self.assertEqual(actual_response["error"]["exception_class"], "UnexpectedServerError")
        self.assertEqual(actual_response["error"]["error_code"], 505)
        self.assertTrue("Unexpected catastrophe!" in actual_response["error"]["exception_text"])
    
    def test_render_cors(self):
        "Render function w/ non-deferred return & Access-Request-Allow-Origin header."
        
        def render_GET(request):
            return "test123"
        
        phony_call_router = object()
        self.request.method = "GET"
        res = urldispatch.URLMatchJSONResource(self.request,
                                               url_matches=self.route_map,
                                               call_router=phony_call_router)
        res.render_GET = render_GET
        ret_res = res.render(self.request)
        self.assertEqual("test123", ret_res)
    
    def test_render_nonnull_deferred_success(self):
        "Non-null render function w/ successful deferred return."
        d = defer.Deferred()
        
        def render_GET(request):
            return d
        
        phony_api_router = type('obj', (object,), {'cross_origin_domains' : '*', 'inhibit_http_caching' : True})
        phony_version_router = type('obj', (object,), {'api_router' : phony_api_router})
        phony_call_router = type('obj', (object,), {'version_router' : phony_version_router})
        
        res = urldispatch.URLMatchJSONResource(self.request,
                                               url_matches=self.route_map,
                                               call_router=phony_call_router)
        res.render_GET = render_GET
        ret_res = res.render(self.request)
        self.assertEqual(NOT_DONE_YET, ret_res)
        d.callback("heya")
        self.assertEqual("*", self.request.getHeader("Access-Control-Allow-Origin"))
        self.assertEquals("true", self.request.getHeader("Access-Control-Allow-Credentials"))
        self.assertEquals("no-cache", self.request.getHeader("Cache-Control"))
        self.assertEquals("no-cache", self.request.getHeader("Pragma"))
        self.assertEqual("heya",
                         self.request.content.getvalue())
    
    def test_render_null_deferred_success(self):
        "Null render function w/ successful deferred return."
        d = defer.Deferred()
        
        def render_GET(request):
            return d
        
        phony_call_router = object()
        res = urldispatch.URLMatchJSONResource(self.request,
                                               url_matches=self.route_map,
                                               call_router=phony_call_router)
        res.render_GET = render_GET
        ret_res = res.render(self.request)
        self.assertEqual(NOT_DONE_YET, ret_res)
        d.callback(None)
        self.assertEqual("",
                         self.request.content.getvalue())
    
    def test_render_deferred_failure(self):
        "Render function w/ failed deferred return."
        d = defer.Deferred()
        
        def render_GET(request):
            return d
        
        phony_call_router = object()
        self.request.method = "GET"
        res = urldispatch.URLMatchJSONResource(self.request,
                                               url_matches=self.route_map,
                                               call_router=phony_call_router)
        res.render_GET = render_GET
        ret_res = res.render(self.request)
        self.assertEqual(NOT_DONE_YET, ret_res)
        fail = Failure(Exception("test error"))
        d.errback(fail=fail)
        self.assertEqual(str(webapi.UnexpectedServerError(self.request,
                                                          fail.getErrorMessage())),
                         self.request.content.getvalue())

class ListVersionsTestCase(unittest.TestCase):
    
    def setUp(self):
        self.request = DummyRequest(api_mode="", api_version="1.0", api_name="")
        self.route_map = [("^/test/me/(?P<group1>.+)", object())]
    
    def test_list_versions_get(self):
        "Test list versions."
        
        def versions_list():
            return {"1.0" : (r"1.0", object()),
                    "0.9" : (r"0.9", object())}
        
        version_router = urldispatch.VersionRouter(versions_list())
        call_router = urldispatch.CallRouter(calls, version_router)
        res = urldispatch.ListVersionsCall(self.request,
                                           url_matches=self.route_map,
                                           call_router=call_router)
        
        res.render_GET(self.request)
        exp_res = json.dumps({"all_versions" : sorted(versions_list()),
                              "curr_version" : self.request.api_version })
        self.assertEqual(res.routes, "list_versions")
        self.assertEqual(exp_res,
                         self.request.content.getvalue())

class CallRouterTestCase(unittest.TestCase):
    
    def setUp(self):        
        self.request = DummyRequest(api_mode="", api_version="1.0", api_name="")
        self.route_map = [("^/test/me/(?P<group1>.+)$", calls.PingCall)]
        self.api_router = urldispatch.APIRouter(self.route_map)
        self.version_router = urldispatch.VersionRouter({"1.0" : (r"1.0", object()),
                                                         "0.9" : (r"0.9", object())},
                                                         self.api_router)
    
    def test_call_router_init_no_list_versions(self):
        "Validate call router initialization w/o version listing resource."
        call_router = urldispatch.CallRouter(calls, self.version_router)
        self.assertEqual(call_router.version_router, self.version_router)
        for route in call_router.route_map:
            self.assertEqual(route[0].pattern, route[1].routes + "$")
    
    def test_call_router_init_list_versions(self):
        "Validate call router initialization w/ version listing resource."
        call_router = urldispatch.CallRouter(calls, self.version_router, True)
        self.assertEqual(call_router.version_router, self.version_router)
        found_list_versions = False
        for route in call_router.route_map:
            self.assertEqual(route[0].pattern, route[1].routes + "$")
            if route[0].pattern == "list_versions$" and \
               route[1].__name__ == "ListVersionsCall":
               found_list_versions = True
        self.assertEqual(found_list_versions, True)
    
    def test_create_route_map_from_string(self):
        "Validate building route map from single route string."
        call_router = urldispatch.CallRouter(calls, self.version_router)
        self.assertEqual(len(call_router.route_map), 1)
        route = call_router.route_map[0]
        self.assertEqual(route[0].pattern, "ping$")
        self.assertEqual(route[1].__name__, "PingCall")
    
    def test_create_route_map_from_unicode(self):
        "Validate building route map from single route unicode string."
        call_router = urldispatch.CallRouter(calls_unicode, self.version_router)
        self.assertEqual(len(call_router.route_map), 1)
        route = call_router.route_map[0]
        self.assertEqual(route[0].pattern, "ping$")
        self.assertEqual(route[1].__name__, "PingCall")
    
    def test_create_route_map_from_list(self):
        "Validate building route map from list of route strings."
        call_router = urldispatch.CallRouter(calls_list, self.version_router)
        self.assertEqual(len(call_router.route_map), 2)
        ping_route_found = False
        me_route_found = False
        for route in call_router.route_map:
            if route[0].pattern == "ping(?P<group1>.*)$" and \
               route[1].__name__ == "PingCall":
               ping_route_found = True
            if route[0].pattern == "me$" and \
               route[1].__name__ == "PingCall":
               me_route_found = True
        self.assertEqual(ping_route_found, True)
        self.assertEqual(me_route_found, True)
    
    def test_get_child_malformed_version(self):
        "Validate retrieving resource with a malformed version header."
        call_router = urldispatch.CallRouter(calls_list, self.version_router)
        self.request.setHeader("X-DigiTar-API-Version", "bobbledygook")
        res = call_router.getChild("noname", self.request)
        self.assertTrue(isinstance(res, urldispatch.UnknownVersion))
    
    def test_get_child_unknown_api_mode(self):
        "Validate retrieving resource with an unknown API mode."
        call_router = urldispatch.CallRouter(calls_list, self.version_router)
        self.request.setHeader("X-DigiTar-API-Version", "test-1.0+badmode")
        res = call_router.getChild("noname", self.request)
        self.assertTrue(isinstance(res, urldispatch.UnknownVersion))
    
    def test_get_child_no_route_match(self):
        "Validate retrieving non-existent resource."
        call_router = urldispatch.CallRouter(calls_list, self.version_router)
        self.request.setHeader("X-DigiTar-API-Version", "test-1.0+prod")
        self.request.uri = "/myroute"
        res = call_router.getChild("noname", self.request)
        self.assertTrue(isinstance(res, urldispatch.UnknownCall))
    
    def test_get_child_route_match(self):
        "Validate retrieving valid resource."
        call_router = urldispatch.CallRouter(calls_list, self.version_router)
        self.request.setHeader("X-DigiTar-API-Version", "test-1.0+prod")
        self.request.uri = "/level1/ping%26io"
        res = call_router.getChild("noname", self.request)
        self.assertTrue(isinstance(res, calls_list.PingCall))
        self.assertTrue(res.url_matches.has_key("group1"))
        self.assertEqual(res.url_matches["group1"], "&io")
    
    def test_get_child_route_match_url_arguments(self):
        "Validate that URL arguments do not interfere with matching a valid resource."
        call_router = urldispatch.CallRouter(calls_list, self.version_router)
        self.request.setHeader("X-DigiTar-API-Version", "test-1.0+prod")
        self.request.uri = "/level1/ping%26io?arg1=ignored"
        res = call_router.getChild("noname", self.request)
        self.assertTrue(isinstance(res, calls_list.PingCall))
        self.assertTrue(res.url_matches.has_key("group1"))
        self.assertEqual(res.url_matches["group1"], "&io")

class VersionRouterTestCase(unittest.TestCase):
    
    def setUp(self):
        self.request = DummyRequest(api_mode="", api_version="1.0", api_name="")
        self.route_map = [("^/test/me/(?P<group1>.+)", calls.PingCall)]
        self.api_router = urldispatch.APIRouter(self.route_map)
        self.version_map = {"1.0" : (r"1.0", v1_0)}
        self.version_router = urldispatch.VersionRouter(self.version_map,
                                                        self.api_router)
    
    def test_router_init(self):
        "Validate version router initialization."
        self.assertEqual(self.api_router, self.version_router.api_router)
        for key in self.version_map.keys():
            self.assertTrue(self.version_router.version_map.has_key(key))
            self.assertEqual(self.version_router.version_map[key][0].pattern,
                             self.version_map[key][0] + r"$")
    
    def test_get_child_malformed_version(self):
        "Validate retrieving resource with malformed version header."
        self.request.setHeader("X-DigiTar-API-Version", "bobbledygook")
        res = self.version_router.getChild("noname", self.request)
        self.assertTrue(isinstance(res, urldispatch.UnknownVersion))
    
    def test_get_child_no_version_match(self):
        "Validate retrieving resource with invalid version."
        self.request.setHeader("X-DigiTar-API-Version", "testapi-2.0+prod")
        res = self.version_router.getChild("noname", self.request)
        self.assertTrue(isinstance(res, urldispatch.UnknownVersion))
    
    def test_get_child_version_match(self):
        "Validate retrieving valid resource."
        self.request.setHeader("X-DigiTar-API-Version", "testapi-1.0+prod")
        self.request.uri = "/level1/ping"
        res = self.version_router.getChild("noname", self.request)
        self.assertTrue(isinstance(res, calls.PingCall))
    
    def test_get_version_map(self):
        "Validate correct version map is returned."
        self.assertEqual(self.version_router.version_map,
                         self.version_router.get_version_map())

class UtilityFunctionsTestCase(unittest.TestCase):
    
    def setUp(self):
        self.request = DummyRequest(api_mode="", api_version="", api_name="")
    
    def test_get_version_no_header_no_queryarg(self):
        "Version extraction - no version supplied"
        result = urldispatch.get_version(self.request)
        self.assertEquals(result["api"], "")
        self.assertEquals(result["version"], "")
        self.assertEquals(result["mode"], "")
        
    
    def test_get_version_in_query_arg(self):
        "Version extraction - version in query string"
        self.request.args["X-DigiTar-API-Version"] = ["dummy_api-1.0+prod"]
        result = urldispatch.get_version(self.request)
        self.assertEquals(result["api"], "dummy_api")
        self.assertEquals(result["version"], "1.0")
        self.assertEquals(result["mode"], "prod")
    
    def test_get_version_in_header(self):
        "Version extraction - version in header"
        self.request.setHeader("X-DigiTar-API-Version", "dummy_api-1.0+prod")
        result = urldispatch.get_version(self.request)
        self.assertEquals(result["api"], "dummy_api")
        self.assertEquals(result["version"], "1.0")
        self.assertEquals(result["mode"], "prod")
    
    def test_get_version_bad_version(self):
        "Version extraction - malformed version"
        self.request.setHeader("X-DigiTar-API-Version", "badmojo")
        self.assertRaises(IndexError, urldispatch.get_version, self.request)
    
    def tearDown(self):
        del(self.request)

class UnknownAPITestCase(unittest.TestCase):
    
    def test_get(self):
        "Test unknown API name return error code & message via GET"
        request = DummyRequest(api_mode="", api_version="", api_name="")
        request.setHeader("X-DigiTar-API-Version", "dummyapi")
        request.uri = "dummy.com/dummyapi"
        resource = urldispatch.UnknownAPI()
        body = resource.render_GET(request)
        self.assertEquals(request.response_code, 404)
        self.assertEquals(request.getHeader("Content-Type"),
                          "application/json; charset=utf-8")
        self.assertEquals(body, str(webapi.UnknownAPIError(request,
                                                           "dummyapi")))
    
    def test_post(self):
        "Test unknown API name return error code & message via POST"
        request = DummyRequest(api_mode="", api_version="", api_name="")
        request.setHeader("X-DigiTar-API-Version", "dummyapi")
        request.uri = "dummy.com/dummyapi"
        resource = urldispatch.UnknownAPI()
        body = resource.render_POST(request)
        self.assertEquals(request.response_code, 404)
        self.assertEquals(request.getHeader("Content-Type"),
                          "application/json; charset=utf-8")
        self.assertEquals(body, str(webapi.UnknownAPIError(request,
                                                           "dummyapi")))

class UnknownCallTestCase(unittest.TestCase):
    
    def test_get(self):
        "Test unknown API call return error code & message via GET"
        request = DummyRequest(api_mode="", api_version="", api_name="")
        request.setHeader("X-DigiTar-API-Version", "dummyapi")
        request.uri = "dummy.com/dummyapi/call"
        resource = urldispatch.UnknownCall()
        body = resource.render_GET(request)
        self.assertEquals(request.response_code, 404)
        self.assertEquals(request.getHeader("Content-Type"),
                          "application/json; charset=utf-8")
        self.assertEquals(body, str(webapi.UnknownAPICallError(request,
                                                               "call")))
    
    def test_post(self):
        "Test unknown API call return error code & message via POST"
        request = DummyRequest(api_mode="", api_version="", api_name="")
        request.setHeader("X-DigiTar-API-Version", "dummyapi")
        request.uri = "dummy.com/dummyapi/call"
        resource = urldispatch.UnknownCall()
        body = resource.render_POST(request)
        self.assertEquals(request.response_code, 404)
        self.assertEquals(request.getHeader("Content-Type"),
                          "application/json; charset=utf-8")
        self.assertEquals(body, str(webapi.UnknownAPICallError(request,
                                                               "call")))

class CORSInterrogationTestCase(unittest.TestCase):
    
    def test_options_request_with_acrh(self):
        "Test a OPTIONS request w/ supplied Access-Control-Request-Headers header."
        route_map = [(r"^/example/", dummy_api)]
        api_config = {"arg1" : True, "arg2" : 42}
        router = urldispatch.APIRouter(route_map, config=api_config, cross_origin_domains="*")
        request = DummyRequest(api_mode="", api_version="", api_name="")
        request.setHeader("Access-Control-Request-Headers", "Content-Type")
        resource = urldispatch.CORSInterrogation(request, api_router=router)
        body = resource.render_OPTIONS(request)
        self.assertEquals(request.response_code, 200)
        self.assertEquals(request.getHeader("Content-Type"),
                          "application/json; charset=utf-8")
        self.assertEquals(request.getHeader("Access-Control-Allow-Origin"),
                          "*")
        self.assertEquals(request.getHeader("Access-Control-Allow-Credentials"),
                          "true")
        self.assertEquals(request.getHeader("Access-Control-Allow-Headers"),
                          "Content-Type")
        self.assertEquals(request.getHeader("Access-Control-Allow-Methods"),
                          "PUT,GET,DELETE,POST,HEAD,TRACE,CONNECT,PROPFIND,PROPPATCH,MKCOL,COPY,MOVE,LOCK,UNLOCK")
        self.assertEquals(body, "")
    
    def test_options_request_no_acrh(self):
        "Test an OPTIONS request w/ no supplied Access-Control-Request-Headers header."
        route_map = [(r"^/example/", dummy_api)]
        api_config = {"arg1" : True, "arg2" : 42}
        router = urldispatch.APIRouter(route_map, config=api_config, cross_origin_domains="*")
        request = DummyRequest(api_mode="", api_version="", api_name="")
        resource = urldispatch.CORSInterrogation(request, api_router=router)
        body = resource.render_OPTIONS(request)
        self.assertEquals(request.response_code, 200)
        self.assertEquals(request.getHeader("Content-Type"),
                          "application/json; charset=utf-8")
        self.assertEquals(request.getHeader("Access-Control-Allow-Origin"),
                          "*")
        self.assertEquals(request.getHeader("Access-Control-Allow-Credentials"),
                          "true")
        self.assertEquals(request.getHeader("Access-Control-Allow-Headers"),
                          "Access-Control-Allow-Origin,Content-Type")
        self.assertEquals(request.getHeader("Access-Control-Allow-Methods"),
                          "PUT,GET,DELETE,POST,HEAD,TRACE,CONNECT,PROPFIND,PROPPATCH,MKCOL,COPY,MOVE,LOCK,UNLOCK")
        self.assertEquals(body, "")

class UnknownVersionTestCase(unittest.TestCase):
    
    def test_get_bad_header(self):
        "Test unknown version return error code & message via GET"
        request = DummyRequest(api_mode="", api_version="", api_name="")
        request.setHeader("X-DigiTar-API-Version", "dummyapi")
        resource = urldispatch.UnknownVersion()
        body = resource.render_GET(request)
        self.assertEquals(request.response_code, 406)
        self.assertEquals(request.getHeader("Content-Type"),
                          "application/json; charset=utf-8")
        self.assertEquals(body, str(webapi.UnknownAPIVersionError(request,
                                                                  "dummyapi")))
    def test_get_no_header(self):
        request = DummyRequest(api_mode="", api_version="", api_name="")
        resource = urldispatch.UnknownVersion()
        body = resource.render_GET(request)
        self.assertEquals(request.response_code, 406)
        self.assertEquals(request.getHeader("Content-Type"),
                          "application/json; charset=utf-8")
        self.assertEquals(body, str(webapi.UnknownAPIVersionError(request,
                                                                  "")))
    
    def test_post(self):
        "Test unknown version return error code & message via POST"
        request = DummyRequest(api_mode="", api_version="", api_name="")
        resource = urldispatch.UnknownVersion()
        body = resource.render_POST(request)
        self.assertEquals(request.response_code, 406)
        self.assertEquals(request.getHeader("Content-Type"),
                          "application/json; charset=utf-8")
        self.assertEquals(body, str(webapi.UnknownAPIVersionError(request,
                                                                  "")))

class APIRouterTestCase(unittest.TestCase):
    
    def test_build_route_map_regex(self):
        "Test initializing the route map  - regex"
        route_map = [(r"^/example/", dummy_api)]
        router = urldispatch.APIRouter(route_map)
        self.assertTrue(router.route_map[0][0].match("/example/"))
    
    def test_build_route_map_api_module(self):
        "Test initializing the route map - API module"
        route_map = [(r"^/example/", dummy_api)]
        router = urldispatch.APIRouter(route_map)
        self.assertTrue(isinstance(router.route_map[0][1], types.ModuleType))
        
    def test_config_import(self):
        "Test API config dictionary import"
        route_map = [(r"^/example/", dummy_api)]
        api_config = {"arg1" : True, "arg2" : 42}
        router = urldispatch.APIRouter(route_map, config=api_config)
        self.assertTrue(router.config["arg1"] == True)
        self.assertTrue(router.config["arg2"] == 42)
    
    def test_get_options(self):
        "Test OPTIONS request."
        route_map = [(r"^/example/", dummy_api)]
        api_config = {"arg1" : True, "arg2" : 42}
        request = DummyRequest(api_mode="prod", api_version="1.0", api_name="dummy_api")
        request.method = "OPTIONS"
        request.setHeader("Access-Control-Request-Headers", "Content-Type")
        router = urldispatch.APIRouter(route_map, config=api_config, cross_origin_domains="*")
        resource = router.getChild("/example/", request)
        self.assertTrue(isinstance(resource, urldispatch.CORSInterrogation))
        resource.render_OPTIONS(request)
        self.assertEquals(request.getHeader("Content-Type"),
                          "application/json; charset=utf-8")
        self.assertEquals(request.getHeader("Access-Control-Allow-Origin"),
                          "*")
        self.assertEquals(request.getHeader("Access-Control-Allow-Credentials"),
                          "true")
        self.assertEquals(request.getHeader("Access-Control-Allow-Headers"),
                          "Content-Type")
        self.assertEquals(request.getHeader("Access-Control-Allow-Methods"),
                          "PUT,GET,DELETE,POST,HEAD,TRACE,CONNECT,PROPFIND,PROPPATCH,MKCOL,COPY,MOVE,LOCK,UNLOCK")
    
    def test_get_child_route_match_api_match(self):
        "Test route match with good API name match in version header"
        route_map = [(r"^/example/", dummy_api)]
        api_config = {"arg1" : True, "arg2" : 42}
        request = DummyRequest(api_mode="prod", api_version="1.0", api_name="dummy_api")
        request.setHeader("X-DigiTar-API-Version", "dummy_api-1.0+prod")
        router = urldispatch.APIRouter(route_map, config=api_config)
        resource = router.getChild("/example/", request)
        self.assertTrue(isinstance(resource, urldispatch.VersionRouter))
        self.assertEquals(resource.api_router, router)
    
    def test_get_child_route_no_api_match(self):
        "Test route match with no API name match in version header"
        request = DummyRequest(api_mode="", api_version="", api_name="")
        request.setHeader("X-DigiTar-API-Version", "badmojoapi-1.0+prod")
        route_map = [(r"^/example/", dummy_api)]
        router = urldispatch.APIRouter(route_map)
        resource = router.getChild("/example/", request)
        self.assertTrue(isinstance(resource, urldispatch.UnknownVersion))
    
    def test_get_child_no_route_match(self):
        "Test no route match"
        route_map = [(r"^/example/", dummy_api)]
        api_config = {"arg1" : True, "arg2" : 42}
        request = DummyRequest(api_mode="prod", api_version="1.0", api_name="dummy_api")
        request.setHeader("X-DigiTar-API-Version", "dummy_api-1.0+prod")
        router = urldispatch.APIRouter(route_map, config=api_config)
        resource = router.getChild("/badmojo/", request)
        self.assertTrue(isinstance(resource, urldispatch.UnknownAPI))
    
    def test_get_child_version_unknown(self):
        "Test version extraction with bad header"
        request = DummyRequest(api_mode="", api_version="", api_name="")
        request.setHeader("X-DigiTar-API-Version", "dummyapi")
        route_map = [(r"^/example/", dummy_api)]
        router = urldispatch.APIRouter(route_map)
        resource = router.getChild("/example/", request)
        self.assertTrue(isinstance(resource, urldispatch.UnknownVersion))
    
    def test_get_route_map(self):
        route_map = [(r"^/example/", dummy_api)]
        router = urldispatch.APIRouter(route_map)
        self.assertEqual(router.route_map, router.get_route_map())

# URLRouter class is deprecated...tests retained for 
# completeness
class URLRouterTestCase(unittest.TestCase):
    
    def setUp(self):
        self.route_map = [(r"^/example/", calls.PingCall)]
        self.url_router = urldispatch.URLRouter(self.route_map)
    
    def test_init_url_router(self):
        self.assertEqual(self.url_router.route_map, self.route_map)
    
    def test_no_match(self):
        request = DummyRequest(api_mode="", api_version="", api_name="")
        request.uri = "/notexample/"
        res = self.url_router.getChild("noname", request)
        self.assertTrue(isinstance(res, urldispatch.UnknownAPI))
    
    def test_match(self):
        request = DummyRequest(api_mode="", api_version="", api_name="")
        request.uri = "/example/"
        res = self.url_router.getChild("noname", request)
        self.assertTrue(isinstance(res, calls.PingCall))