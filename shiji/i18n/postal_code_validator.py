# ###################################################################
# FILENAME: i18n/postal_code_validator.py
# PROJECT: 
# DESCRIPTION: International postal code validator classes.
#
#
# $Id$
# ###################################################################
# (C)2015 DigiTar Inc.
# Licensed under the MIT License.
# ###################################################################

import re, os
from os import path
from lxml import etree

class PostalCodeValidator (object):
    """
    Verifies that a given postal code is valid or invalid.
    """
    
    def __init__(self, postal_data_path=None):
        """Initialize (and load) validator. If postal_data_path is supplied,
           PostalCodeValidator will attempt to load the file's contents into
           the validator. The file must be in the same format as the
           postalCodeData.xml file supplied by CLDR core releases under
           common/supplemental.
           
           Arguments:
           
              postal_data_path (string) (optional) - Path to CLDR postalCodeData formatted
                                                     XML file containing the postal code
                                                     pattern data to load.
           Returns:
               
               Success: Nothing
               
               Failure: Raises an exception.).
        """
        self.postal_code_patterns = {}
        
        if(postal_data_path):
            # Load postal code data from supplied XML filename
            if not path.exists(postal_data_path):
                raise PostalCodeDataFileDNEError(postal_data_path)
            
            postal_tree = etree.parse(postal_data_path)
            for element in postal_tree.find("postalCodeData").iterchildren("postCodeRegex"):
                self.load_country(element.attrib["territoryId"], element.text)
    
    def supported_countries(self):
        """
        Return a list of 2-digit ISO 3166 country codes
        for the countries' postal codes the validator
        can verify.
        
        Arguments:
            None
            
        Returns: (list of strings)
            * List of 2-digit ISO 3166 country code strings.
        """
        return self.postal_code_patterns.keys()
    
    def load_country(self, iso_code, pattern):
        """
        Load/replace a country's postal code regex pattern into the validator.
        
        Arguments:
        
            * iso_code (string) - 2-digit ISO 3166 country code
            * pattern (string) - Regular expression pattern that matches
                                 the country's valid postal codes.
        
        Returns:
        
            Success:
                Nothing
            
            Failure:
                Raises an exception.
        """
        
        if(len(iso_code) > 2):
            raise InvalidISO2DCountryCodeError
        
        self.postal_code_patterns[iso_code.upper()] = re.compile("^(%s)$"%pattern)
    
    def valid_postal_code(self, iso_code, postal_code):
        """
        Verify if given postal code is valid.
        
        Arguments:
        
            * iso_code (string) - 2-digit ISO 3166 country code
            * postal_code (string) - Postal code to validate.
        
        Returns:
        
            Success:
                String of matching postal code.
            
            Failure: None (or raises exception)
        """
        
        iso_code = iso_code.upper()
        
        if(len(iso_code) > 2):
            raise InvalidISO2DCountryCodeError
        
        if(iso_code not in self.postal_code_patterns):
            raise UnsupportedCountryError(iso_code)
        
        match = self.postal_code_patterns[iso_code].match(postal_code)
        if(match):
            return match.groups()[0]
        else:
            return None
    
    def valid_postal_code_global(self, postal_code):
        """
        Iterates through all known postal code patterns to find a match.
        
        NB: This can be very resource intensive. Use only if you absolutely
        don't know the country code.
        
        Arguments:
        
            * postal_code (string) - Postal code to validate.
        
        
        Returns: See .valid_postal_code()
        """
        
        for iso_code in self.postal_code_patterns.keys():
            valid_code = self.valid_postal_code(iso_code, postal_code)
            if(valid_code):
                return valid_code
        
        return None

class PostalCodeDataFileDNEError(Exception):
    def __init__(self, path):
        Exception.__init__(self, "Could not access postal code data file: %s" % path)

class InvalidISO2DCountryCodeError(Exception):
    
    def __init__(self):
        Exception.__init__(self, "Invalid 2-digit ISO 3166 country code.")
    

class UnsupportedCountryError(Exception):
    
    def __init__(self, iso_code):
        Exception.__init__(self, "Cannot validate postal codes for country: %s" % iso_code)