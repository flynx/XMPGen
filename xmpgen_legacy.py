#=======================================================================

__version__ = '''0.0.01'''
__sub_version__ = '''20110908102649'''
__copyright__ = '''(c) Alex A. Naanou 2011'''


#-----------------------------------------------------------------------

from itertools import repeat, chain, izip


#-----------------------------------------------------------------------
#--------------------------------------------------------izip_longest---
# taken from the python docs...
def izip_longest(*args, **kwds):
	# izip_longest('ABCD', 'xy', fillvalue='-') --> Ax By C- D-
	fillvalue = kwds.get('fillvalue')
	def sentinel(counter = ([fillvalue]*(len(args)-1)).pop):
		yield counter()			# yields the fillvalue, or raises IndexError
	fillers = repeat(fillvalue)
	iters = [chain(it, sentinel(), fillers) for it in args]
	try:
		for tup in izip(*iters):
			yield tup
	except IndexError:
		pass



#=======================================================================
#											 vim:set ts=4 sw=4 nowrap :
