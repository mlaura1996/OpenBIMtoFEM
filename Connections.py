import gmsh

def split_beam_and_assign_to_wall():
    """
    Splits beam volumes into two parts based on wall planes. Beams and walls are identified
    based on physical groups containing "StructuralTimber" and "Masonry" respectively.
    The yellow part (inside the wall) is assigned to the wall's physical group, and the
    blue part to a new group.

    Returns:
        None
    """

    # Retrieve physical groups
    physical_groups = gmsh.model.getPhysicalGroups()
    
    # Identify beams and walls
    beams = []
    walls = []

    for dim, tag in physical_groups:
        name = gmsh.model.getPhysicalName(dim, tag)
        if "StructuralTimber" in name:
            beams.append(gmsh.model.getEntitiesForPhysicalGroup(dim, tag))
        elif "Masonry" in name:
            walls.append(gmsh.model.getEntitiesForPhysicalGroup(dim, tag))

        # Flatten the arrays in beams and walls
    beams = [item for sublist in beams for item in (sublist if hasattr(sublist, "__iter__") else [sublist])]
    walls = [item for sublist in walls for item in (sublist if hasattr(sublist, "__iter__") else [sublist])]

    # Loop through walls and beams
    print("####################[Walls]####################")
    wall_tuples = []
    for wall in walls:
        wall_tag = wall

        wall_vertices = gmsh.model.getBoundary([(3, wall_tag)], oriented=False, recursive=False)
        wall_vertices_tags =  [sublist[1] for sublist in wall_vertices]
        print(wall_tag)
        print(wall_vertices_tags)
        wall_bound = wall_tag, wall_vertices_tags
        print(type(wall_bound))
        
        wall_tuples.append(wall_bound)
        print(wall_tuples)
        

    print("####################[Beams]####################")
    for beam_tag in beams:
        beam_vertices = gmsh.model.getBoundary([(3, beam_tag)], oriented=False, recursive=False)
        beam_vertices_tags =  [sublist[1] for sublist in beam_vertices]
        print(beam_tag)
        print(beam_vertices_tags)





    # Run the Gmsh GUI to observe the result
    #gmsh.fltk.run()