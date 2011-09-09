#!/bin/env python
#=======================================================================

__version__ = '''0.1.04'''
__sub_version__ = '''20110909172345'''
__copyright__ = '''(c) Alex A. Naanou 2011'''


#-----------------------------------------------------------------------

import shutil, sys, os, os.path
from itertools import chain, imap, islice
import simplejson

from pli.functional import curry, rcurry

if sys.version_info < (2, 6):
	from xmpgen_legacy import izip_longest
else:
	from itertools import izip_longest



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

XMP_TEMPLATE_NAME = 'TEMPLATE.XMP'
CONFIG_NAME = '.xmpgen'

DEFAULT_CFG = {
	'ROOT_DIR': '.',
	'INPUT_DIR': 'preview (RAW)',
	# NOTE: we do not need a default aoutput dir as it will default to
	# 		ROOT_DIR...
	#'OUTPUT_DIR': None,
	'TRAVERSE_DIR': 'fav',

	'RAW_EXTENSION': '.NEF',
	'THRESHOLD': 5,
	'RATINGS': [
		# basic ratings...
		5, 4, 3, 2, 1,
		# labels...
		# XXX add default labels...
	],

	'XMP_TEMPLATE': '''\
<x:xmpmeta xmlns:x="adobe:ns:meta/">
	<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
		<rdf:Description rdf:about="" xmlns:xap="http://ns.adobe.com/xap/1.0/">
			<xap:CreatorTool>XMPGen</xap:CreatorTool>
			<xap:Rating>%(rating)s</xap:Rating>
			<xap:Label>%(label)s</xap:Label>
		</rdf:Description>
	</rdf:RDF>
</x:xmpmeta>''',

	'RATE_TOP_LEVEL': False,
	'SEARCH_INPUT': True,
	'SEARCH_OUTPUT': True,
	'VERBOSITY': 1,
	'USE_LABELS': False,
}


#-----------------------------------------------------------------------
#------------------------------------------------------------rcollect---
def rcollect(root, next_dir=DEFAULT_CFG['TRAVERSE_DIR'], collect_base=True, ext=('.jpg', '.JPG')):
	'''
	generator to collect all the files in the topology.
	'''
	for r, dirs, files in os.walk(root):
		if collect_base:
			# filter files...
			yield [ f for f in files if True in [ f.endswith(e) for e in ext ]]
		else:
			collect_base = True
		# filter dirs...
		if next_dir in dirs:
			dirs[:] = [next_dir]
		else:
			del dirs[:] 


#-------------------------------------------------------------collect---
def collect(root, next_dir=DEFAULT_CFG['TRAVERSE_DIR'], collect_base=True, ext=('.jpg', '.JPG')):
	'''
	same as collect, but does its work bottom-down.
	'''
	##!!! STUB
	data = list(rcollect(root, next_dir, collect_base, ext))
	for e in data[::-1]:
		yield e


#---------------------------------------------------------------index---
def index(collection):
	'''
	generator to index the collection.

	each level represents the difference between itself and the previous level.
	each level also contains the original number of elements.

	NOTE: duplicate file names will be merged.
	'''
	prev = None
	for level in collection:
		cur = set(level)
		if prev is not None:
			cur.difference_update(set(prev))
		prev = level
		yield {
			'total count': len(level),
			'items': cur, 
		}



#----------------------------------------------------------------rate---
def rate(index, ratings=DEFAULT_CFG['RATINGS'], threshold=DEFAULT_CFG['THRESHOLD']):
	'''
	generator to rate the indexed elements.

	this combines similar levels.

	NOTE: if the count of non-intersecting elements relative to the total 
	      number of elements is below the threshold, the level will be 
		  merged with the next. such levels are called "similar".
	'''
	threshold = float(threshold)/100

	i = 0
	buf = ()
	for level in index:
		buf += (level,)
		if float(len(level['items']))/level['total count'] <= threshold:
			continue
		yield ratings[i], buf
		buf = ()
		i += 1



#-----------------------------------------------------------------------
#--------------------------------------------------------action_dummy---
def action_dummy(path, rating, label, data):
	'''
	'''
	return True


#----------------------------------------------------------filewriter---
def action_filewriter(path, rating, label, data):
	'''
	'''
	##!!! check is file already exists...
	file(path, 'w').write(data)
	return True


#-------------------------------------------------------action_logger---
def action_logger(path, rating, label, data, verbosity=1):
	'''
	'''
	if verbosity == 1:
		print '.',
	elif verbosity == 2:
		print '%s (%s, %s)' % (path, rating, label)
	return True


