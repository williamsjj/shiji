#!/usr/bin/python
####################################################################
# FILENAME: utilities/shiji_admin.py
# PROJECT: Shiji API
# DESCRIPTION: Management utility for creating new APIs and versions.
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
import sys, os, re, inspect, json
from optparse import OptionParser
from datetime import date
import mako, markdown
from mako.lookup import TemplateLookup
from shiji import urldispatch, webapi

ARG_ERR = -1
MKDIR_ERR = -2
WRITE_FILE_ERR = -3
TEMPLATE_ERR = -4

re_version_entry = re.compile(r'\s*"(?P<version_id>[.\d]+)"\s*:\s*\(r"(?P<version>[.\d]+)",\s*(?P<version_module>v[_\d]+)\)\s*')

curr_dir = os.getcwdu()
templates_dir = os.path.dirname(os.path.realpath(__file__)) + "/utility_templates"
template_lookup = TemplateLookup(directories=templates_dir,
                                 output_encoding="utf-8",
                                 input_encoding="utf-8",
                                 encoding_errors="replace")

def extract_version_map(fn):
    version_list = []
    
    f_api_init = open(fn, "r")
    in_versions = False
    
    for line in f_api_init.readlines():
        if line[:16] == "api_versions = {":
            in_versions = True
        if in_versions:
            version_match = re_version_entry.match(line)
            if version_match:
                version_dict = version_match.groupdict()
                version_list.append([version_dict["version_id"],
                                     version_dict["version"],
                                     version_dict["version_module"]])
            if line[-2] == "}":
                in_versions = False
    f_api_init.close()
    return version_list

def process_route(route):
    """Format route RegEx for display."""
    
    # Remove RegEx control characters
    route = route.replace("(?P","")
    route = route.replace("[^/]*)", "")
    if route[-1] == "$":
        route = route[:-1]
    
    return route

def process_api_desc(desc):
    """Apply processing on body to prepare for display."""
    
    # Escape newlines for JSON compatibility
    desc = markdown.markdown(desc)
    desc = desc.replace("\n", "\\n")    
    return desc

def cmd_gen_config(fn_config):
    "Create a new stub config file for shijid."
    
    try:
        tmpl_config = template_lookup.get_template("shiji.conf.mako")
        if os.path.exists(fn_config):
            print "Config file %s already exists. Exiting." % fn_config
            sys.exit(WRITE_FILE_ERR)
        
        f_config = open(fn_config, "w")
        f_config.write(tmpl_config.render())
        f_config.flush()
        f_config.close()
    except IOError, e:
        print "Error generating config file %s." % (fn_config, str(e))
        sys.exit(WRITE_FILE_ERR)


def cmd_new(api, version):
    "Create a new API and/or version."
    # Generate API stub if it doesn't already exist
    api_dir = curr_dir + "/" + api
    version_module = "v" + "_".join(version.split("."))
    tmpl_new_api = template_lookup.get_template("new_api.py.mako")
    tmpl_new_api_config = template_lookup.get_template("new_api_config_module.py.mako")
    if not os.path.exists(api_dir):
        try:
            os.mkdir(api_dir)
        except Exception, e:
            print "Error making directory '%s': %s" % (api, str(e))
            sys.exit(MKDIR_ERR)
        
        # Generate <api>/__init__.py
        try:
            f_api_init = open(api_dir + "/__init__.py", "w")
            f_api_init.write(tmpl_new_api.render(api=api,
                                                 version_module=version_module,
                                                 version_map={}
                                                 ))
        except IOError, e:
            print "Error generating %s/__init__.py: %s" % (api, str(e))
            sys.exit(WRITE_FILE_ERR)
        
        f_api_init.close()
        
        # Generate <api>/config.py
        try:
            f_api_config = open(api_dir + "/config.py", "w")
            f_api_config.write(tmpl_new_api_config.render(api=api))
        except IOError, e:
            print "Error generating %s/config.py: %s" % (api, str(e))
            sys.exit(WRITE_FILE_ERR)
        
        f_api_config.close()
        
        print "Generated '%s' API." % api
    
    # Generate version if it doesn't already exist
    if not os.path.isdir(api_dir):
        print "Error. '%s' already exists and is not a directory."
        sys.exit(MKDIR_ERR)
    
    version_dir = api_dir + "/" + version_module
    
    if os.path.exists(version_dir):
        print "'%s/%s' version directory already exists. Exiting." % (api, version_module)
        sys.exit(MKDIR_ERR)
    
    try:
        os.mkdir(version_dir)
    except Exception, e:
        print "Error making directory '%s/%s':%s" % (api, version_module, str(e))
        sys.exit(MKDIR_ERR)
    
    # Update <api>/__init__.py with new version
    version_map = extract_version_map(api_dir + "/__init__.py")
    version_map.append([version, version, version_module])
    
    # Generate <api>/<version>/__init__.py
    tmpl_new_version = template_lookup.get_template("new_version.py.mako")
    try:
        f_ver_init = open(version_dir + "/__init__.py", "w")
        f_ver_init.write(tmpl_new_version.render(api=api,
                                                 version=version,
                                                 version_module=version_module))
    except IOError, e:
        print "Error generating %s/%s/__init__.py: %s" % (api,
                                                          version_module,
                                                          str(e))
    
    try:
        f_api_init = open(api_dir + "/__init__.py", "w")
        f_api_init.write(tmpl_new_api.render(api=api,
                                             version_module=version_module,
                                             version_map=version_map
                                             ))
    except IOError, e:
        print "Error generating %s/__init__.py: %s" % (api, str(e))
        sys.exit(WRITE_FILE_ERR)
    f_api_init.close()
    
    # Generate <api>/<version>/calls.py
    tmpl_new_calls = template_lookup.get_template("new_calls.py.mako")
    try:
        f_calls = open(version_dir + "/calls.py", "w")
        f_calls.write(tmpl_new_calls.render(api=api,
                                            version=version,
                                            version_module=version_module))
    except IOError, e:
        print "Error generating %s/%s/calls.py: %s" % (api,
                                                       version_module,
                                                       str(e))
        sys.exit(WRITE_FILE_ERR)
    
    # Generate <api>/<version>/errors.py
    tmpl_new_calls = template_lookup.get_template("new_errors.py.mako")
    try:
        f_calls = open(version_dir + "/errors.py", "w")
        f_calls.write(tmpl_new_calls.render(api=api,
                                            version=version,
                                            version_module=version_module))
    except IOError, e:
        print "Error generating %s/%s/errors.py: %s" % (api,
                                                        version_module,
                                                        str(e))
        sys.exit(WRITE_FILE_ERR)
    
    print "Generated version '%s'" % version

