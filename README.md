# 指示 #
# Shiji - RESTful API Framework #

_Shiji means "commands" in Japanese. It's a JSON-focused, asynchronous framework for building and running RESTful web APIs in Python._

We &hearts; [Twisted](https://twistedmatrix.com).

[![Circle CI](https://circleci.com/gh/williamsjj/shiji.svg?style=svg)](https://circleci.com/gh/williamsjj/shiji)

## Low-down ##

Shiji is designed to make it easier to handle things like API versioning, argument type validation for JSON, and automatically generating API docs (built-in support for [statsd](https://github.com/etsy/statsd) metrics too!).

__shijid__ runs everything. It allows you to build your API and simply add it to shijid.conf and start serving it. Each API you make can also validate and analyze its own configuration data from shijid.conf.

Shiji plays nice with [virtualenv](https://virtualenv.readthedocs.org/en/latest/).

## Getting Started ##

First install ```shiji``` from PyPI:

```pip install shiji```

Next generate the stub files and structure for your first API version:

```shiji_admin -A mylogin_api -V 1.0```

You'll now have a directory structure that looks like this:

```
__init__.py
config.py
v1_0/__init__.py
v1_0/calls.py
v1_0/errors.py
```

### Understanding our first API version... ###
Let's look at \_\_init\_\_.py:

```python
from shiji import urldispatch
import v1_0

# api_name, api_versions and version_router are required to be
# present for APIRouter to accept this module.

api_name = "mylogin_api"
api_versions = {
                "1.0" : (r"1.0", v1_0),
                }
version_router = urldispatch.VersionRouter(api_versions)
```

There's 3 important things going on here. We've...

* ...imported the ```v1_0``` module from our new API so we can install it: ```import v1_0```
* ...given our API its official internal name: ```api_name = "mylogin_api"```
* ...and most importantly we've installed a map entry between our ```v1_0``` module and its internal version ID ```r"1.0"```.

All HTTP API callers are required to pass a special header to indicate what API version they want:

```X-DigiTar-API-Version: mylogin_api-1.0+prod```

The ```1.0``` will be extracted by Shiji's ```VersionRouter``` and matched against the ```r"1.0"``` entry in the ```api_versions``` map. Since the match is exact, the API HTTP request will be automatically dispatched to the imported ```v1_0``` API version module. 

The ```r"1.0"``` literal is actually a regular expression. So you can have incredibly flexible version routing. For example, you could route all 1.x API versions to the ```v1_0``` module:

```python
api_versions = {
                "1.0" : (r"1\..*", v1_0),
                }
```

__NOTE:__ The ```"1.0"``` map key is used for internal purposes only. Only the regular expression literal ```r"<version_string>"``` is used to match a header version to an API version module.

If we want to add another version to our API, we can use ```shiji_admin``` to generate the version stubs:

```shiji_admin -A mylogin_api -V 2.0```

```shiji_admin``` is smart enough to not touch your existing ```v1_0``` module, and just add a reference to the new version in ```api_versions```:

```python
api_versions = {
                "1.0" : (r"1.0", v1_0),
                "2.0" : (r"2.0", v2_0),
                }
```

### Adding our first API call... ###

Take a peek inside ```v1_0/calls.py```...a stub for a very simple API call has already been added for us:

```python
class PingCall (urldispatch.URLMatchJSONResource):
    """
    Echoes back at caller.
    """
    routes = r"ping[^/]*$"
    
    def render_GET(self, request):
        
        if request.api_mode == "prod":
            mode_string = "I'm production baby!"
        elif request.api_mode == "test":
            mode_string = "I'm in testing mode. :("
        else:
            mode_string = "I have no clue what mode I'm in."
        
        response = "PONG! Right back at ya. %s " % mode_string
        response = response + "(API: %s, Version: %s, Mode: %s)" % (request.api_name,
                                                                    request.api_version,
                                                                    request.api_mode)
        webapi.write_json(request, response)
```

All API calls in Shiji are subclasses of ```urldispatch.URLMatchJSONResource```, which has all the magic needed to parse and validate our API request. 

In this case ```PingCall``` is the internal name of our API call subclass...it's only used by your Python code. To tell ```shijid``` how to match requests for ```PingCall``` we set the ```routes``` regex class variable:

```python
routes = r"ping[^/]*$"
```

When ```shijid``` starts up, it scans the ```calls.py``` of all your API version modules for subclasses of ```urldispatch.URLMatchJSONResource```, and installs them using the ```routes``` regex for each subclass. So  ```PingCall``` will respond to requests matching:

```
http://<fqdn>/myloginapi/ping
```

Now let's say you'd like to supply a timestamp in the URL path for ```PingCall``` and treat it as an argument to the API call:

```
http://<fqdn>/myloginapi/ping/1438732412
```

We can add a [named capture group](https://docs.python.org/2/library/re.html) to ```routes```:

```python
routes = r"ping/(?P<timestamp>[0-9]+)$"
```

This will ensure only URLs ending in ```ping/``` plus an integer will be matched. The matched value will be available in the ```self.url_matches``` dictionary:

```python
class PingCall (urldispatch.URLMatchJSONResource):
    
    routes = r"ping/(?P<timestamp>\d+)$"
    
    def render_GET(self, request):
        timestamp =  int(self.url_matches["timestamp"])
        ...
```

Lastly, we've only defined a ```render_GET``` method on our ```PingCall``` subclass. So our call will only respond to HTTP ```GET``` requests right now. We can respond to ```POST```,```PUT```,```DELETE```, and ```HEAD``` requests by adding methods of the form: ```render_<HTTP_VERB>(self, request):```

There's one last thing we need to serve our new API with ```shijid```...a ```shijid.conf``` file. ```shiji_admin``` can stub one of these for us too:

```
shiji_admin -C ./myapis.shiji.conf
```

Let's take a look at our new config file stub:

```dosini
[general]
listen_ip: 127.0.0.1
listen_port: 9990
; Valid options: select, epoll, kqueue
reactor: select
; Base path for API modules
base_path: /<myapis>/

[logging]
; Optional. If log_file is not defined or is missing,
; will default to logging to syslog (preferred)
log_file:
syslog_prefix: "Shiji"

[auth]
secure_cookies_secrets: [""]

[apis]
; Listed in form:
;    module_name: url_path_regex
<api1>: <api1_path>

; OPTIONAL - Config sections for APIs
; If present, your API must implement
; the config_validate() function in its
; outer __init__.py
;[config_api1]
;api_option1: test
```

We only need to change a few things so ```shijid``` can find our new API:

```dosini
[general]
...
base_path: <set this to the path containing the mylogin_api folder>
...
[apis]
; Listed in form:
;    module_name: url_path_regex
mylogin_api : myloginapi
```

That's it! ```mylogin_api : myloginapi``` tells ```shijid``` to import our ```mylogin_api``` module, and use the regular expression ```myloginapi``` to match requests (you can use any regular expression you like to match requests for your API module):

```bash
$ shijid -c myapis.shiji.conf -p /tmp/shijid.pid &
[1] 70742

$ curl -H "Content-Type: application/json;charset=utf-8" -H "X-DigiTar-API-Version: mylogin_api-1.0+prod" http://localhost:9990/myloginapi/ping/123
"PONG! Right back at ya. I'm production baby!  (Timestamp Val: 123) (API: mylogin_api, Version: 1.0, Mode: prod)"
```

That's all it takes to serve your new API! Adding new calls is as simple as adding ```urldispatch.URLMatchJSONResource``` sub-classes to ```calls.py``` in your API module. You can find the full source code in: [/examples/mylogin_api](./examples/mylogin_api)



### Validating URL & JSON arguments ###

Serving a GET API call is fun. But for real work we need to be able to accept arguments as query URL and JSON arguments. 

Let's add a ```POST``` to ```PingCall``` to test our handling URL and JSON arguments:

```python
    @webapi.json_arguments([("client_tz", int),
                            ("client_id", unicode),
                            ("new_client", bool, webapi.ARG_OPTIONAL)])
    @webapi.url_arguments(["simple_auth_key"])
    @defer.inlineCallbacks
    def render_POST(self, request):
        
        # Make sure simple_auth_key is a good key
        auth_key = request.args["simple_auth_key"][0]
        if auth_key != "abc":
            defer.returnValue(str(webapi.ValueError(request, 
                                                    "simple_auth_key",
                                                    "Key isn't valid!")))
        
        # Test latency to request example.com
        start_time = time.time()
        web_agent = Agent(reactor)
        resp = yield web_agent.request("GET", "http://example.com")
        end_time = time.time()
        
        # new_client is an optional parameter,
        # so set a default value if it isn't present
        # in the JSON arguments
        new_client = False
        if request.jsonArgs.has_key("new_client"):
            new_client = request.jsonArgs["new_client"]
        
        # Return a JSON dictionary as the API call result.
        return_dict = {"result" : {"latency" : end_time-start_time,
                                   "client_tz" : request.jsonArgs["client_tz"],
                                   "client_id" : request.jsonArgs["client_id"],
                                   "new_client" : request.jsonArgs["new_client"]}}
        
        defer.returnValue(json.dumps(return_dict))
```

__NOTE:__ Before I start dissecting, there's a couple of housekeeping things here regarding how Twisted operates. Since Twisted is single-threaded and asynchronous, any code that has to wait on network I/O to complete should release control back to Twisted until the network I/O is done. This can be done most efficiently using [Twisted Deferreds](http://twistedmatrix.com/documents/15.2.0/core/howto/defer.html) (aka. promises) that define callbacks of your choosing to run when the network I/O is done. However, we're going to use the ```defer.inlineCallbacks``` function decorator instead. It will let us use Python's ```yield``` statement to tell Twisted where we want it to come back to when the network I/O completes (```inlineCallbacks``` does all the magic of creating Deferreds and registering callbacks for you, at the expense of extra overhead). Once we start using ```inlineCallbacks``` we also can't simply use ```return``` to send our response to the client. Instead we'll use ```defer.returnValue()``` everywhere we'd use a ```return``` statement.

The key to validating URL and JSON arguments are the ```@webapi.url_arguments``` and ```@webapi.json_arguments` decorators:

```python
    @webapi.json_arguments([("client_tz", int),
                            ("client_id", unicode),
                            ("new_client", bool, webapi.ARG_OPTIONAL)])
    @webapi.url_arguments(["simple_auth_key"])
```

```json_arguments``` only works with ```POST``` and ```PUT``` requests, and expects a JSON dictionary in the request body. The ```json_arguments``` decorator takes a list of tuples that define the keys to require in the JSON dictionary, and the datatypes they should be:

```python
[("<key_name>", <python_datatype>)]
```

So in this case:
```python
    @webapi.json_arguments([("client_tz", int),
                            ("client_id", unicode),
                            ("new_client", bool, webapi.ARG_OPTIONAL)])
```

expects a JSON dictionary in the HTTP request body that looks like this:

```json
{
	"client_tz" : -7,
	"client_id" : "someclient_id12",
	"new_client" : true
}
```

If ```client_tz``` isn't an integer, or ```client_id``` isn't a valid string, ```shijid``` will automatically return a ```webapi.ValueError``` HTTP response for you:

```bash
$curl -H "Content-Type: application/json;charset=utf-8" -H "X-DigiTar-API-Version: mylogin_api-1.0+prod" -X POST -d '{"client_tz" : "notaninteger", "client_id" : "myclient012", "new_client" : true}' http://localhost:9990/myloginapi/ping/123?simple_auth_key=abc

{"result": null, "error": {"exception_class": "ValueError", "error_code": 502, "exception_text": "Invalid value for argument 'client_tz'. Must be of type int"}}
```

Anytime a required URL or JSON argument is missing, or a JSON argument has an unexpected datatype, a ```webapi.ValueError``` response will be returned for you.

Wait. What about that ```webapi.ARG_OPTIONAL``` flag set on ```new_client```:
```python
...
("new_client", bool, webapi.ARG_OPTIONAL)
...
```

By default, ```json_arguments``` expects all JSON arguments to be required. Sometimes though, you want a JSON argument to be optional, but still enforce it to be a specific datatype if it is present. Adding ```webapi.ARG_OPTIONAL``` as the third item in the argument definition tuple, tells ```json_arguments``` you want that JSON argument to be optional.

Providing all of your requirements were satisified, ```shijid``` will provide your JSON arguments cast to their expected datatypes in the ```request.jsonArgs``` dictionary:

```python
        new_client = False
        if request.jsonArgs.has_key("new_client"):
            new_client = request.jsonArgs["new_client"]
```

Lastly, we have the ```url_arguments``` decorator:

```python
@webapi.url_arguments(["simple_auth_key"])
```

```url_arguments``` looks for required arguments in the [URL query string](https://en.wikipedia.org/wiki/Query_string). It takes a list of expected argument names, and only ensures they are present (it does NOT do datatype validation...if you need that use JSON arguments). In this case, it looks for ```simple_auth_key``` in the request's URL query string:

```
http://localhost:9990/myloginapi/ping/123?simple_auth_key=abc
```

If ```simple_auth_key``` is missing, a ```webapi.ValueError``` response will be automatically returned:

```bash
$ curl -H "Content-Type: application/json;charset=utf-8" -H "X-DigiTar-API-Version: mylogin_api-1.0+prod" -X POST -d '{"client_tz" : -7, "client_id" : "myclient012", "new_client" : true}' http://localhost:9990/myloginapi/ping/123

{"result": null, "error": {"exception_class": "ValueError", "error_code": 502, "exception_text": "Invalid value for argument 'simple_auth_key'. Argument is missing."}}
```

Query string arguments are always accessible under the ```request.args``` dictionary:

```python
auth_key = request.args["simple_auth_key"][0]
```

__NOTE:__ Each argument's value is stored as a list, since the same query string argument could be supplied multiple times in the same URL.

### Returning Custom Errors ###

You can always return Shiji's built-in error objects (see __Built-In APIError Classes__):

```python
defer.returnValue(str(webapi.ValueError(request, 
                                        "simple_auth_key",
                                        "Key isn't valid!")))
```

...which will respond to the user with a well-formatted JSON error dictionary:

```json
{"result": null, "error": {"exception_class": "ValueError", "error_code": 502, "exception_text": "Invalid value for argument 'simple_auth_key'. Key isn't valid!"}}
```

But you can also create your own Shiji-compatible error reponses that are sent to the user as JSON error dictionaries. Just sub-class ```webapi.APIError```, defining your own values for the class variables ```error_code```, ```exception_class```, and ```exception_text```:

```python
class SampleAdvancedError(APIError):
    error_code = 101
    exception_class = "SampleAdvancedError"
    exception_text = "A sample error that takes arguments in addition to 'request'. Extra Arg Value: %s"
    
    def __init__(self, request_object, extra_arg):
        self.exception_text = self.exception_text % extra_arg
        APIError.__init__(self, request_object)
```

__NOTE:__ If your error's ```exception_text``` never changes, you can skip overriding ```APIError```'s ```__init__``` method.

Then simply call ```str(SampleAdvancedError(request, "extra argument"))``` to create a JSON error dictionary.

The other benefit from defining your errors using subclasses of ```webapi.APIError``` is that ```shiji_admin``` will find and include them automatically when you generate API documentation.

### Custom API Configuration ###

Every Shiji API module has ```config.py``` shared by all of that API's versions. It defines a single method ```validate_config``` that is supplied a dictionary of options for that API taken from ```shijid.conf``` and is expected to return a finalized dictionary of the API's options:

```python
def validate_config(config_dict):
    
    required_fields = []
    
    for field in required_fields:
        if not config_dict.has_key(field):
            raise Exception("Missing required option '%s' in API config." % field)
    
    return config_dict
```

```validate_config``` can implement any validation and translation logic you desire, and should raise an ```Exception``` to stop ```shijid``` from starting up if a critical error is found in the API's configuration options. ```config_dict``` is populated with the key/value items in the API's section of ```shijid.conf```. For example, if your API were named ```myapi_login```, its configuration options would come from:

```dosini
[config_myapi_login]
db_server=value1
db_port=value2
```

and would appear in ```config_dict``` as:

```python
{"db_server" : "value1",
 "db_port" : "value2"}
```

```validate_config``` __must__ return a dictionary. From with your API calls, you can access the API's validated configuration data through ```request.api_config```:

```python
def render_GET(self, request):
    database_host = request.api_config["myapi_login"]["db_server"]
    database_port = request.api_config["myapi_login"]["db_port"]
    ...
```

### Result Paging ###

You'll likely find yourself implementing result paging on a regular basis, so Shiji provides a helper decorator to sanity check paging arguments ```page``` and ```page_len``` in the URL query string:

```python
@webapi.paged_results(default_page=0,default_page_len=200,max_page_len=500)
```

* ```default_page``` specifies the value of ```request.args["page"][0]``` if ```page``` is not provided in the URL query string.
* ```default_page_len``` specifies the value of ```request.args["page_len"][0]``` if ```page_len``` is not provided in the URL query string.
* ```max_page_len``` specifies the maximum value that is allowed for ```page_len```. (```page_len``` is the number of entries you will return per-page).

When you use ```@webapi.paged_results```, it will check to see if ```page``` and ```page_len` URL query string arguments are present and then:

* Validate ```page``` and ```page_len``` are valid integers.
* Validate ```page``` is &gt; -1.
* Validate ```page_len``` is &gt; 0 and &lt; ```max_page_len```.

Just add it as an additional decorator to your ```render_<HTTP_VERB>``` methods:

```python
    @webapi.paged_results(default_page=0,default_page_len=50,max_page_len=75)
    @defer.inlineCallbacks
    def render_GET(self, request):
        curr_page = request.args["page"][0]
        entries_per_page = request.args["page_len"][0]
        
        entries_list = yield get_some_entries()
        if len(entries_list) == 0:
          defer.returnValue(json.dumps([]))
        
        first_entry_idx = curr_page*entries_per_page
        if first_entry_idx > len(entries_list):
          first_entry_idx = 0
        last_entry_idx = first_entry_idx+entries_per_page
        if last_entry_idx > len(entries_list):
          last_entry_idx = len(entries_list)
        
        defer.returnValue(json.dumps(entries_list[first_entry_idx:last_entry_idx]))
```

### statsd Metric Support ###

If ```statsd``` support is configured in ```shijid.conf```, you can ship metrics using the ```metrics``` attribute on any ```request``` object:

```python

def render_GET(self, request):
    ...
    request.metrics.increment("myapi.somevalue")
    ...
```

We use an embedded version of ```txstatsd```.

## Generating API Documentation ##

```shiji_admin``` can automatically generate documentation for your web APIs using the docstrings on the ```render_<HTTP_VERB>``` methods. It will also list all error types defined in the API using ```APIError``` subclasses (including Shiji built-in errors). 

For example, let's say you added a docstring to the ```render_GET``` method for ```PingCall``` explaining how to use it:

```python
  def render_GET(self, request):
      """
      Simple PING call, that echoes back the client's supplied timestamp.
      
      URL Path Arguments:
      ----------
          timestamp (int) - Client supplied UNIX timestamp.
      
      
      Returns
      ---------
      
          Success:
              (unicode) - String echoing parameters.
      
          Failure:
              Returns a JSON error dictionary.
      
      """
      ...
```

You can automatically generate documentation for  ```mylogin_api``` by running:

```bash
$ shiji_admin -D mylogin_api -T json | python -m json.tool
```

```json
{
    "api_name": "mylogin_api",
    "versions": {
        "1.0": {
            "calls": {
                "ping/<timestamp>\\d+)": {
                    "GET": "<pre><code>    Simple PING call, that echoes back the client's supplied timestamp.\\n\\n    URL Path Arguments:\\n    ----------\\n        timestamp (int) - Client supplied UNIX timestamp.\\n\\n\\n    Returns\\n    ---------\\n\\n        Success:\\n            (unicode) - String echoing parameters.\\n\\n        Failure:\\n            Returns a JSON error dictionary.\\n</code></pre>",
                    "POST": "<pre><code>    Calculate the latency of querying example.com.\\n\\n    URL Path Arguments:\\n    ----------\\n        timestamp (int) - Client supplied UNIX timestamp.\\n\\n    JSON Body Arguments:\\n    ----------\\n        client_tz (int) - Client's timezone offset from GMT.\\n        client_id (unicode) - Client's unique client ID string.\\n        new_client (bool) (optional) - Does magic if true...\\n\\n    Returns:\\n    ----------\\n\\n    Success:\\n            \"result\" : {\\n                \"latency\" (float) - Time it took to complete example.com request in secs.\\n                \"client_tz\" (int) - Supplied client timezone offset.\\n                \"client_id\" (unicode) - Supplied unique client ID.\\n                \"new_client\" (bool) - Whether magic happened...\\n            }\\n\\n    Failure:\\n        Returns a JSON error dictionary.\\n</code></pre>"
                }
            },
            "error_codes": {
                "AccessDeniedError": {
                    "error_code": 501,
                    "exception_text": "Insufficient permission to perform the requested action."
                },
                "CharsetNotUTF8Error": {
                    "error_code": 504,
                    "exception_text": "The Content-Type of the API request did not specify a charset, or the charset specified was not UTF-8."
                },
                "ContentTypeError": {
                    "error_code": 503,
                    "exception_text": "The Content-Type of the API request was not of the expected format...or the API/version requested does not exist."
                },
                "ExpiredSecureCookieError": {
                    "error_code": 508,
                    "exception_text": "Secure cookie '%s' is expired."
                },
                "InvalidAuthenticationError": {
                    "error_code": 506,
                    "exception_text": "Authentication information is invalidly formed and/or missing required elements."
                },
                "InvalidSecureCookieError": {
                    "error_code": 507,
                    "exception_text": "Secure cookie '%s' signature '%s' is invalid."
                },
                "JSONDecodeError": {
                    "error_code": 205,
                    "exception_text": "Arguments passed in API call request are not validly formed JSON."
                },
                "JSONEncodeError": {
                    "error_code": 204,
                    "exception_text": "An unrecoverable error has occurred JSON-encoding the API call result."
                },
                "RequestNotHashError": {
                    "error_code": 206,
                    "exception_text": "Request body must be a JSON-encoded hash table/dictionary."
                },
                "SampleAdvancedError": {
                    "error_code": 101,
                    "exception_text": "A sample error that takes arguments in addition to 'request'. Extra Arg Value: %s"
                },
                "SampleNormalError": {
                    "error_code": 100,
                    "exception_text": "A sample normal error that doesn't take arguments except for 'request'."
                },
                "UnexpectedServerError": {
                    "error_code": 505,
                    "exception_text": "An unexpected error has occurred processing the request. Error: '%s'"
                },
                "UnknownAPICallError": {
                    "error_code": 203,
                    "exception_text": "The requested API call '%s' is unknown."
                },
                "UnknownAPIError": {
                    "error_code": 208,
                    "exception_text": "The requested API '%s' is unknown."
                },
                "UnknownAPIVersionError": {
                    "error_code": 207,
                    "exception_text": "API version '%s' is invalid or specifies an API/version that does not exist."
                },
                "ValueError": {
                    "error_code": 502,
                    "exception_text": "Invalid value for argument '%s'. %s"
                }
            }
        }
    }
}
```

```shiji_admin``` documentation generation supports two output template types:

* ```fogbugz``` - An HTML output using styles compatible with the [Fogbugz](http://www.fogcreek.com/fogbugz/) Wiki.
* ```json``` - A JSON dictionary containing all of the call and error documentation for the API.

The JSON output is likely more interesting, since you can pipe it into other tools to turn into the exact format you want. The JSON output uses this structure:

* api_name (string) - Name of the API being documented
* versions (dictionary) :
  * &lt;version_number&gt; (dictionary)
    * calls (dictionary)
      * &lt;API call regex pattern&gt; (dictionary) 
        * &lt;HTTP verb&gt; (string) - Docstring for render_&lt;HTTP_VERB&gt;
    * errors (dictionary)
      * &lt;exception_class&gt; (dictionary) 
        * error_code (int)
        * exception_text (string)

## Authenticating API Requests ##

Shiji provides built-in support for secure cookies. ```shijid``` supports a list of multiple secrets that can be used for signing secure cookies to allow for key rotation (the first secret is used for signing new secure cookies). Within your code you can use these calls to set and get valid secure cookies:

* ```auth.get_secure_cookie(request, cookie_name)``` - Returns either the decoded value of the secure cookie if it is valid or ```webapi.ExpiredSecureCookieError``` or ```webapi.InvalidSecureCookieError``` if the cookie was expired or invalidly signed.
	* ```request``` (twisted.web.http.Request) - Object containing the HTTP request.
	* ```cookie_name``` (unicode string) - Name of the secure cookie to validate and decode. 
* ```auth.set_secure_cookie(request, name, value, expires_days=30, path="/")``` - Creates/signs and sets the specified secure cookie in the given Twisted Request object.
	* ```request``` (twisted.web.http.Request) - Object containing the HTTP request.
	* ```name``` (unicode string) - Name of the secure cookie to set.
	* ```value``` (unicode string) - Value to set in the secure cookie (and sign).
	* ```expires_days``` (int) - How many days secure cookie should be valid for. (Default: 30)
	* ```path``` (unicode string) - Cookie path. (Default: /)


## Locations & Versioning ##

APIs are segmented by top-level URL (i.e. /auth, /user,  /logging, etc.) and are versioned based on the X-DigiTar-API-Version HTTP header passed in the HTTP request (http://barelyenough.org/blog/2008/05/versioning-rest-web-services/).
 
Versions take the form:
 
```
<API>-<dotted version #>+<prod>
```

For example, this  would indicate a request for v0.9 of the ```auth``` API in production mode (only "prod" mode is supported):

```
X-DigiTar-API-Version: auth-0.9+prod
```

API requests missing an X-DigiTar-API-Version header, requests specifying a non-existent version of an API, or a X-DigiTar-API-Version that doesn't follow the format above will return a ```406 'Not Acceptable'``` HTTP error. 

##Arguments &amp; Return Values##

### REST/JSON ###

__HTTP Request Content-Type:__ ```application/json;charset=utf-8```
_(This is important. If not set to application/json;charset=utf-8 we will reject the request.)_

__Any internally experienced exceptions (i.e. can't connect to needed database, etc) will return an UnexpectedServerError API exception.__

#### Data Type Notes: ####

* __All strings are UTF-8 strings.__
* __Unless otherwise indicated, integers are 64-bit signed integers.__

#### Arguments: ####

* Encoded as a __JSON__ hashtable in the request's message body, where the keys are the argument names and values are the argument values.
*	Values are expected to be of the types specified by the API call's documentation.

#### Return Values/Errors: ####

* The entire returned response is encoded using UTF-8.
* Errors are returned as __JSON__ hashtables with two possible top-level keys: ```error```, ```result```
* The ```result``` top-level key is always present in errors. It is ```null``` if an error has occurred. You are encouraged to always put your return values under the ```result``` key in your API responses.
* The ```error```top-level key is always present. It is ```null``` if __no__ error has occurred. Otherwise (the HTTP response code is 4xx...see HTTP Error Codes below), it contains the details about an exception and its value is a hash table with the keys ```error_code```, ```exception_class```, ```exception_text```:

| KEY | DATA TYPE | VALUE |
|-----|-----------|-------|
| error\_code | integer | Error code for this exception class. |
| exception\_class | string | Camel-cased unique name for this exception. |
| exception\_text | string | Explanation text of what went wrong. Typically written in such a way as to be displayable to the end-user. |

__Example:__

```json
{"error_code" : 507,
 "exception_class" : "InvalidSecureCookieError",
 "exception_text" : "Secure cookie 'username' signature '1c5df83af507656cf5412151c0557c06e7ece200' is invalid."}
````

__IMPORTANT:__ ```error_code``` is only guaranteed to be unique amongst errors within the same API (i.e. the same ```error_code``` number could be reused for a different error in another API). You should use ```exception_class``` for identifying the type of error.

#### Built-In APIError Classes ####


| exception\_class | error\_code | exception\_text |
| --- | --- | --- |
| UnknownAPICallError | 203 | The requested API call "%s" is unknown. |
| JSONEncodeError | 204 | An unrecoverable error has occurred JSON-encoding the API call result. |
| JSONDecodeError | 205 | Arguments passed in API call request are not validly formed JSON. |
| RequestNotHashError | 206 | Request body must be a JSON-encoded hash table/dictionary. |
| UnknownAPIVersionError | 207 | API version "%s" is invalid or specifies an API/version that does not exist. |
| UnknownAPIError | 208 | The requested API "%s" is unknown. |
| AccessDeniedError | 501 | Insufficient permission to perform the requested action. |
| ValueError | 502 | Invalid value for argument "%s". %s |
| ContentTypeError | 503 | The Content-Type of the API request was not of the expected format...or the API/version requested does not exist. |
| CharsetNotUTF8Error| 504 | The Content-Type of the API request did not specify a charset, or the charset specified was not UTF-8. |
| UnexpectedServerError | 505 | An unexpected error has occurred processing the request. Error: "%s" |
| InvalidAuthenticationError | 506 | Authentication information is invalidly formed and/or missing required elements. |
| InvalidSecureCookieError | 507 | Secure cookie "%s" signature "%s" is invalid. |
| ExpiredSecureCookieError | 508 | Secure cookie "%s" is expired. |


#### HTTP Error Codes ####

| HTTP ERROR CODE | ERROR MESSAGE |  MEANING |
|-----------------|---------------|----------|
| 404 | Unknown Page/API | The requested page/API does not exist. |
| 406 | Not Acceptable | X-DigiTar-API-Version is missing, invalid or specifies an API/version that does not exist. |
| 409 | Conflict | An error has occurred other than:<br/>1.) Version information missing<br/>2.) an unknown API was called.<br/>__Parse the response body to identify the specific JSON-encoded exception.__ |

#### Result Paging ###

API calls that return lists of records may implement "paging" of the results to ensure good performance. For calls that indicate __Paged Results__, you can control the number of results returned per request, and your relative position in the result list using the following URL query string arguments (each call will indicate their default and maximum allowed values for ```page_len```):

* ```page_len``` __(int)__ - Maximum number of results to return in the given request.
* ```page``` __(int)__ - Zero-indexed relative position in the result set for the specified ```page_len```.

## shijid.conf Reference##

### [general] Section ###

| Option Name | Value |
| --- | --- |
| listen_ip | IP address to listen on. |
| listen_port | TCP port to listen on. |
| reactor | Twisted reactor type. Valid options: select, epoll, kqueue (recommended: epoll) |
| server_ident | Optional. Sets the ```Server``` header name. (Default: ```Shiji API Server```) |
| base\_path | Base path to your API modules. |
| cross\_origin\_domains | Value is set in the ```Access-Control-Allow-Origin``` header used to allow CORS requests. |
| inhibit\_http\_caching | Disable caching by setting ```Cache-Control: no-cache``` and ```Pragma: no-cache```. |
| thread\_pool\_size | Set the Twisted thread\_pool\_size used for DBAPI requests etc. |

### [statsd] Section ###

| Option Name | Value |
| --- | --- |
| host | Hostname of statsd metric server. Can be empty to indicate no metric support. |
| port | TCP port of statsd metric server. |
| scheme | Scheme to prefix on all logged metrics. (e.g. myco.myapi) |

### [logging] Section ###

| Option Name | Value |
| --- | --- |
| log_file | Path to log file. __Optional.__ If ```log_file``` is not defined or is missing, will default to logging to syslog (preferred) |
| syslog_prefix | Text to prefix on syslog entries. |

### [auth] Section ###
| Option Name | Value |
| --- | --- |
| secure_cookies_secrets | JSON array of strings defining secrets allowed to sign secure cookies. |

### [apis] Section ###

__NOTE:__ This section defines the API modules to load and the base URL path they will be accessible on. The API base path is defined as a regular expression to allow matching flexibility.

__Example:__
```dosini
my\_auth\_api: auth
```

### [config_&lt;API_module_name&gt;] ###

Each API module has a config section ```[config_<API_module_name>]```. For example:

```dosini
[config_my_auth_api]
```

The options of the API's config section are passed as a dictionary into the API's ```config.validate_config(dict)``` call, so the API can validate and massage them as needed. The dictionary returned from ```config.validate_config(dict)``` is accessible in each API call via ```request.api_config["<API_module_name>"]```.

## License ##

Shiji is licensed under the MIT License. Please see [LICENSE.md](./shiji/blob/master/LICENSE.md) in the project directory for the full license terms.

&copy;2015 DigiTar Inc.