#--------------------------------------------------------action_break---
def action_break(path, rating, label, data):
	'''
	'''
	return False


#------------------------------------------------------------generate---
def generate(ratings, root, getpath=os.path.join, actions=(action_filewriter,), template=DEFAULT_CFG['XMP_TEMPLATE']):
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
		xmp_data = template % {'rating': rating, 'label': label}
		for name in reduce(list.__add__, [ list(s['items']) for s in data ]):
			for action in actions:
				if action is action_dummy:
					continue
				if not action(getpath(root, '.'.join(name.split('.')[:-1])) + '.XMP', rating, label, xmp_data):
					break



#-----------------------------------------------------------------------
#------------------------------------------------------buildfilecache---
def buildfilecache(root, ext=DEFAULT_CFG['RAW_EXTENSION'], skip_dirs=(DEFAULT_CFG['INPUT_DIR'],)):
	'''
	build a cache of all files in a tree with an extension ext.

	the cache is indexed by file name without extension and contains full paths.

	NOTE: if this finds more than one file with same name in the sub tree it will fail.
	'''
	res = {}
	for path, dirs, files in os.walk(root): 
		if len(skip_dirs) > 0:
			dirs[:] = list(set(dirs).difference(skip_dirs))	
		for f in files:
			if f.endswith(ext):
				base = '.'.join(f.split('.')[:-1])
				if base in res:
					raise TypeError, 'file %s%s exists in two locations!' % (f, ext)
				res[base] = os.path.join(path, f)
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
#---------------------------------------------------------load_config---
def load_config(config, default_cfg=DEFAULT_CFG):
	'''
	'''
	# NOTE: this does not like empty configurations files...
	user_config = simplejson.loads(locate(CONFIG_NAME, (HOME_CFG, SYSTEM_CFG), default='{}'))

	config = default_cfg.copy()
	config.update(user_config)

	config['XMP_TEMPLATE'] = locate(
			XMP_TEMPLATE_NAME, 
			(HOME_CFG, SYSTEM_CFG), 
			default=config['XMP_TEMPLATE'])
	return config


#--------------------------------------------------------load_options---
def load_options(config, default_cfg=DEFAULT_CFG):
	'''
	'''
	from optparse import OptionParser, OptionGroup

	parser = OptionParser(
						usage='Usage: %prog [options]',
						version='%prog ' + __version__,
						epilog=None)
	parser.add_option('--root',
						dest='root',
						default=config['ROOT_DIR'],
						help='root of the directory tree we will be working at (default: "%default").', 
						metavar='ROOT')
	parser.add_option('--input',
						dest='input',
						default=config['INPUT_DIR'],
						help='name of directory containing previews (default: "%default").\n'
						'NOTE: this directory tree can not be used for OUTPUT.', 
						metavar='INPUT')
	parser.add_option('--output',
						dest='output',
						help='name of directory to store .XMP files. if --no-search '
						'is not set this is where we search for relevant files (default: ROOT).', 
						metavar='OUTPUT')
	# verbosity level...
	parser.add_option('-v', '--verbose',
						dest='verbosity',
						action='store_const',
						const=2,
						default=config['VERBOSITY'],
						help='increase output verbosity.')
	parser.add_option('-q', '--quiet',
						dest='verbosity',
						action='store_const',
						const=0,
						default=config['VERBOSITY'],
						help='decrease output verbosity.')
	parser.add_option('-m', '--mute',
						dest='verbosity',
						action='store_const',
						const=-1,
						default=config['VERBOSITY'],
						help='mute output.')

	advanced = OptionGroup(parser, 'Advanced options')
	advanced.add_option('--rate-top-level', 
						dest='rate_top_level',
						action='store_true',
						default=config['RATE_TOP_LEVEL'],
						help='if set, also rate top level previews.')
	advanced.add_option('--no-search-input', 
						dest='search_input',
						action='store_false',
						default=config['SEARCH_INPUT'],
						help='if set, this will disable searching for input directories, '
						'otherwise ROOT/INPUT will be used directly.\n'
						'NOTE: this will find all matching INPUT directories, '
						'including nested ones.') 
	advanced.add_option('--no-search-output', 
						dest='search_output',
						action='store_false',
						default=config['SEARCH_OUTPUT'],
						help='if set, this will disable searching for RAW files, '
						'and XMPs will be stored directly in the OUTPUT directory.') 
	advanced.add_option('--group-threshold', 
						dest='threshold',
						default=config['THRESHOLD'],
						help='percentage of elements unique to a level below which '
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
						default=config['TRAVERSE_DIR'],
						help='directory used to traverse to next level (default: "%default").', 
						metavar='TRAVERSE_DIR')
	advanced.add_option('--raw-extension',
						dest='raw_ext',
						default=config['RAW_EXTENSION'],
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
						default=config['USE_LABELS'],
						help='if set, use both labels and ratings.') 

	advanced.add_option('--dry-run',
						dest='dry_run',
						action='store_true',
						default=False,
						help='run but do not create any files.')

	parser.add_option_group(advanced)

	configuration = OptionGroup(parser, 'Configuration options')
	configuration.add_option('--config-print', 
						dest='config_print',
						action='store_true',
						default=False,
						help='print current configuration and exit.')
	configuration.add_option('--config-defaults-print', 
						dest='config_defaults_print',
						action='store_true',
						default=False,
						help='print current configuration and exit.')

	parser.add_option_group(configuration)

	options, args = parser.parse_args()

	# be polite and save the originla config data...
	config = config.copy()

	# prune and write the data...
	config.update({
			'ROOT_DIR': options.root,
			'INPUT_DIR': options.input,
			'OUTPUT_DIR': options.output if options.output else options.root,
			'TRAVERSE_DIR': options.traverse_dir,
			'RAW_EXTENSION': options.raw_ext,
			'THRESHOLD': options.threshold,
			'XMP_TEMPLATE': file(options.xmp_template, 'r').read() 
								if options.xmp_template 
								else config['XMP_TEMPLATE'],
			'RATE_TOP_LEVEL': options.rate_top_level,
			'SEARCH_INPUT': options.search_input,
			'SEARCH_OUTPUT': options.search_output,
			'VERBOSITY': options.verbosity,
			'USE_LABELS': options.use_labels,
			})
	if not options.use_labels:
		config['RATINGS'] = range(5, 0, -1)
	
	# configuration stuff...
	# sanity check...
	if True in (options.config_defaults_print, options.config_print):
		print_prefix = False
		if len([ s for  s in  (options.config_defaults_print, options.config_print) if s]) > 1:
			print_prefix = True
		if options.config_print:
			if print_prefix:
				print 'Current Configuration:'
			print simplejson.dumps(config, sort_keys=True, indent=4)
			print
		if options.config_defaults_print:
			if print_prefix:
				print 'Default Configuration:'
			print simplejson.dumps(default_cfg, sort_keys=True, indent=4)
			print
		raise SystemExit

	return config, options



