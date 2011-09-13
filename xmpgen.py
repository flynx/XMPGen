#!/bin/env python
#=======================================================================

__version__ = '''0.1.04'''
__sub_version__ = '''20110913124534'''
__copyright__ = '''(c) Alex A. Naanou 2011'''


#-----------------------------------------------------------------------

import shutil, sys, os, os.path
from itertools import chain, imap, islice
import simplejson

from pli.functional import curry, rcurry
from pli.logictypes import ANY

if sys.version_info < (2, 6):
	from xmpgen_legacy import izip_longest
else:
	from itertools import izip_longest



#-----------------------------------------------------------------------
#
#
#-----------------------------------------------------------------------
# helpers...
#----------------------------------------------------------------join---
def join(*p, **n):
	'''
	'''
	n.pop('path', None)
	return os.path.join(*p, **n)
	

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
	'SKIP': ['preview (RAW)',],

	# for available options see: HANDLE_OVERFLOW_OPTIONS
	'HANDLE_OVERFLOW': 'merge-bottom',
}

HANDLE_OVERFLOW_OPTIONS = {
	'skip-top': None,
	'skip-bottom': None,
	'merge-bottom': None,
	'merge-top': None,
	'increase-threshold': None,
	'growing-threshold': None,
	'use-labels': None,
}


#-----------------------------------------------------------------------
#----------------------------------------------------load_commandline---
def load_commandline(config, default_cfg=DEFAULT_CFG):
	'''
	load configuration data from command-line arguments.
	'''
	from optparse import OptionParser, OptionGroup

	parser = OptionParser(
						usage='Usage: %prog [options]',
						version='%prog ' + __version__,
						epilog='NOTEs: xmpgen will overwrite existing .XMP files (will be fixed soon). '
						'xmpgen will get confused when processing a large archive '
						'containing sets of different but identically named files (will be fixed soon). '
						'xmpgen will search for both INPUT and OUTPUT so explicit declaration is needed '
						'onlu in non-standard cases and for fine control.')
	parser.add_option('--root',
						default=config['ROOT_DIR'],
						help='root of the directory tree we will be working at (default: "%default").', 
						metavar='ROOT')
	parser.add_option('--input',
						default=config['INPUT_DIR'],
						help='name of directory containing previews (default: "%default").\n'
						'NOTE: this directory tree can not be used for OUTPUT.', 
						metavar='INPUT')
	parser.add_option('--output',
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
						default=config['TRAVERSE_DIR'],
						help='directory used to traverse to next level (default: "%default").', 
						metavar='TRAVERSE_DIR')
	advanced.add_option('--raw-extension',
						default=config['RAW_EXTENSION'],
						help='use as the extension for RAW files (default: "%default").', 
						metavar='RAW_EXTENSION')
##	advanced.add_option('--labels',
##						help='...', 
##						metavar='LABELS')
	advanced.add_option('--xmp-template',
						help='use XMP_TEMPLATE instead of the internal template.', 
						metavar='XMP_TEMPLATE')
	advanced.add_option('--use-labels', 
						action='store_true',
						default=config['USE_LABELS'],
						help='if set, use both labels and ratings.') 
	advanced.add_option('-s', '--skip', 
						action='append',
						default=config['SKIP'],
						help='list of directories to skip from searching for RAW '
						'files (default: %default)',
						metavar='SKIP') 
	##!!! list available modes here...
	advanced.add_option('--handle-overflow', 
						default=config['HANDLE_OVERFLOW'],
						help='the way to handle tree depth greater than the number '
						'of given ratings (default: %default). '
						'available options are: ' + str(tuple(HANDLE_OVERFLOW_OPTIONS.keys())),
						metavar='HANDLE_OVERFLOW') 
	parser.add_option_group(advanced)

	runtime = OptionGroup(parser, 'Runtime options')
	runtime.add_option('--dry-run',
						action='store_true',
						default=False,
						help='run but do not create any files.')
	parser.add_option_group(runtime)


	configuration = OptionGroup(parser, 'Configuration options')
	configuration.add_option('--config-print', 
						action='store_true',
						default=False,
						help='print current configuration and exit.')
	configuration.add_option('--config-defaults-print', 
						action='store_true',
						default=False,
						help='print default configuration and exit.')
	parser.add_option_group(configuration)

	options, args = parser.parse_args()

	# be polite and save the originla config data...
	config = config.copy()

	# prune and write the data...
	config.update({
			'ROOT_DIR': options.root,
			'INPUT_DIR': options.input,
			'OUTPUT_DIR': options.output if options.output else options.root,
			'TRAVERSE_DIR': options.traverse_dir_name,
			'RAW_EXTENSION': options.raw_extension,
			'THRESHOLD': options.group_threshold,
			'XMP_TEMPLATE': file(options.xmp_template, 'r').read() 
								if options.xmp_template 
								else config['XMP_TEMPLATE'],
			'RATE_TOP_LEVEL': options.rate_top_level,
			'SEARCH_INPUT': options.search_input,
			'SEARCH_OUTPUT': options.search_output,
			'VERBOSITY': options.verbosity,
			'USE_LABELS': options.use_labels,
			'SKIP': list(set(options.skip + [options.input])),
			})
	if not options.use_labels:
		config['RATINGS'] = range(5, 0, -1)
	
	if options.handle_overflow not in HANDLE_OVERFLOW_OPTIONS:
		raise ValueError, ('HANDLE_OVERFLOW value %s unsupported '
								'(use --help flag for list of options).' % options.handle_overflow)
	config['HANDLE_OVERFLOW'] = options.handle_overflow 


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