def cmd_docs(docs, template):
    "Generate API documentation."
    doc_tree = {"versions" : {}}
    sys.path.append(curr_dir)
    api_module = __import__(docs)
    
    doc_tree["api_name"] = api_module.api_name
    
    for version in api_module.api_versions.keys():
        doc_tree["versions"][version] = {"calls" : {}, "error_codes" : {}}
        for member in inspect.getmembers(api_module.api_versions[version][1].calls):
            if inspect.isclass(member[1]):
                if issubclass(member[1], urldispatch.URLMatchJSONResource):
                    if member[1].routes:
                        api_call = {}
                        for sub_member in dir(member[1]):
                            if sub_member[:7] == "render_":
                                method_doc = getattr(member[1], sub_member).__doc__
                                if method_doc and sub_member[7:] != "HEAD" and method_doc[:14] != "Our super-JSON":
                                    api_call[sub_member[7:]] = process_api_desc(getattr(member[1], sub_member).__doc__)
                        
                        if isinstance(member[1].routes, str):
                            doc_tree["versions"][version]["calls"][process_route(member[1].routes)] = api_call
                        elif isinstance(member[1].routes, list):
                            route_list = ""
                            for route in member[1].routes:
                                route_list = route_list + "," + process_route(route)
                            doc_tree["versions"][version]["calls"][route_list] = api_call
        
        for member in (inspect.getmembers(api_module.api_versions[version][1].errors) + \
                       inspect.getmembers(webapi)):
            if inspect.isclass(member[1]):
                if issubclass(member[1], webapi.APIError) and not member[1].__name__=="APIError":
                    if not member[1].exception_class:
                        raise Exception("Error Generation API Docs: Error class %s is missing an exception_class." % member[1].__name__)
                    errcode_contents = { "error_code" : member[1].error_code,
                                         "exception_text" : member[1].exception_text }
                    doc_tree["versions"][version]["error_codes"][member[1].exception_class] = errcode_contents
    
    if template.lower() == "json":
        return json.dumps(doc_tree)
    else:
        try:
            tmpl_doc = template_lookup.get_template("doc_api_%s.html.mako" % template)
            return tmpl_doc.render(versions=doc_tree["versions"], year=date.today().year)
        except mako.exceptions.TopLevelLookupException:
            print "Error. No documentation template '%s'." % template
            sys.exit(TEMPLATE_ERR)

def main():
    # Validate command line and setup utility
    parser = OptionParser()
    parser.add_option("-A", "--api", dest="api",
                      help="Usage: --api <api_name> <version_number> \n " + \
                           "Create a new API in the current working directory " + \
                           "named <api_name>.")
    parser.add_option("-V", "--version", dest="version",
                  help="Usage: --version <version_number> \n " + \
                       "Create a new version for the API spec'd by --api. ")
    parser.add_option("-D", "--docs", dest="docs",
                      help="Usage: --docs <api_to_document> \n" + \
                           "Generate API documentation for the spec'd API.")
    parser.add_option("-T", "--docs_template", dest="template",
                      help="Usage: --docs_template <template_ID> \n" + \
                           "Output generated API documentation using " + \
                           "spec'd template. (Valid: fogbugz, json)")
    parser.add_option("-C", "--gen_config", dest="gen_config",
                      help="Usage: --gen_config <config_file_path> \n" + \
                           "Generate a stub shijid config file."
                     )
    args = parser.parse_args()[0]

    if not (args.api and args.version) and not (args.docs and args.template) and not args.gen_config:
        print "Missing required arugments. Please use --help for usage details."
        sys.exit(ARG_ERR)
    
    # Process "--gen_config" command
    if args.gen_config:
        cmd_gen_config(args.gen_config)
    
    # Process "--new" command
    if args.api and args.version:
        cmd_new(args.api, args.version)
    
    # Process --docs and --template command
    if args.docs and args.template:
        print cmd_docs(args.docs, args.template)

if __name__ == "__main__":
    main()