#-----------------------------------------------------------------------
#-----------------------------------------------------------------run---
def run():
	# setup config data...
	config, runtime_options = load_options(load_config(DEFAULT_CFG))

	# cache some names...
	output = config['OUTPUT_DIR']
	root = config['ROOT_DIR']
	input = config['INPUT_DIR']
	traverse_dir = config['TRAVERSE_DIR']
	threshold = config['THRESHOLD']
	raw_ext = config['RAW_EXTENSION']
	rate_top_level = config['RATE_TOP_LEVEL']
	search_input = config['SEARCH_INPUT']
	search_output = config['SEARCH_OUTPUT']
	verbosity = config['VERBOSITY']

	# runtime options...
	dry_run = runtime_options.dry_run

	# prepare to count created files...
	files_written = [0]
	def action_count(*p, **n):
		files_written[0] += 1
		return True

	# do the actaual dance...
	res = generate(
		rate(
			index(
				# chose weather we need to skip the last element...
					collect(os.path.join(root, input), traverse_dir, rate_top_level) 
						if not search_input 
						# locate correct preview dirs...
						else (reduce(list.__add__, l) 
									for l 
									in izip_longest(fillvalue=[], *(collect(d, traverse_dir, rate_top_level) 
										for d 
										in getdirpaths(
												root, 
												input, 
												builddircache(root, input)))))), 
			ratings=config['RATINGS'],
			threshold=threshold), 
		output, 
		# find a location for each output file...
		getpath=(curry(getfilepath, cache=buildfilecache(output, raw_ext, (input,))) 
					if search_output 
					# just write to ROOT...
					else os.path.join),
		actions=(
			curry(action_logger, verbosity=verbosity),
			action_break if dry_run else action_dummy,
			action_filewriter,
			action_count,
		),
		template=config['XMP_TEMPLATE'])

	if verbosity >= 0:
		if verbosity == 1:
			print
		print 'Written %s files.' % files_written[0]

	return res

	

#-----------------------------------------------------------------------
if __name__ == '__main__':
	run()



#=======================================================================
#                                            vim:set ts=4 sw=4 nowrap :
