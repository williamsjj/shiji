#!/usr/bin/python
####################################################################
# FILENAME: setup.py
# PROJECT: Shiji API
# DESCRIPTION: Install Shiji API module.
#
#
#
####################################################################
# (C)2016 DigiTar Inc.
# Licensed under the MIT License.
####################################################################

from setuptools import setup, find_packages
 
version = '1.0.15'
 
setup(name='shiji',
      version=version,
      description="Shiji Web API Framework",
      long_description="""Shiji makes it easy to build HTTP & RESTful APIs using Twisted Web.""",
      classifiers=[],
      keywords=['rest','api','twisted','web','json','framework'],
      author='DigiTar Inc.',
      author_email='support@digitar.com',
      url='https://github.com/williamsjj/shiji',
      license='MIT License',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests', 'old*']),
      package_data={'' : ['*.mako','utilities/utility_templates/*']},
      zip_safe=False,
      install_requires=["Twisted>=15.0",
                        "simplejson>=2.0",
                        "Mako>=0.3",
                        "Markdown>=2.0",
                        "lxml>=3.0.1"],
      entry_points="""
      [console_scripts]
      shiji_admin = shiji.utilities.shiji_admin:main
      shijid = shiji.utilities.shijid:main
      """
    )
