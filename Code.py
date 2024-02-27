import ifcopenshell
import ifc2ops_model_export_geometry as model 
import ifc2ops_meshing as meshing
import ifc2ops_analysis as analysis
import gmsh2opensees as g2o
import openseespy.opensees as ops 



ifcFile = ifcopenshell.open("StructuralModel.ifc") #herecallyourfile
elements = ifcFile.by_type('IfcElement')

print(elements)



data = model.exportProperties(ifcFile, elements)
print(data)

FileName = 'Facade'
file = FileName + '.step'

stepfile = model.STEPwriter(elements, data, FileName)

MyModel = meshing.mesh_physical_groups(stepfile, data, True)


Fixed = meshing.fix_boundaries(MyModel)

Meshed = meshing.meshing(Fixed, True)


opsModel = analysis.Create4NodesTetraedron(Meshed, data)


staticAnalysis = analysis.StaticAnalysis(opsModel[0], opsModel[2], Meshed )

EigenAnalysis = analysis.EigenValue(opsModel[0], Meshed )
