# -*- coding: utf-8-*-
####################################################################
# FILENAME: shijid.py
# PROJECT: Shiji API
# DESCRIPTION: Shiji API daemon
#
# REQUIRES:
#
# 
# $Id$
####################################################################
# (C)2015 DigiTar Inc.
# Licensed under the MIT License.
####################################################################
import sys, os, syslog, traceback
try:
    import json
except ImportError:
    import simplejson as json

pyfile_path = ''.join([path_part + "/" for path_part in __file__.split("/")[:-1]])
sys.path.append(pyfile_path)

from shiji import urldispatch, foundation, auth, stats
import shiji

from ConfigParser import SafeConfigParser, NoOptionError, NoSectionError
from optparse import OptionParser

import twisted.internet
import twisted.python.log as tw_log
import twisted.python.syslog as tw_syslog

def validate_config(fn_config):
    """
    Read the spec'd config in and return a configuration parser.
    """
    try:
        f_configuration = open(fn_config)
    except Exception:
        print "Could not open configuration file '%s'. Please check the location." \
               % fn_config
        sys.exit(-1)

    cfg = SafeConfigParser()
    cfg.readfp(f_configuration)
    f_configuration.close()
    
    return cfg
    
    


def main():
    opt_parser = OptionParser()
    opt_parser.add_option("-c", "--config_file", dest="config_file", 
                      default="/etc/shiji/shiji.conf",
                      help="Path to the Shiji config file to be used. The " \
                      "default is /etc/shiji/shiji.conf")
    opt_parser.add_option("-p", "--pid_file", dest="pid_file", 
                      default="/var/run/shijid.pid",
                      help="Path to the Shiji PID file to be used. The " \
                      "default is /var/run/shijid.pid")
    args = opt_parser.parse_args()[0]
    
    pid_file = args.pid_file
    
    # # Retrieve configuration
    if os.getenv("SHIJI_CONFIG"):
        fn_config = os.getenv("SHIJI_CONFIG")
    else:
        fn_config = args.config_file
    cfg_central = validate_config(fn_config)


    # Load general settings
    try:
        listen_ip = cfg_central.get("general", "listen_ip")
    except NoOptionError:
        print "No 'listen_ip' directive found. Defaulting to 127.0.0.1."
        listen_ip = "127.0.0.1"
    
    try:
        thread_pool_size = cfg_central.getint("general", "thread_pool_size")
    except NoOptionError:
        print "No 'thread_pool_size' directive found. Defaulting to: 30"
        thread_pool_size = 30
    
    try:
        listen_port = cfg_central.getint("general", "listen_port")
    except NoOptionError:
        print "No 'listen_port' directive found. Defaulting to 9990."
        listen_port = 9990
    
    try:
        reactor_type = cfg_central.get("general", "reactor").lower()
        if not reactor_type in ["select", "epoll", "kqueue"]:
            print "Invalid reactor type '%s'. Only select, epoll, kqueue allowed." % reactor_type
            sys.exit(-1)
    except NoOptionError:
        print "No reactor type specified. Defaulting to 'select'."
    
    try:
        base_path = cfg_central.get("general", "base_path")
        sys.path.append(base_path)
    except NoOptionError:
        print "Could not find 'base_path' directive. A base path for the API modules must be defined. Exiting."
        sys.exit(-1)
    
    try:
        server_ident = cfg_central.get("general", "server_ident")
    except NoOptionError:
        server_ident = "Shiji API Server"
    
    try:
        cross_origin_domains = cfg_central.get("general", "cross_origin_domains")
    except NoOptionError:
        cross_origin_domains = None
    
    try:
        inhibit_http_caching = cfg_central.getboolean("general", "inhibit_http_caching")
    except NoOptionError:
        inhibit_http_caching = True
    
    try:
        honor_xrealip = cfg_central.getboolean("general", "honor_x_realip")
    except NoOptionError:
        honor_xrealip = True
    
    # Load statsd
    statsd_host = statsd_port = statsd_scheme = None
    if "statsd" in cfg_central.sections():
        try:
            statsd_host = cfg_central.get("statsd", "host")
        except NoOptionError:
            print "[statsd] section is present, but required 'host' option missing."
            sys.exit(-1)
        
        try:
            statsd_port = cfg_central.getint("statsd", "port")
        except NoOptionError:
            print "[statsd] section is present, but required 'port' option missing."
            sys.exit(-1)
        
        try:
            statsd_scheme = cfg_central.get("statsd", "scheme")
        except NoOptionError:
            print "[statsd] section is present, but required 'scheme' option missing."
            sys.exit(-1)
    
    # Load custom configuration sections
    config = {}
    
    for section in cfg_central.sections():
        if section[:7] == "config_":
            api_name = section[7:].lower()
            config[api_name] = dict(cfg_central.items(section))
            try:
                api_module = __import__(api_name + ".config" ,globals(),locals(),[],-1)
            except ImportError, e:
                print "Could not load API '%s' when parsing API config sections. (%s)" % (api_name, str(e))
                sys.exit(-1)
            config[api_name] = api_module.config.validate_config(config[api_name])
    
    # Setup the API routes...list of tuples
    api_hash = dict(cfg_central.items("apis"))
    
    routes =[]
    
    for api in api_hash.keys():
        api_module = __import__(api,globals(),locals(),[],-1)
        routes.append((api_hash[api], api_module))
    
    root = urldispatch.APIRouter(routes, config=config, 
                                 cross_origin_domains=cross_origin_domains,
                                 inhibit_http_caching=inhibit_http_caching)
    shiji.change_server_ident(server_ident)
    
    # Setup logging
    try:
        fn_log = cfg_central.get("logging", "log_file")
    except NoOptionError:
        fn_log = ""
    
    try:
        log_prefix = cfg_central.get("logging", "syslog_prefix")
    except NoOptionError:
        log_prefix = "Shiji"
    
    if fn_log:
        tw_log.startLogging(open(fn_log, "w"))
    else:
        tw_syslog.startLogging(prefix=log_prefix, facility=syslog.LOG_LOCAL0)
    
    # Install reactor
    try:
        if reactor_type.lower() == "epoll":
            from twisted.internet import epollreactor as selected_reactor
            from twisted.internet import reactor
        elif reactor_type.lower() == "select":
            from twisted.internet import selectreactor as selected_reactor
            from twisted.internet import reactor
        elif reactor_type.lower() == "kqueue":
            from twisted.internet import kqreactor as selected_reactor
            from twisted.internet import reactor
    except IOError, e:
        print "Error starting up reactor type '%s'. (%s)" % (reactor_type, str(e))
        sys.exit(-2)
    
    
    # Set thread pool size
    print "Setting Thread Pool Size: %d" % thread_pool_size
    reactor.suggestThreadPoolSize(thread_pool_size)
    
    # Install Authentication
    
    try:
        auth_enabled = cfg_central.getboolean("auth", "enable_auth")
    except NoOptionError:
        auth_enabled = False
    
    if auth_enabled:
        try:
            auth_mod_name = cfg_central.get("auth", "auth_module")
        except NoOptionError:
            print "'auth_module' option is required when authentication is enabled."
            sys.exit(-1)
        
        try:
            auth_class_name = cfg_central.get("auth", "auth_class")
        except NoOptionError:
            print "'auth_class' option is required when authentication is enabled."
            sys.exit(-1)
        
        try:
            json_args = json.loads(cfg_central.get("auth", "auth_args"))
            auth_args = {}
            for arg in json_args.keys():
                auth_args[str(arg)] = json_args[arg]
        except NoOptionError:
            print "'auth_args' option is required when authentication is enabled."
            sys.exit(-1)
        except ValueError:
            print "'auth_args' contents is not valid JSON."
            sys.exit(-1)
        
        auth_module = __import__(auth_mod_name, globals(), locals(), [], -1)
        auth_class = getattr(auth_module, auth_class_name)
        auth.install_auth(auth_class(**auth_args))
    
    try:
        secure_cookies_secrets = json.loads(cfg_central.get("auth", "secure_cookies_secrets"),
                                            encoding='ascii')
        secure_cookies_secrets = [x.encode("ascii") for x in secure_cookies_secrets]
    except NoOptionError:
        print "Required option 'secure_cookies_secrets' is missing from 'auth' section."
        sys.exit(-1)
    
    auth.install_secure_cookies(secure_cookies_secrets)
    
    # Start up statsd connection if configured
    if statsd_host:
        print "API Stats Enabled. (statsd Server:%s:%d  Prefix:%s)" % (statsd_host, statsd_port, statsd_scheme)
        reactor.listenUDP(0, stats.install_stats(statsd_host,
                                                 statsd_port,
                                                 statsd_scheme))
    
    # Bind listening server factory to Twisted application
    reactor.listenTCP(listen_port, foundation.ShijiSite(root, honor_xrealip=honor_xrealip), interface=listen_ip)
    
    # Set up PID and run
    try:
        if os.path.exists(pid_file):
            print "Removing stale PID file."
            os.remove(pid_file)
    except Exception, e:
        print "Error removing stale PID file. (%s)" % str(e)
        sys.exit(-3)
    
    try:
        f = open(pid_file, "w")
        f.write(str(os.getpid()))
        f.flush()
        f.close()
    except Exception, e:
        print "Error writing PID file %s. (%s)" % (pid_file, str(e))
        sys.exit(-3)
    
    print "Listening on %s:%d" % (listen_ip, listen_port)
    reactor.run()
    
    try:
        os.remove(pid_file)
    except Exception, e:
        print "Error removing PID file %s. (%s)" % (pid_file, str(e))
        sys.exit(-3)

if __name__ == "__main__":
    main()
