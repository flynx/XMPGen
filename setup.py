#!/usr/bin/env python
#=======================================================================

__version__ = '''0.1.12'''
__sub_version__ = '''20110929161924'''
__copyright__ = '''(c) Alex A. Naanou 2003'''


#-----------------------------------------------------------------------
__long_doc__ = file('README.rst').read()
__doc__ = __long_doc__.split('\n\n', 1)[0]

print __doc__

#-----------------------------------------------------------------------
__classifiers__ = '''\
Development Status :: 3 - Alpha
Topic :: Utilities
License :: OSI Approved :: BSD License
Natural Language :: English
Programming Language :: Python
Environment :: Console
'''

#-----------------------------------------------------------------------
from setuptools import setup
import os.path as os_path
import sys
import py2exe

import xmpgen
__pkg_version__ = xmpgen.__version__

license = 'BSD Licence.'


#-----------------------------------------------------------------------
setup(
	name = 'xmpgen',
	version = __pkg_version__,
	description = __doc__,
	long_description = __long_doc__,
	author = 'Alex A. Naanou',
	author_email = 'alex.nanou@gmail.com',
	url = 'https://github.com/flynx/XMPGen',
	license = license,
	platforms = ['any'],
	classifiers = filter(None, __classifiers__.split("\n")),

	install_requires = ['pli'],
	##!!! this needs to be done...
##	dependency_links = [],

	include_package_data = True,

	packages = [],
	# NOTE: xmpgen_legacy is for python version < 2.6
	py_modules = ['xmpgen', 'xmpgen_legacy'],

	entry_points = {
		'console_scripts': [
			'xmpgen = xmpgen:run'
		],
	},
	
	# py2exe stuff...
	options = {"py2exe": {
					'compressed': 1,
##					'optimize': 2,
					'bundle_files': 2,
##					'packages': 'encodings',
					}},
	console = ['xmpgen.py']
	)



#=======================================================================
#                                            vim:set ts=4 sw=4 nowrap :