#----------------------------------------------------load_config_file---
def load_config_file(config, default_cfg=DEFAULT_CFG):
	'''
	load configuration data from config file
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



#-----------------------------------------------------------------------
#------------------------------------------------------------rcollect---
def rcollect(root, next_dir=DEFAULT_CFG['TRAVERSE_DIR'],
		collect_base=True, ext=('.jpg', '.JPG')):
	'''
	generator to collect all the files in the topology.

	yield:
		# lists of file names on each level, starting from the top and
		# going down.
		(
			[...],
			root
		)
	'''
	for r, dirs, files in os.walk(root):
		if collect_base:
			# filter files...
			res = [ (root, f) for f in files if True in [ f.endswith(e) for e in ext ]]
			# skip empty levels...
			if len(res) == 0:
				continue
			yield res
		else:
			collect_base = True
		# filter dirs...
		if next_dir in dirs:
			dirs[:] = [next_dir]
		else:
			del dirs[:] 


#-------------------------------------------------------------collect---
def collect(root, next_dir=DEFAULT_CFG['TRAVERSE_DIR'], 
		collect_base=True, ext=('.jpg', '.JPG')):
	'''
	same as collect, but does its work bottom-down.

	yield:
		same as rcollect(...) but in reverse order...
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

	yeild:
		{
			# same as collect(...) but diffed with the previous
			# level...
			'items': [...],
			# original number of elements...
			'total count': N,
			# root path for the current sub tree...
			'path': S,
		}
	'''
	prev = None
	for level in collection:
		cur = set(level)
		# skip empty levels...
		if len(level) == 0:
			continue
		if prev is not None:
			cur.difference_update(set(prev))
		prev = level
		yield {
			'total count': len(level),
			'items': cur, 
		}


#----------------------------------------------------------------rate---
##!!! do the overflow...
def rate(index, ratings=DEFAULT_CFG['RATINGS'], threshold=DEFAULT_CFG['THRESHOLD'], overflow_strategy=None):
	'''
	generator to rate the indexed elements.

	this also combines similar levels.

	NOTE: if the count of non-intersecting elements relative to the total 
	      number of elements is below the threshold, the level will be 
		  merged with the next. such levels are called "similar".

	yield:
		(
			# rating...
			N,
			# list of levels, each same as returned by index(...)...
			(...)
		)
	'''
	threshold = float(threshold)/100

	i = 0
	buf = ()
	for level in index:
		buf += (level,)
		if level['total count'] <= 0 or float(len(level['items']))/level['total count'] <= threshold:
			continue
		yield ratings[i], buf
		buf = ()
		i += 1



#-----------------------------------------------------------------------
#--------------------------------------------------------action_dummy---
def action_dummy(path, rating, label, data):
	'''
	dummy action, does nothing.
	'''
	return True


#----------------------------------------------------------filewriter---
##!!! check if file already exists...
def action_filewriter(path, rating, label, data):
	'''
	action to write a file.
	'''
	##!!! check if file already exists...
	file(path, 'w').write(data)
	return True


#-------------------------------------------------------action_logger---
def action_logger(path, rating, label, data, verbosity=1):
	'''
	action to log the current processed file.
	'''
	if verbosity == 1:
		print '.',
	elif verbosity == 2:
		print '%s (%s, %s)' % (path, rating, label)
	return True


#--------------------------------------------------------action_break---
def action_break(path, rating, label, data):
	'''
	action that prevents executions of subsequent actions.
	'''
	return False


#------------------------------------------------------------generate---
def generate(ratings, root, getpath=join, 
		actions=(action_filewriter,), template=DEFAULT_CFG['XMP_TEMPLATE']):
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
		for p, name in reduce(list.__add__, [ list(s['items']) for s in data ]):
			path = getpath(root, '.'.join(name.split('.')[:-1]), path=p) + '.XMP'
			for action in actions:
				if action is action_dummy:
					continue
				if not action(path, rating, label, xmp_data):
					break



#-----------------------------------------------------------------------
#------------------------------------------------------buildfilecache---
def buildfilecache(root, ext=DEFAULT_CFG['RAW_EXTENSION'], 
		skip_dirs=(DEFAULT_CFG['INPUT_DIR'],)):
	'''
	build a cache of all files in a tree with an extension ext.

	the cache is indexed by file name without extension and contains full paths.

	NOTE: if this finds more than one file with same name in the sub tree it will fail.
	'''
	res = {}
	for path, dirs, files in os.walk(root): 
		if path in skip_dirs:
			continue
		if len(skip_dirs) > 0:
			dirs[:] = list(set(dirs).difference(skip_dirs))	
		for f in files:
			if f.endswith(ext):
				base = '.'.join(f.split('.')[:-1])
				if base in res:
					res[base] += [(path, f)]
				res[base] = [(path, f)]
	return res


#-------------------------------------------------------bestpathmatch---
def bestpathmatch(source, paths, split=None):
	'''
	select closest path to source.

	here we use two criteria to judge closeness:
		- depth/size of sub-tree.
		  a tree at a deeper location (smaller) beats the more general
		  (larger) sub-tree.
		  e.g. max length of identical path section starting from root 
		  wins.

					A
				   / \			path AB is closer to AB(T) than A (obvious)
				  /   B
				 /   / \		path ABD is closer to AB(T) than AC
			    C   D  (T)

		- within a minimal sub-tree the shortest distance to sub-tree 
		  root wins.

		  		 	A
				   /|\
				  / | \
				 B  C (T)		path AB is closer to T than ACD		
				    |
				    D

	NOTE: we can not decide by our selves if two paths produce identical
		  scores.
		  e.g. paths AB and AC in the above diagram are at the same 
		  distance from T.
	'''
	if split is not None:
		source = split(source)
	final_score = 0
	res = [] 

	for path in paths:
		score = -1
		if split is not None:
			path = split(path)
		# go through path components top down...
		for i, (a, b) in enumerate(zip(path, source)):
			if a != b:
				# miss/stop..
				break
			if a == b:
				# we beet the score...
				if i > score:
					score = i
		# index results with max score...
		if score > final_score:
			final_score = score
			res = [path]
		# multiple possible matches (resolve on next stage)...
		elif score == final_score:
			res += [path]
	if len(res) > 1:
		# we have two+ paths and we need to decide which is a better
		# match via length...
		l = [ len(p) for p in res ]
		if l.count(min(l)) > 1:
			raise ValueError, 'we have more than one %s candidate directories with identical priorities relative to source %s.' % (res, source)
		res = [res[l.index(min(l))]]
	return res[0]


#---------------------------------------------------------getfilepath---
##!!! test for multiple matches...
def getfilepath(root, name, path=None, cache=None):
	'''
	find a file in a directory tree via cache and return it's path.

	NOTE: name should be given without an extension.
	NOTE: this ignores extensions.
	'''
	t_names = cache.get(name, ())
	if len(t_names) == 0:
		raise KeyError, 'file %s not found.' % name
	elif len(t_names) == 1:
		p, n = t_names[0]
		return os.path.join(p, '.'.join(n.split('.')[:-1]))
	elif len(t_names) > 1:
		# select best path match...
		p, n = bestpathmatch(name[0], ( e[0] for e in t_names )), name[1]

		return os.path.join(p, '.'.join(n.split('.')[:-1]))


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
		return
##	# make this compatible with name patterns...
##	##!!! this seams to yield odd results -- fails with --search-input...
##	for d in chain(cache[n] for n in (k for k in cache.keys() if k == name)):
	for d in cache[name]:
		yield d



#-----------------------------------------------------------------------
#-----------------------------------------------------------------run---
def run():
	'''
	prepare configuration data and run.
	'''
	# setup config data...
	config, runtime_options = load_commandline(load_config_file(DEFAULT_CFG))

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
	skip = config['SKIP']

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
									in izip_longest(
											fillvalue=[], 
											*(collect(d, traverse_dir, rate_top_level) 
										for d 
										in getdirpaths(
												root, 
												input, 
												builddircache(root, input)))))), 
			ratings=config['RATINGS'],
			threshold=threshold), 
		output, 
		# find a location for each output file...
		##!!! we do not need to do this if collect returned no results...
		getpath=(curry(getfilepath, cache=buildfilecache(output, raw_ext, skip_dirs=skip)) 
					if search_output 
					# just write to ROOT...
					else join),
		# actions to perform per XMP file...
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
