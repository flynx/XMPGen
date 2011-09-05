#=======================================================================

__version__ = '''0.0.01'''
__sub_version__ = '''20110905234928'''
__copyright__ = '''(c) Alex A. Naanou 2011'''


#-----------------------------------------------------------------------

import shutil, os, os.path
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



#-----------------------------------------------------------------------
# config data and defaults...

HOME_CFG='~'

SYSTEM_CFG='.'

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

THRESHOLD = 1.0/100

RATINGS = [
	##!!! the folowing need to be changed to the standard Adobe uses in Br and Lr...
	# labels...
	'yellow',
	'blue',
	# basic ratings...
	5, 4, 3, 2, 1,
]



#-----------------------------------------------------------------------
#-------------------------------------------------------------collect---
def collect(root, next_dir='fav', ext=('.jpg', '.JPG')):
	'''
	collect all the files in the topology.
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
	index the collection.

	each level represents the difference between itself and the next level.
	each level also contains the number of elements in it originally (before 
	removal of elements also contained in the next level)
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
	yield res


#----------------------------------------------------------------rate---
def rate(index, ratings=RATINGS, threshold=THRESHOLD):
	'''
	rate the indexed elements.

	this combines similar levels.

	NOTE: if the count of non-intersecting elements relative to the total 
	      number of elements is below the threshold, the level will be 
		  merged with the next. such levels are called "similar".
	'''
	# XXX not too good to buffer the whole thing but we need to go from
	#     the back...
	index = list(index)
	index.reverse()

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


#----------------------------------------------------------buildcache---
def buildcache(root, ext='.NEF'):
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


#-------------------------------------------------------------getpath---
def getpath(root, name, cache=None):
	'''
	find a file in a directory tree via cache and return it's path.

	NOTE: name should be given without an extension.
	NOTE: this ignores extensions.
	'''
	return '.'.join(cache[name].split('.')[:-1])



#-----------------------------------------------------------------------
if __name__ == '__main__':
	from optparse import OptionParser, OptionGroup

	parser = OptionParser(usage='Usage: %prog [options] [ROOT [INPUT [OUTPUT]]]')
	parser.add_option('--root',
						dest='root',
						default='.',
						help='root of the directory tree we will be working at.', 
						metavar='ROOT')
	parser.add_option('--input',
						dest='input',
						default='preview',
						help='name of directory containing previews.', 
						metavar='INPUT')
	parser.add_option('--output',
						dest='output',
						default='.',
						help='name of directory to store .XMP files. if --no-search '
						'is not set this is where we search for relevant files.', 
						metavar='OUTPUT')

	advanced = OptionGroup(parser, 'Advanced options')
	##!!!
	advanced.add_option('--no-search', 
						dest='search',
						action='store_false',
						default=True,
						help='if set, this will disable searching for RAW files, '
						'and XMPs will be stored directly in the OUTPUT directory.') 
	advanced.add_option('--use-labels', 
						dest='use_labels',
						action='store_true',
						default=False,
						help='if set, use both labels and ratings.') 
	advanced.add_option('--group-threshold', 
						dest='threshold',
						default=5,
						help='precentage of elements unique to a level below which '
						'the level will be merged with the next one.',
						metavar='THRESHOLD') 
##	advanced.add_option('--xmp-no-update', 
##						dest='xmp_update',
##						action='store_false',
##						default=True,
##						help='Not Implemented') 
	advanced.add_option('--raw-extension',
						dest='raw_ext',
						default='.NEF',
						help='use as the extension for RAW files.', 
						metavar='RAW_EXTENSION')
##	advanced.add_option('--labels',
##						dest='labels',
##						help='...', 
##						metavar='LABELS')
##	advanced.add_option('--xmp-template',
##						dest='xmp_template',
##						help='...', 
##						metavar='XMP_TEMPLATE')
	parser.add_option_group(advanced)

	(options, args) = parser.parse_args()


	ROOT = options.root
	INPUT = options.input
	OUTPUT = options.output

	THRESHOLD = float(options.threshold)/100
	RAW_EXTENSION = options.raw_ext

	if not options.use_labels:
		RATINGS = range(5, 0, -1)
	
	generate(
			rate(
				index(
					##!!! locate correct preview dirs...
					collect(os.path.join(ROOT, INPUT))), 
				ratings=RATINGS,
				threshold=THRESHOLD), 
			OUTPUT, 
			getpath=(curry(getpath, cache=buildcache(OUTPUT, RAW_EXTENSION)) 
						if options.search 
						else os.path.join))



#=======================================================================
#                                            vim:set ts=4 sw=4 nowrap :
