#=======================================================================

__version__ = '''0.0.01'''
__sub_version__ = '''20110912164910'''
__copyright__ = '''(c) Alex A. Naanou 2011'''


#-----------------------------------------------------------------------

import os, shutil
from pli.testlog import logstr
from pli.functional import curry

import xmpgen
from xmpgen import *


#-----------------------------------------------------------------------

TEST_DIR = os.path.join('test', 'preview (RAW)')
EMPTY_DIR = os.path.join('test', 'empty')
TEST_DESTINATION = 'test'


xmpgen.DEFAULT_CFG['RATINGS'][0:0] = [
	##!!! the folowing need to be changed to the standard Adobe uses in Br and Lr...
	# labels...
	'yellow',
	'blue',
]



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
	!cleanup()

	!list(collect(TEST_DIR))
	!list(rcollect(TEST_DIR))

	list(collect(TEST_DIR)) == list(rcollect(TEST_DIR))[::-1]
		-> True


	---

	bestpathmatch('ABT', ('A', 'AB', 'ABT', 'AC', 'ABD'))
		-> 'ABT'

	bestpathmatch('ABT', ('A', 'AB', 'AC', 'ABD'))
		-> 'AB'

	bestpathmatch('ABT', ('A', 'AC', 'ABD'))
		-> 'ABD'

	bestpathmatch('AT', ('AB', 'ACD', 'AT'))
		-> 'AT'

	bestpathmatch('AT', ('AB', 'ACD'))
		-> 'AB'

##	##!!! this should fail because we have two paths with same score...
##	bestpathmatch('AT', ('AB', 'AC'))


	---

	!list(index(collect(TEST_DIR)))

	# corner cases...
	list(collect('mooo'))
		-> []
	list(collect(EMPTY_DIR)) 
		-> []

	list(index([]))
		-> []
	list(rate([]))
		-> []
	list(rate(index([])))
		-> []

	generate([], 'fooo', actions=())
		-> None

	buildfilecache('fooo') 
		-> {}
##	# this will fail with a KeyError, because 'mooo' does indeed not
##	# exist in an empty cache...
##	getfilepath('fooo', 'mooo', buildfilecache('fooo'))
##		

	builddircache('fooo', 'mooo')
		-> {}
	list(getdirpaths('fooo', 'mooo', buildfilecache('fooo', 'mooo')))
		-> []

##	[ (e['total count'], len(e['items'])) for e in list(index([ [(1, 2), (4, 5), ], [(1, 2), (4, 5), (5, 6)], [(1, 2), (2, 3), (4, 5), (5, 6)], ]))]


	---

	!list(index(collect(TEST_DIR)))

	[ (e['total count'], len(e['items'])) for e in index(collect(TEST_DIR)) ]
		-> [(101, 101), (107, 6), (184, 77), (487, 303)]

##	raise SystemExit

	[ (rating, len(data)) for rating, data in dict(rate(index(collect(TEST_DIR)))).items() ]
		-> [('blue', 1), (4, 1), (5, 1), ('yellow', 1)]

	# will combine two levels...
	[ (rating, len(data)) for rating, data in dict(rate(index(collect(TEST_DIR)), threshold=10)).items() ]
		-> [('blue', 2), (5, 1), ('yellow', 1)]

	# output sums number of elements puer group...
	[ (rating, [len(i['items']) for i in data]) for rating, data in dict(rate(index(collect(TEST_DIR)), threshold=10)).items() ]
		-> [('blue', [6, 77]), (5, [303]), ('yellow', [101])]

	---

	# generate the XMP files...
	generate(rate(index(collect(TEST_DIR)), threshold=10), TEST_DESTINATION)

	# cleanup...
	cleanup()
		-> 'found and removed 487 XMP files in 1 directories.'

	---

	# generate the XMP files and put them in the same place as a
	# coresponding raw file...
	generate(rate(index(collect(TEST_DIR)), threshold=10), TEST_DESTINATION, curry(getfilepath, cache=buildfilecache(TEST_DESTINATION, )))

	# cleanup...
	cleanup()
		-> 'found and removed 487 XMP files in 2 directories.'

	---

	os.system('python xmpgen.py --root=test --no-search-output --no-search-input -m')
		-> 0

	cleanup()
		-> 'found and removed 184 XMP files in 1 directories.'

	---

	os.system('python xmpgen.py --root=test --no-search-input -m')
		-> 0

	cleanup()
		-> 'found and removed 184 XMP files in 2 directories.'

	---

	os.system('python xmpgen.py -m')
		-> 0

	cleanup()
		-> 'found and removed 199 XMP files in 3 directories.'

	---

	os.system('python xmpgen.py --rate-top-level -m')
		-> 0

	cleanup()
		-> 'found and removed 517 XMP files in 3 directories.'

	---

	os.system('python xmpgen.py --input=fooo -m')
		-> 0

	cleanup()
		-> 'found and removed 0 XMP files in 0 directories.'

	---

	os.system('python xmpgen.py --input=%s -m' % os.path.join('test', 'empty'))
		-> 0

	cleanup()
		-> 'found and removed 0 XMP files in 0 directories.'

	---

	os.system('python xmpgen.py --root=%s -m' % os.path.join('test', 'empty'))
		-> 0

	cleanup()
		-> 'found and removed 0 XMP files in 0 directories.'

	---

	# XXX same as above...
	os.system('python xmpgen.py --input=fooo --no-search-input -m')
		-> 0

	cleanup()
		-> 'found and removed 0 XMP files in 0 directories.'

	---

	os.system('python xmpgen.py --input=fooo --no-search-output -m')
		-> 0

	cleanup()
		-> 'found and removed 0 XMP files in 0 directories.'

	---

	os.system('python xmpgen.py --input=fooo --no-search-output --no-search-input -m')
		-> 0

	cleanup()
		-> 'found and removed 0 XMP files in 0 directories.'

''', only_errors=False)





#=======================================================================
#                                            vim:set ts=4 sw=4 nowrap :
