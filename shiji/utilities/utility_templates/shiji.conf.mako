;
; Shiji API Daemon Config
;

[general]
listen_ip: 127.0.0.1
listen_port: 9990
; Valid options: select, epoll, kqueue
reactor: select
server_ident: My Custom API Server
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