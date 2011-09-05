#=======================================================================

__version__ = '''0.0.01'''
__sub_version__ = '''20110905185119'''
__copyright__ = '''(c) Alex A. Naanou 2011'''


#-----------------------------------------------------------------------

import os, shutil
from pli.testlog import logstr
from pli.functional import curry

from xmpgen import collect, index, rate, generate, getpath, buildcache


#-----------------------------------------------------------------------

TEST_DIR = os.path.join('test', 'preview')
TEST_DESTINATION = 'test'



#-----------------------------------------------------------------------
# remove all generated XMP files...
def cleanup(path=TEST_DESTINATION):
	i = 0
	d = 0
	found = False
	for p, _, files in os.walk(TEST_DESTINATION):
		for f in files:
			if f.endswith('.XMP'):
				if not found:
					found = True
				os.remove(os.path.join(p, f))
				i += 1
		if found:
			d += 1
			found = False
	return 'found and removed %s XMP files in %s directories.' % (i, d)


#-----------------------------------------------------------------------

logstr('''
	![ l for l in collect(TEST_DIR) ]


	[ (e['total count'], len(e['items'])) for e in index(collect(TEST_DIR)) ]
		-> [(487, 303), (184, 77), (107, 6), (101, 101)]


	[ (rating, len(data)) for rating, data in dict(rate(index(collect(TEST_DIR)))).items() ]
		-> [('blue', 1), (4, 1), (5, 1), ('yellow', 1)]

	# will combine two levels...
	[ (rating, len(data)) for rating, data in dict(rate(index(collect(TEST_DIR)), threshold=1.0/10)).items() ]
		-> [('blue', 2), (5, 1), ('yellow', 1)]

	# output sums number of elements puer group...
	[ (rating, [len(i['items']) for i in data]) for rating, data in dict(rate(index(collect(TEST_DIR)), threshold=1.0/10)).items() ]
		-> [('blue', [6, 77]), (5, [303]), ('yellow', [101])]

	---

	# generate the XMP files...
	generate(rate(index(collect(TEST_DIR)), threshold=1.0/10), TEST_DESTINATION)

	# cleanup...
	cleanup()
		-> 'found and removed 487 XMP files in 1 directories.'

	---

	# generate the XMP files and put them in the same place as a
	# coresponding raw file...
	generate(rate(index(collect(TEST_DIR)), threshold=1.0/10), TEST_DESTINATION, curry(getpath, cache=buildcache(TEST_DESTINATION)))

	# cleanup...
	cleanup()
		-> 'found and removed 487 XMP files in 2 directories.'

''')





#=======================================================================
#                                            vim:set ts=4 sw=4 nowrap :
