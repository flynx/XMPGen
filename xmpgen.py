#=======================================================================

__version__ = '''0.0.01'''
__sub_version__ = '''20110908011855'''
__copyright__ = '''(c) Alex A. Naanou 2011'''


#-----------------------------------------------------------------------

import shutil, os, os.path
from itertools import chain
from pli.functional import curry


#-----------------------------------------------------------------------
#
# actions:
# 	- collect data		- DONE
# 	- build index		- DONE
# 	- normalize index	- DONE
# 	- map ratings		- DONE
# 	- generate			- DONE
#
#
#-----------------------------------------------------------------------
# helpers...
#--------------------------------------------------------------locate---
def locate(name, locations=(), default=None):
	'''
	locate an entity in locations and if none are available use a default.

	NOTE: this will read the contents of the file.
	'''
	for l in locations:
		try:
			return file(os.path.join(l, name), 'r').read()
		except IOError:
			continue
	return default


#------------------------------------------------------------skiplast---
def skiplast(iterable):
	'''
	skip last element of iterable
	'''
	prev = None
	for e in iterable:
		if prev is not None:
			yield e
		prev = e
	if prev is not None:
		yield e
	

#-----------------------------------------------------------------------
# config data and defaults...

HOME_CFG = '~'

SYSTEM_CFG = '.'

ROOT_DIR = '.'
INPUT_DIR = 'preview (RAW)'
### NOTE: we do not need a default aoutput dir as it will default to
### 		ROOT_DIR...
##OUTPUT_DIR = ROOT_DIR
TRAVERSE_DIR = 'fav'

RAW_EXTENSION = '.NEF'

XMP_TEMPLATE_NAME = 'TEMPLATE.XMP'

XMP_TEMPLATE = locate(XMP_TEMPLATE_NAME, (HOME_CFG, SYSTEM_CFG), default='''\
<x:xmpmeta xmlns:x="adobe:ns:meta/">
	<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
		<rdf:Description rdf:about="" xmlns:xap="http://ns.adobe.com/xap/1.0/">
			<xap:CreatorTool>XMPGen</xap:CreatorTool>
			<xap:Rating>%(rating)s</xap:Rating>
			<xap:Label>%(label)s</xap:Label>
		</rdf:Description>
	</rdf:RDF>
</x:xmpmeta>
''')

THRESHOLD = 5

RATINGS = [
	# labels...
	##!!! add default labels...
	# basic ratings...
	5, 4, 3, 2, 1,
]



#-----------------------------------------------------------------------
#-------------------------------------------------------------collect---
def collect(root, next_dir=TRAVERSE_DIR, ext=('.jpg', '.JPG')):
	'''
	generator to collect all the files in the topology.
	'''
	for r, dirs, files in os.walk(root):
		# filter files...
		yield [ f for f in files if True in [ f.endswith(e) for e in ext ]]
		# filter dirs...
		if next_dir in dirs:
			dirs[:] = [next_dir]
		else:
			del dirs[:] 


#---------------------------------------------------------------index---
def index(collection):
	'''
	generator to index the collection.

	each level represents the difference between itself and the next level.
	each level also contains the number of elements in it originally (before 
	removal of elements also contained in the next level)

	NOTE: duplicate file names will be merged.
	'''
	prev = res = None
	for level in collection:
		cur = set(level)
		if prev is not None:
			prev.difference_update(cur)
		prev = cur
		if res is not None:
			# return the previous res...
			# NOTE: this is done so as to avoid modifying the data that
			#		the user already has.
			yield res
		res = {
			'total count': len(level),
			'items': cur, 
		}
	if res is None:
		# the collection is empty, thus we need to return nuthing.
		return
	yield res


#----------------------------------------------------------------rate---
def rate(index, ratings=RATINGS, threshold=THRESHOLD):
	'''
	generator to rate the indexed elements.

	this combines similar levels.

	NOTE: if the count of non-intersecting elements relative to the total 
	      number of elements is below the threshold, the level will be 
		  merged with the next. such levels are called "similar".
	'''
	# XXX not too good to buffer the whole thing but we need to go from
	#     the back...
	index = list(index)
	index.reverse()
	threshold = float(threshold)/100

	i = 0
	buf = ()
	for level in index:
		buf += (level,)
		if float(len(level['items']))/level['total count'] > threshold:
			yield ratings[i], buf
			buf = ()
			i += 1


#------------------------------------------------------------generate---
def generate(ratings, root, getpath=os.path.join, template=XMP_TEMPLATE):
	'''
	generate XMP files.
	'''
	for rating, data in ratings:
		if type(rating) in (str, unicode):
			label = rating
			rating = 5
		else:
			label = ''
			rating = rating
		xmp_data = XMP_TEMPLATE % {'rating': rating, 'label': label}
		for name in reduce(list.__add__, [ list(s['items']) for s in data ]):
			##!!! check is file already exists...
			file(getpath(root, '.'.join(name.split('.')[:-1])) + '.XMP', 'w').write(xmp_data)


#------------------------------------------------------buildfilecache---
def buildfilecache(root, ext=RAW_EXTENSION):
	'''
	build a cache of all files in a tree with an extension ext.

	the cache is indexed by file name without extension and contains full paths.

	NOTE: if this finds more than one file with same name in the sub tree it will fail.
	'''
	res = {}
	for path, _, files in os.walk(root): 
		for f in files:
			if f.endswith(ext):
				if f in res:
					raise TypeError, 'file %s%s exists in two locations!' % (f, ext)
				res['.'.join(f.split('.')[:-1])] = os.path.join(path, f)
	return res


