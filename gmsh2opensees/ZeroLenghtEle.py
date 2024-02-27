import os

if os.name == 'nt':
	import openseespy.opensees as ops
else:   #not checked in mac
	import opensees as ops



from numpy import array, int32, double, concatenate, unique, setdiff1d, zeros
from numpy.linalg import norm




def add_nodes_to_ops(nodeTags, gmshmodel, remove_duplicates=True):
	"""
	Adds nodes in list nodeTags (coming from one of the other functions in this library)
	to the opensees model. Possibly can avoid duplicates by setting the remove_duplicates flag. 
	"""

	#Flatten the nodeTags array and remove duplicate nodes within the physical group
	nodeTags = unique(array(nodeTags, dtype=int).reshape(-1))

	#Remove global duplicates if need be
	if remove_duplicates:
		defined_nodes = ops.getNodeTags()
		nodeTags = setdiff1d(nodeTags, defined_nodes)

	for nodeTag in nodeTags:
		coord, parametricCoord, dim, tag = gmshmodel.mesh.get_node(nodeTag)
		ops.node(int(nodeTag), *coord)

def createZeroLenghtEle(nodeTags, gmshmodel, remove_duplicates=True):
	"""
	Adds nodes in list nodeTags (coming from one of the other functions in this library)
	to the opensees model. Possibly can avoid duplicates by setting the remove_duplicates flag. 
	"""

	#Flatten the nodeTags array and remove duplicate nodes within the physical group
	nodeTags = unique(array(nodeTags, dtype=int).reshape(-1))

	#Remove global duplicates if need be
	if remove_duplicates:
		defined_nodes = ops.getNodeTags()
		nodeTags = setdiff1d(nodeTags, defined_nodes)

	#take the last OPS tag
	tags = (ops.getNodeTags())
	last_tag = (tags[-1])

	EleTags = ops.getEleTags()
	last_eleTag = EleTags[-1] 

	for nodeTag in nodeTags:
		last_tag = last_tag + 1 
		coord, parametricCoord, dim, tag = gmshmodel.mesh.get_node(nodeTag)
		
		nodeTagEnd = ops.node(int(last_tag), *coord)
		last_eleTag = last_eleTag +1 

		ops.element('zeroLength', last_eleTag, (nodeTag, nodeTagEnd), '-mat', *matTags, (1,2))