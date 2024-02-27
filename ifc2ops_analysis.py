import openseespy.opensees as ops
import gmsh2opensees as g2o
import gmsh
import numpy as np
import matplotlib.pyplot as plt

def CreateLinearElasticMaterial(solidMaterialTag, E, nu, rho):
     ops.nDMaterial('ElasticIsotropic', solidMaterialTag, E, nu, rho)

def CreateNonLinearMaterial(solidMaterialTag, PaFc, E, nu):
    fc = (float(PaFc)) #MPa - N/mm2
    sig0 = fc
    ec = fc/E
    ft = fc/10
    et = ft/E

    ops.nDMaterial('ASDConcrete3D', solidMaterialTag, E, nu,
            '-Ce', 0.0, ec, ec+1,
            '-Cs', 0.0, fc, fc,
            '-Cd', 0.0, 0.0, 0.0,
            '-Te', 0.0, et, et+1,
            '-Ts', 0.0, ft, ft,
            '-Td', 0.0, 0.0, 0.0,
            'implex')

def Create4NodesTetraedron(gmshmodel, data):

    #modelBuilder
    ops.model("basicBuilder","-ndm",3,"-ndf",3)
    
    #get the material Name
    solidMaterialTag = 0
    g = 9810 #mm/s2
    allTheTags = []

    for dictionary in data:
        PhysicalGroup = dictionary['MaterialName']
        print(PhysicalGroup)
        PaE = dictionary['YoungModulus'] #Pa - N/m2
        E = (float(PaE))*1e-6 #MPa - N/mm2
        mrho = dictionary['MassDensity'] # kg / m³
        rho = float(mrho*1e-12) # Tons / mm³
        nu = dictionary['PoissonRatio'] #--
        solidMaterialTag = solidMaterialTag + 1

        if 'CompressiveStrength' in dictionary:
            PaFc = dictionary['CompressiveStrength'] #Pa - N/m2
            Fc = float(PaFc)*1e-6 #MPa - N/mm2
            Mat = CreateNonLinearMaterial(solidMaterialTag, Fc, E, nu)           
        else:
            Mat = CreateLinearElasticMaterial(solidMaterialTag, E, nu, rho)

        #get physical group
        elementTags, nodeTags, elementName, elementNnodes = g2o.get_elements_and_nodes_in_physical_group(PhysicalGroup, gmshmodel)
        allTheTags.append(elementTags)
        #add nodes to ops
        for nodeTag in nodeTags:
        #print(nodeTag)
            g2o.add_nodes_to_ops(nodeTag, gmshmodel, True)

        for eleTag, eleNodes in zip(elementTags, nodeTags):
            ops.element('FourNodeTetrahedron', eleTag, *eleNodes, solidMaterialTag, 0, 0, rho*g)

    


    elementTags2, nodeTags2, elementName2, elementNnodes2 = g2o.get_elements_and_nodes_in_physical_group("Fix", gmshmodel)
    g2o.fix_nodes(nodeTags2, 'XYZ')

    finalTags = [item for sublist in allTheTags for item in sublist]

    # ops.printModel('-JSON', '-file', 'model.json')
    # ops.printModel()
    return ops, elementTags, finalTags, nodeTags


