# -*- coding: utf-8-*-
# ###################################################################
# FILENAME: ./${api}/config.py
# PROJECT: 
# DESCRIPTION: ${api} API Configuration Validation
#
#
# ###################################################################


# Validate API configuration section from config file
def validate_config(config_dict):
    
    required_fields = []
    
    for field in required_fields:
        if not config_dict.has_key(field):
            raise Exception("Missing required option '%s' in API config." % field)
    
    return config_dict