#---------------------------------------------------------getfilepath---
def getfilepath(root, name, cache=None):
	'''
	find a file in a directory tree via cache and return it's path.

	NOTE: name should be given without an extension.
	NOTE: this ignores extensions.
	'''
	return '.'.join(cache[name].split('.')[:-1])


#-------------------------------------------------------builddircache---
def builddircache(root, name):
	'''
	build directory cache.

	NOTE: for simple name patterns this will return a single item.
	'''
	res = {}
	for path, dirs, _ in os.walk(root): 
		for d in dirs:
			if d == name:
				if d in res:
					res[d] += [os.path.join(path, d)]
				else:
					res[d] = [os.path.join(path, d)]
	return res


#----------------------------------------------------------getdirpath---
def getdirpaths(root, name, cache=None):
	'''
	generator to yield directory cache elements by name.
	'''
	if name not in cache:
		raise TypeError, 'directory "%s" does not exist in tree %s.' % (name, root)
##	# make this compatible with name patterns...
##	##!!! this seams to yield odd results -- fails with --search-input...
##	for d in chain(cache[n] for n in (k for k in cache.keys() if k == name)):
	for d in cache[name]:
		yield d


#-----------------------------------------------------------------------
if __name__ == '__main__':
	from optparse import OptionParser, OptionGroup

	##!!! move all the defaults from here to the constants section...
	parser = OptionParser(
						usage='Usage: %prog [options]',
						version='%prog ' + __version__)
	parser.add_option('--root',
						dest='root',
						default=ROOT_DIR,
						help='root of the directory tree we will be working at (default: "%default").', 
						metavar='ROOT')
	parser.add_option('--input',
						dest='input',
						default=INPUT_DIR,
						help='name of directory containing previews (default: "%default").', 
						metavar='INPUT')
	parser.add_option('--output',
						dest='output',
						help='name of directory to store .XMP files. if --no-search '
						'is not set this is where we search for relevant files (default: ROOT).', 
						metavar='OUTPUT')

	advanced = OptionGroup(parser, 'Advanced options')
	advanced.add_option('--rate-top-level', 
						dest='rate_top_level',
						action='store_true',
						default=False,
						help='if set, do not rate top level previews.')
	advanced.add_option('--search-input', 
						dest='search_input',
						action='store_true',
						default=False,
						help='if set, this will enable searching for input directories, '
						'otherwise ROOT/INPUT will be used directly.\n'
						'NOTE: this will find all matching INPUT directories, '
						'including nested ones.') 
	advanced.add_option('--no-search-output', 
						dest='search_output',
						action='store_false',
						default=True,
						help='if set, this will disable searching for RAW files, '
						'and XMPs will be stored directly in the OUTPUT directory.') 
	advanced.add_option('--group-threshold', 
						dest='threshold',
						default=THRESHOLD,
						help='precentage of elements unique to a level below which '
						'the level will be merged with the next one (default: "%default").',
						metavar='THRESHOLD') 
	##!!! we need to be able to update or ignore existing xmp files, curently they will be overwritten...
##	advanced.add_option('--xmp-no-update', 
##						dest='xmp_update',
##						action='store_false',
##						default=True,
##						help='Not Implemented') 
	advanced.add_option('--traverse-dir-name',
						dest='traverse_dir',
						default=TRAVERSE_DIR,
						help='directory used to traverse to next level (default: "%default").', 
						metavar='TRAVERSE_DIR')
	advanced.add_option('--raw-extension',
						dest='raw_ext',
						default=RAW_EXTENSION,
						help='use as the extension for RAW files (default: "%default").', 
						metavar='RAW_EXTENSION')
##	advanced.add_option('--labels',
##						dest='labels',
##						help='...', 
##						metavar='LABELS')
	advanced.add_option('--xmp-template',
						dest='xmp_template',
						help='use XMP_TEMPLATE instead of the internal template.', 
						metavar='XMP_TEMPLATE')
	advanced.add_option('--use-labels', 
						dest='use_labels',
						action='store_true',
						default=False,
						help='if set, use both labels and ratings.') 

##	advanced.add_option('--save-configuration', 
##						dest='save_config',
##						action='store_true',
##						default=False,
##						help='if set, write current command-line options to ~/.xmpgen '
##						'file to be used as default.\n'
##						'NOTE: the only option that will not be written is --save-configuration, obviously.') 

	parser.add_option_group(advanced)

	options, args = parser.parse_args()

	# prune some data...
	output = options.output if options.output else options.root
	XMP_TEMPLATE = file(options.xmp_template, 'r').read() if options.xmp_template else XMP_TEMPLATE
	if not options.use_labels:
		RATINGS = range(5, 0, -1)

	# do the actaual dance...
	generate(
			rate(
				# chose weather we need to skip the last element...
				(iter if options.rate_top_level else skiplast)(
					index(
						# use ROOT/INPUT...
						collect(os.path.join(options.root, options.input), options.traverse_dir) 
							if not options.search_input 
							# locate correct preview dirs...
							##!!! chaining is wrong here. we need to zip and then  merge each level...
							##!!! $*#%$^#%, why is there no option to padd the shorter elements of zip?!!!
							else chain(*(collect(d, options.traverse_dir) 
											for d 
											in getdirpaths(
													options.root, 
													options.input, 
													builddircache(options.root, options.input)))))), 
				ratings=RATINGS,
				threshold=options.threshold), 
			output, 
			# find a location for each output file...
			getpath=(curry(getfilepath, cache=buildfilecache(output, options.raw_ext)) 
						if options.search_output 
						# just write to ROOT...
						else os.path.join),
			template=XMP_TEMPLATE)



#=======================================================================
#                                            vim:set ts=4 sw=4 nowrap :