def NonLinearStaticAnalysis(ops, elementTags, gmshmodel):
    Nsteps = 10
    ts_tag = 1
    ops.timeSeries('Linear', ts_tag)

    patternTag = 1
    ops.pattern('Plain', patternTag, ts_tag)

    ops.eleLoad("-ele", *elementTags, "-type", "-selfWeight", 0, 0, -1)

    ops.system("UmfPack")
    ops.numberer("Plain")
    ops.constraints('Plain')
    ops.integrator("LoadControl", 1/Nsteps)
    ops.algorithm("Newton")

    # create test
    #ops.test('NormUnbalance',10, 5000)
    ops.test('EnergyIncr', 0.01, 500)

    ops.analysis("Static")
    #ops.analyze(Nsteps) #very important or unless I will just analyze the first step

    data = np.zeros((Nsteps+1,2))
    for j in range(Nsteps):
        ops.analyze(1)
        data[j+1,0] = ops.nodeDisp(4,1)
    
    g2o.visualize_eleResponse_in_gmsh(gmshmodel, elementTags, "strains", new_view_name=f"Strain")


    #calculate the principal strains

    allTheStrains = []
    for i in range(6):
        modelData = (gmsh.view.getModelData(i+1, 0))[2]
        strain = []
        for value in modelData:
            strain.append(value[0])
        allTheStrains.append(strain)


    with open('AllStrain.txt', 'w') as file:
    # Write something to the file
        file.write(str(allTheStrains))


    #organize strain
    epsxx = allTheStrains[0]
    epsyy = allTheStrains[1]
    epszz = allTheStrains[2]
    epsxy = allTheStrains[3]
    epsyz = allTheStrains[4]
    epszx = allTheStrains[5]

    # print(len(epsxx))
    # print(len(epsyy))
    # print(len(epszz))
    # print(len(epsxy))
    # print(len(epsyz))
    # print(len(epszx))

    viewEleTags = (gmsh.view.getModelData(1, 0))[1]

    nodeNumbers = len(viewEleTags)

    with open('Tags.txt', 'w') as file:
    # Write something to the file
        file.write(str(viewEleTags))

    allSigma_I = []
    allSigma_II = []
    allSigma_III = []

    for i in range(nodeNumbers):

        strainMatrix = np.array([[epsxx[i], epsxy[i], epszx[i]],
                                [epsxy[i], epsyy[i], epsyz[i]],
                                [epszx[i], epsyz[i], epszz[i]]])
        
        eigenvalues, eigenvectors = np.linalg.eig(strainMatrix)

        index = eigenvalues.argsort()[::-1]
        EigenValues = eigenvalues[index]
        EigenVectors = eigenvectors[:, index]

        Sigma_I = EigenValues[0]
        Sigma_II = EigenValues[1]
        Sigma_III = EigenValues[2]



        SigmaPrincipal = np.array([[Sigma_I, 0.0, 0.0],
                                [0.0, Sigma_II, 0.0],
                                [0.0, 0.0, Sigma_III]])

        x_prime = EigenVectors[:, 0]
        y_prime = EigenVectors[:, 1]
        z_prime = EigenVectors[:, 2]    

        allSigma_I.append(Sigma_I)
        allSigma_II.append(Sigma_II)
        allSigma_III.append(Sigma_III)

    with open('SigmaI.txt', 'w') as file:
    # Write something to the file
        file.write(str(allSigma_I))

    # print('MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM')


    # print(eigenvalues)
    # print('sorted')
    # print(EigenValues)
    # print('NNNNNNNNNNNNNNNNNNNNNNNNNN')
    # print(eigenvectors)

    # print('__________________________________________________________________________________________')
    # print(str(Sigma_I))


    # sorted_indices = np.argsort(eigenvalues)[::-1]
    # principal_strains = eigenvalues[sorted_indices]
    # principal_directions = eigenvectors[:, sorted_indices]

    # print('------------------------------------------------------------------')
    # print(len(principal_strains))

#Add eigenvalues as data
    gmsh.view.add("PrincipalStrain_MAX", 7)
    gmsh.view.addHomogeneousModelData(tag = 7, step = 0, modelName = gmsh.model.getCurrent(), dataType = "ElementData", tags = viewEleTags, data = allSigma_I, time = 0, numComponents=-1, partition=0)

    gmsh.view.add("PrincipalStrain_MIN", 8)
    gmsh.view.addHomogeneousModelData(tag = 8, step = 0, modelName = gmsh.model.getCurrent(), dataType = "ElementData", tags = viewEleTags, data = allSigma_III, time = 0, numComponents=-1, partition=0)

    # Add eigenvectors as data
    # for i, node_tag in enumerate(viewEleTags):
    #     gmsh.view.addHomogeneousModelData(node_tag, 'Eigenvector', eigenvectors[i])

    # Save the view as a .pos file
    #gmsh.view.write('eigen_data.pos')

    # for i in range(Ncomponents):
    #gmsh.view.addHomogeneousModelData(
    #     tag=viewnums[i], 
    #     step=step,
    #     time=time, 
    #     modelName=gmsh.model.getCurrent(),
    #     dataType="ElementData",
    #     numComponents=-1,
    #     tags=eleTags,
    #     data=eleResponse_data[:,i].reshape((-1))


    gmsh.fltk.run()

    return data

