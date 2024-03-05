import ifcopenshell
import json
#Create a dictionary to store the types from the ifc



def exportProperties(ifcFile, elements):

    materials = ifcFile.by_type('IfcMaterial')
    FullDictionaries = []
    i = 0

    
    for element in elements:

        # PropertiesName = ['solidMaterialTag']
        # i = i +1 
        # PropertiesValue = [i]
        PropertiesName = []
        i = i +1 
        PropertiesValue = []
        for rel in element.HasAssociations:
            matNameRel = rel.RelatingMaterial

            if hasattr(matNameRel, "Name") == True: #to see if the material is associated with the element
                matName = matNameRel.Name
                print(matName)
            
            elif rel.RelatingMaterial.is_a()=="IfcMaterialLayerSet": #because of Roofs
                for matlayer in rel.RelatingMaterial.MaterialLayers:
                    print(matlayer)
                    matName = matlayer.Material.Name
                    print(matName)

            elif rel.RelatingMaterial.is_a()=="IfcMaterialProfileSet": #because of Beams/columns
                for matlayer in rel.RelatingMaterial.MaterialLayers:
                    print(matlayer)
                    matName = matlayer.Material.Name
                    print(matName)        


        # in case Material is in the type
        for Type in element.IsTypedBy:
            ElementType = Type.RelatingType
            # print(ElementType)
            for relType in ElementType.HasAssociations:
                if relType.RelatingMaterial.is_a()=="IfcMaterialLayerSet": #because of Walls
                    #print('Material is attributed to type and it is based on a layer: ' + str(ElementType[2]) )
                    for matlayer in relType.RelatingMaterial.MaterialLayers:
                        matName = matlayer.Material.Name
                        print(matName)

                elif relType.RelatingMaterial.is_a()=="IfcMaterialProfileSet": #because of beams    
                    #print('Material is attributed to type and it is based on profiles')
                    for relass in relType.RelatingMaterial.MaterialProfiles:
                        matName = relass.Material.Name                       
                        print(matName)

        for material in materials:
            if material.Name == matName:
                #print(material.HasProperties) #prints all the psets
                for pset in material.HasProperties:
                    PropertiesName.append('MaterialName')
                    label = str(matName)
                    PropertiesValue.append(label) #this is to create physical groups 

                    if pset.Name == "Pset_MaterialCommon" or pset.Name == "Pset_MaterialMechanical":
                        #print(PropertiesName)                          
                        property = [item for item in pset if isinstance(item, tuple)] #the properties are stored as tuples
                        for ele in property[0]:
                            #print(ele)
                            PropertyName = ele[0]
                            PropertyValue = ele[2][0]
                            #print(PropertyName, ":", PropertyValue)
                            PropertiesName.append(PropertyName)
                            PropertiesValue.append(PropertyValue)

        dictionary = {PropertiesName[i]: PropertiesValue[i] for i in range(len(PropertiesName))}


        FullDictionaries.append(dictionary)
        dictionaries = []

        for item in FullDictionaries:
            if item not in dictionaries:
                dictionaries.append(item)

        filteredDics = [d for d in dictionaries if 'YoungModulus' in d]
                
    return(filteredDics)




#second function
import ifcopenshell.geom
import OCC.Core.TopoDS
from OCC.Core.STEPControl import (STEPControl_AsIs, STEPControl_Writer)
from OCC.Core.Interface import Interface_Static_SetCVal
from OCC.Core.STEPControl import (STEPControl_AsIs, STEPControl_Writer)
from OCC.Core.STEPConstruct import stepconstruct_FindEntity
from OCC.Core.TCollection import TCollection_HAsciiString
import OCC.Core.STEPConstruct
from OCC.Extend.DataExchange import read_step_file_with_names_colors
import OCC.Core.STEPConstruct
from OCC.Extend.DataExchange import read_step_file_with_names_colors
import OCC.Core.AIS
import OCC.Core.XCAFDoc
import OCC.Display.SimpleGui
from OCC.Core.IFSelect import IFSelect_RetError
from OCC.Core.BRepTools import breptools_Read
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Sewing
from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.TopAbs import TopAbs_FACE
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeSolid
from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh
from OCC.Core.TopoDS import TopoDS_Face, TopoDS_Solid

#the step writer labeling 

def STEPwriter(elements, data, fileName):

    labels = []
    for dictionary in data:
        value = dictionary['MaterialName']
        print(value)
        labels.append(value)

    selected_elements = []

    for element in elements:
        if element.is_a("IfcOpeningElement"):
            continue
        selected_elements.append(element)
    #print(selected_elements)

    # geometry settings
    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_PYTHON_OPENCASCADE, True) #generalinfo


    #OCAF SETTINGS
    # schema = 'AP214'
    schema = 'AP203'
    # AP242
    assembly_mode = 1
    writer = STEPControl_Writer()
    fp = writer.WS().TransferWriter().FinderProcess()
    Interface_Static_SetCVal('write.step.schema', schema)
    Interface_Static_SetCVal('write.step.unit', 'M')
    Interface_Static_SetCVal('write.step.assembly', str(assembly_mode))

    

    #label assignment
    for element in selected_elements:
        if element.Representation is not None:
            try:
                product = ifcopenshell.geom.create_shape(settings, element)
                # teste = product.geometry
                # shape_gpXYZ = teste.Location().Transformation().TranslationPart()
                # print(element.Name)
                # print(shape_gpXYZ.X(), shape_gpXYZ.Y(), shape_gpXYZ.Z())
            except:
                print("Shape creation failed")
            #product = ifcopenshell.geom.create_shape(settings, element)
            shape = OCC.Core.TopoDS.TopoDS_Iterator(product.geometry).Value()
            print(shape.DumpJsonToString())
            print(shape.NbChildren())
            if int(shape.NbChildren()) > 1:
                sewing = BRepBuilderAPI_Sewing()
                face_iterator = TopExp_Explorer(shape, TopAbs_FACE)
                while face_iterator.More():
                    face = face_iterator.Current()
                    sewing.Add(face)
                    face_iterator.Next()

                sewing.Perform()
                result = sewing.SewedShape()
                print(result)
                print(face_iterator.ExploredShape())
                print('gfuyfjfgygfjy')
                solid_maker = BRepBuilderAPI_MakeSolid(result)
                print(solid_maker.Solid())
                shape = solid_maker.Solid()

            for label in labels:
                if label in str(element.ObjectType):
                    print('ok')
                    eleName = label
                    
            Interface_Static_SetCVal('write.step.product.name', eleName)
            status = writer.Transfer(shape, STEPControl_AsIs)
            if int(status) > int(IFSelect_RetError):
                raise Exception('Some Error occurred')
            item = stepconstruct_FindEntity(fp, shape)
            item.SetName(TCollection_HAsciiString(eleName))
            if not item:
                raise Exception('Item not found')

    writer.Write(fileName + '.step'), read_step_file_with_names_colors(fileName + '.step')

    return str(fileName + '.step')

                    








