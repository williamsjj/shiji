# ###################################################################
# FILENAME: test_i18n.py
# PROJECT: 
# DESCRIPTION: Test internationalization support
#
#
# $Id$
# ###################################################################
# (C)2015 DigiTar Inc.
# Licensed under the MIT License.
# ###################################################################
import os
from twisted.trial import unittest
from shiji.i18n import postal_code_validator

class PostalCodeValidatorTests(unittest.TestCase):
    "Postal code validator tests."
    
    def setUp(self):
        script_path = os.path.dirname(os.path.realpath(__file__))
        self.fn_postal_data = "%s/sample_cldr_data/postalCodeData.xml" % script_path
        
        self.sample_postal_data = {"GB" : """GIR[ ]?0AA|((AB|AL|B|BA|BB|BD|BH|BL|BN|BR|BS|BT|CA|CB|CF|CH|CM|CO|CR|CT|CV|CW|DA|DD|DE|DG|DH|DL|DN|DT|DY|E|EC|EH|EN|EX|FK|FY|G|GL|GY|GU|HA|HD|HG|HP|HR|HS|HU|HX|IG|IM|IP|IV|JE|KA|KT|KW|KY|L|LA|LD|LE|LL|LN|LS|LU|M|ME|MK|ML|N|NE|NG|NN|NP|NR|NW|OL|OX|PA|PE|PH|PL|PO|PR|RG|RH|RM|S|SA|SE|SG|SK|SL|SM|SN|SO|SP|SR|SS|ST|SW|SY|TA|TD|TF|TN|TQ|TR|TS|TW|UB|W|WA|WC|WD|WF|WN|WR|WS|WV|YO|ZE)(\d[\dA-Z]?[ ]?\d[ABD-HJLN-UW-Z]{2}))|BFPO[ ]?\d{1,4}}"""
                                  }
        
        self.good_postal_codes = {"GB" : "DN55 1PT",
                                  "DE" : "39130",
                                  "JP" : "196-0025"}
        
        
        self.bad_postal_codes = {"GB" : "DN55 XPT",
                                 "DE" : "39x30",
                                 "JP" : "196-00x5"}
    
    
    def test_load_country_ok(self):
        """Verify loading valid country postal code data."""
        validator = postal_code_validator.PostalCodeValidator()
        validator.load_country("GB", self.sample_postal_data["GB"])
        self.assertTrue(validator.valid_postal_code("GB", self.good_postal_codes["GB"]))
    
    def test_load_country_invalid_iso_code(self):
        """Verify loading a non-2-digit country code fails."""
        validator = postal_code_validator.PostalCodeValidator()
        self.assertRaises(postal_code_validator.InvalidISO2DCountryCodeError,
                          validator.load_country,
                          "GBX",
                          self.sample_postal_data["GB"])
    
    def test_supported_countries(self):
        """Verify supported countries returns the correct number."""
        validator = postal_code_validator.PostalCodeValidator()
        validator.load_country("GB", self.sample_postal_data["GB"])
        validator.load_country("DE", self.sample_postal_data["GB"])
        validator.load_country("JP", self.sample_postal_data["GB"])
        
        self.assertEqual(len(validator.supported_countries()), 3)
        for country in ["GB", "DE", "JP"]:
            self.assertTrue(country in validator.supported_countries())
    
    def test_load_country_data_from_xml_ok(self):
        """Verify loading postal data from CLDR postalCodeData.xml formatted file."""
        validator = postal_code_validator.PostalCodeValidator(self.fn_postal_data)
        self.assertTrue(len(validator.postal_code_patterns.keys()) > 3)
        
    def test_load_country_data_from_xml_file_dne(self):
        """Verify attempting to load a non-existent postal data file raises PostalCodeDataFileDNEError."""
        self.assertRaises(postal_code_validator.PostalCodeDataFileDNEError,
                          postal_code_validator.PostalCodeValidator,
                          self.fn_postal_data+"garbage")
    
    def test_valid_postal_code_ok(self):
        """Verify validating a good postal code succeeds."""
        validator = postal_code_validator.PostalCodeValidator(self.fn_postal_data)
        for country in self.good_postal_codes:
            self.assertEqual(validator.valid_postal_code(country, self.good_postal_codes[country]),
                             self.good_postal_codes[country])
    
    def test_invalid_postal_code_fails(self):
        """Verify validating a bad postal code fails."""
        validator = postal_code_validator.PostalCodeValidator(self.fn_postal_data)
        for country in self.bad_postal_codes:
            self.assertEqual(validator.valid_postal_code(country, self.bad_postal_codes[country]),
                             None)
    
    def test_valid_postal_code_invalid_country(self):
        """Verify validating a postal code with an invalid country code."""
        validator = postal_code_validator.PostalCodeValidator(self.fn_postal_data)
        self.assertRaises(postal_code_validator.UnsupportedCountryError,
                          validator.valid_postal_code,
                          "ZZ",
                          "doesn't matter")
    
    def test_valid_postal_code_unsupported_country(self):
        """Verify validating a postal code for an unsupported country fails."""
        validator = postal_code_validator.PostalCodeValidator(self.fn_postal_data)
        self.assertRaises(postal_code_validator.InvalidISO2DCountryCodeError,
                          validator.valid_postal_code,
                          "abc",
                          "doesn't matter")
    
    def test_valid_postal_code_global_ok(self):
        """Verify validating a good postal code without country code succeeds."""
        # YY = Mayotte, valid postal code is 97660
        validator = postal_code_validator.PostalCodeValidator(self.fn_postal_data)
        self.assertEqual(validator.valid_postal_code_global("97660"),
                         "97660")
    
    def test_invalid_postal_code_global_fails(self):
        """Verify validating a globally unknown postal code without country code fails."""
        validator = postal_code_validator.PostalCodeValidator(self.fn_postal_data)
        self.assertEqual(validator.valid_postal_code_global("97x60"),
                         None)
    