def ParallelStaticNonLinearAnalysis(ops, elementTags, gmshmodel):
    pid = ops.getPID()
    np = ops.getNP()
    Nsteps = 10
    ts_tag = 1
    ops.timeSeries('Linear', ts_tag)

    patternTag = 1
    ops.pattern('Plain', patternTag, ts_tag)

    ops.eleLoad("-ele", *elementTags, "-type", "-selfWeight", 0, 0, -1)

    ops.partition() #this is the automatic partition in subdomains 

    '''Things for parallelization'''
    ops.system("Mumps") #the system that allow to pass back and forth the data. Its the linux parallel solver that does that
    ops.numberer("ParallelRCM") #if we want to number the equation, some node are shares and this allow the job of numbering the nodes in order to understand. This is a paralle version of the RCM number


    ops.constraints('Plain')
    ops.integrator("LoadControl", 1/Nsteps)
    ops.algorithm("Newton")

    # create test for convergence
    ops.test('NormUnbalance',10, 50)

    ops.analysis("Static")

    data = np.zeros((Nsteps+1,2))
    for j in range(Nsteps):
        ops.analyze(1)
        data[j+1,0] = ops.nodeDisp(4,1)
    
    g2o.visualize_eleResponse_in_gmsh(gmshmodel, elementTags, "strains", new_view_name=f"Strain")

    gmsh.fltk.run()
    return

def StaticAnalysis(ops, elementTags, gmshmodel):
    ts_tag = 1
    ops.timeSeries('Constant', ts_tag)

    patternTag = 1
    ops.pattern('Plain', patternTag, ts_tag)

    ops.eleLoad("-ele", *elementTags, "-type", "-selfWeight", 0, 0, -1)

    ops.system("UmfPack")
    ops.numberer("Plain")
    ops.constraints('Plain')
    ops.integrator("LoadControl", 1.0)
    ops.algorithm("Linear")

    ops.analysis("Static")

    ops.analyze(1)

    for node in ops.getNodeTags():
        disp = ops.nodeDisp(node)
        print(f"node # {node} {disp=}")

    g2o.visualize_displacements_in_gmsh(gmshmodel, ops.getNodeTags())
    g2o.visualize_eleResponse_in_gmsh(gmshmodel, elementTags, "stresses", new_view_name=f"Stress")
    g2o.visualize_eleResponse_in_gmsh(gmshmodel, elementTags, "strains", new_view_name=f"Strain")

    gmsh.fltk.run()

    return disp

def EigenValue(ops, gmshmodel):
    ops.system("UmfPack")
    ops.numberer("Plain")
    ops.constraints('Plain')
    ops.integrator("Newmark", 0.5, 0.25)
    ops.algorithm("Linear")

    ops.analysis("Transient")

    Nmodes = 300
    lamda = ops.eigen(Nmodes)
    ops.modalProperties('-print', '-file', 'ReportFinal.txt')
    #the eigenvalues
    print(f"{lamda=}")

    from numpy import sqrt, pi

    for i, lam in enumerate(lamda):
        mode = i + 1
        omega = sqrt(lam)
        f = omega / (2*pi)
        T = 1 / f
        print(f"{mode=} {omega=} (rad/s) {f=} (Hz) {T=} (s)")

        #mode = 2 
        g2o.visualize_eigenmode_in_gmsh(gmshmodel,
                                        mode=mode,
                                        f=sqrt(lamda[mode-1])/(2*pi), 
                                        animate=True)

    gmsh.fltk.run()
    gmsh.finalize()


    