#=======================================================================

__version__ = '''0.0.01'''
__sub_version__ = '''20110905175748'''
__copyright__ = '''(c) Alex A. Naanou 2011'''


#-----------------------------------------------------------------------

import shutil, os, os.path


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


#-----------------------------------------------------------------------

def collect(root, next_dir='fav', ext=('.jpg', '.JPG')):
	'''
	'''
	for r, dirs, files in os.walk(root):
		# filter files...
		yield [ f for f in files if True in [ f.endswith(e) for e in ext ]]
		# filter dirs...
		if next_dir in dirs:
			dirs[:] = [next_dir]
		else:
			del dirs[:] 


def index(collection):
	'''
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



THRESHOLD = 1.0/100
RATINGS = [
	##!!! the folowing need to be changed to the standard Adobe uses in Br and Lr...
	# labels...
	'yellow',
	'blue',
	# basic ratings...
	5, 4, 3, 2, 1,
]

def rate(index, ratings=RATINGS, threshold=THRESHOLD):
	'''
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



##!!!
def getpath(root, name, ext='NEF'):
	'''
	find a file in a directory tree and return it's path.

	NOTE: name should be given without an extension.
	NOTE: this will find a file with an extension ext.
	NOTE: if this finds more than one file with same name in the sub tree it will fail.
	'''
	##!!! locate a propper NEF file and use it's path...
	return os.path.join(root, name)



def generate(ratings, path, getpath=os.path.join, template=XMP_TEMPLATE):
	'''
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
			file(getpath(path, '.'.join(name.split('.')[:-1])) + '.XMP', 'w').write(xmp_data)





#=======================================================================
#                                            vim:set ts=4 sw=4 nowrap :
