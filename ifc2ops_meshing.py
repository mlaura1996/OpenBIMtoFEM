import gmsh

def mesh_physical_groups(stepFile, data, runGmsh = True): #maybe I separate

    labels = []
    for dictionary in data:
        value = dictionary['MaterialName']
        #print(value)
        labels.append(value)

    gmsh.initialize()
    gmsh.model.mesh.setOrder(2)
    gmsh.option.setNumber("General.Terminal", 1)

    #importing geo
    gmsh.model.add(stepFile[-4])
    gmsh.open(stepFile)

    #mantaining coherence between adjacent solids 
    gmsh.model.occ.fragment(gmsh.model.occ.getEntities(3), [])
    gmsh.model.occ.synchronize()

    #Create Physical groups
    tridEleTags = gmsh.model.occ.getEntities(dim = 3)

    #Original Dictionary

    OriginalDictionaryKeys = []
    OriginalDictionaryValues = []
    for ele in tridEleTags:
        tg = ele[1]
        EntName = gmsh.model.getEntityName(3, tg)
        OriginalDictionaryKeys.append(EntName)
        OriginalDictionaryValues.append(tg)

    OriginalDictionary= {k: v for k, v in zip(OriginalDictionaryKeys, OriginalDictionaryValues)}
    #print(OriginalDictionary)

    #Labeling Dictionary

    LabelDictionaryKeys = []
    [LabelDictionaryKeys.append(x) for x in labels if x not in LabelDictionaryKeys]
    LabelDictionaryValues = [0]*len(LabelDictionaryKeys)
    print(len(LabelDictionaryKeys))

    LabelDictionary = {key: None for key in LabelDictionaryKeys}

    FinalDict = {}

    for key2 in LabelDictionary.keys():
        matches = [OriginalDictionary[key1] for key1 in OriginalDictionary.keys() if key2 in key1]
        if matches:
            FinalDict[key2] = matches

    print(LabelDictionary)
    print(FinalDict)

    for key in FinalDict.keys():
        value = FinalDict[key]
        # print(key)
        # print(value)
        gmsh.model.addPhysicalGroup(dim=3, tags=value, name=key)

    if runGmsh:
        gmsh.fltk.run()

    gmsh.write('model.msh')
    
    return gmsh.model #it returns the model

def fix_boundaries(gmshmodel, runGmsh = True):

    for dim, tag in gmshmodel.getPhysicalGroups():
        # get the name of the physical group
        name = gmshmodel.getPhysicalName(dim, tag)

        # check if the name is "Fix"
        if "Footing" in name:
            print('Name is not the issue')
            # get the tags of all the entities in the physical group "Fix"
            footingTags = gmshmodel.getEntitiesForPhysicalGroup(3, tag)

    footingDimTag = [(3, footingTags[i]) for i in range(len(footingTags))]
    boundary = (gmshmodel.get_boundary(footingDimTag))
    boundaryTags = [sublist[1] for sublist in boundary]
    realBoundary  = [ent for ent in boundaryTags if ent < 0]
    #FinalBound  = [abs(n) for n in boundaryTags]
    FinalBound  = [abs(n) for n in realBoundary]

    # Compute the normal of each surface
    
    ToFix = []
    for surface in FinalBound:
        # Get the nodes of the surface
        normal = gmshmodel.getNormal(surface, [1,0,0,1])
        if normal[2] == -1 and normal[5] ==-1:
            print(str(surface) + str(normal))
            ToFix.append(surface)

    gmshmodel.addPhysicalGroup(dim=2, tags=ToFix, name="Fix")

    if runGmsh:
        gmsh.fltk.run()

    return(gmsh.model)

def applyLoad(gmshmodel, runGmsh = True):
    for dim, tag in gmshmodel.getPhysicalGroups():
        # get the name of the physical group
        name = gmshmodel.getPhysicalName(dim, tag)

        # check if the name is "Fix"
        if "TimberBoard" in name:
            # get the tags of all the entities in the physical group "Fix"
            BoardTags = gmshmodel.getEntitiesForPhysicalGroup(3, tag)

    BoardDimTag = [(3, BoardTags[i]) for i in range(len(BoardTags))]
    boundary = (gmshmodel.get_boundary(BoardDimTag))
    boundaryTags = [sublist[1] for sublist in boundary]
    print(boundaryTags)
    realBoundary  = [ent for ent in boundaryTags if ent < 0]
    FinalBound  = [abs(n) for n in boundaryTags]
    #FinalBound  = [abs(n) for n in realBoundary]

    # Compute the normal of each surface
    
    forLoad = []
    for surface in FinalBound:
    #for surface in boundaryTags:
        # Get the nodes of the surface
        normal = gmshmodel.getNormal(surface, [1,0,0,1])
        print(str(surface) + str(normal))
        if float(normal[2]) > 0 and float(normal[5]) > 0:
            forLoad.append(surface)

    gmshmodel.addPhysicalGroup(dim=2, tags=forLoad, name="Load")
    #gmshmodel.addPhysicalGroup(dim=2, tags=realBoundary, name="Load")

    return(gmsh.model)


def meshing(gmshmodel, runGmsh = True): #attenzione che voglio fare un parametro ifc
    gmshmodel.geo.removeAllDuplicates()

    gmsh.option.setNumber("Mesh.AngleToleranceFacetOverlap", 0.001)
    gmsh.option.setNumber("Mesh.MeshSizeMax", 450)

    gmshmodel.mesh.generate(3)
    gmshmodel.mesh.optimize()
    gmshmodel.mesh.remove_duplicate_nodes()

    if runGmsh:
        gmsh.fltk.run()

    return(gmsh.model)








