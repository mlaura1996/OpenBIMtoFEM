import gmsh
import numpy as np 

def find_common_numbers(tuple1, list_of_tuples):
    """
    This function accepts a tuple with the structure (int, [list of numbers]) and a list of tuples with the same structure.
    It returns a dictionary where the keys are the first numbers of the tuples from the list that have common numbers
    with the input tuple, and the values are the common numbers.

    :param tuple1: Tuple with structure (int, [list of numbers])
    :param list_of_tuples: List of tuples with the same structure (int, [list of numbers])
    :return: A dictionary with the first number of the matching tuples as keys and the common numbers as values.
    """
    # Extract the list from the first tuple
    list1 = tuple1[1]
    

    # Dictionary to store the results
    common_results = {}

    # Iterate over the list of tuples
    for t in list_of_tuples:
        # Extract the list from the current tuple
        list2 = t[1]

        # Find common elements using set intersection
        common_numbers = set(list1) & set(list2)

        # If there are common numbers, add to the results
        if common_numbers:
            common_results[t[0]] = common_numbers

    return common_results

def find_unique_numbers(tuple1, list_of_tuples):
    """
    This function accepts a tuple with the structure (int, [list of numbers]) and a list of tuples with the same structure.
    It returns the numbers from the first tuple that are not in common with any tuple in the list.

    :param tuple1: Tuple with structure (int, [list of numbers])
    :param list_of_tuples: List of tuples with the same structure (int, [list of numbers])
    :return: A set of numbers that are unique to the first tuple.
    """
    # Extract the list from the first tuple
    list1 = set(tuple1[1])

    # Set to collect all numbers from the second parameter
    all_other_numbers = set()

    # Iterate over the list of tuples to collect all numbers
    for t in list_of_tuples:
        all_other_numbers.update(t[1])

    # Find unique numbers by subtracting the set of all other numbers
    unique_numbers = list1 - all_other_numbers

    return unique_numbers

def group_normals(tags): 
    normals = []
    for tag in tags:
        parametric_coords = [1,0,0,1]  # Example parametric coordinates, can be adjusted as needed
        normal = gmsh.model.getNormal(tag, parametric_coords)
        normals.append(normal)
    
    return normals

def get_normals(tags):
    """
    Create a dictionary associating surface tags with their normals.

    :param tags: List of surface tags.
    :return: A dictionary with surface tags as keys and their normals as values.
    """
    normals_dict = {}
    for tag in tags:
        parametric_coords = [1, 0, 0, 1]  # Example parametric coordinates, can be adjusted as needed
        normal = gmsh.model.getNormal(tag, parametric_coords)
        normals_dict[tag] = normal  # Extract the first normal vector (x, y, z)

    return normals_dict

def group_arrays_by_absolute_values(arrays, tol=1e-9):
    """
    Groups numpy arrays based on having the same absolute values.
    
    :param arrays: List of numpy arrays
    :param tol: Tolerance for comparison of absolute values
    :return: A list of groups, where each group is a list of arrays with matching absolute values.
    """
    groups = []

    for array in arrays:
        abs_array = np.abs(array)
        found_group = False

        for group in groups:
            if np.allclose(np.abs(group[0]), abs_array, atol=tol):  # Compare absolute values with a tolerance
                group.append(array)
                found_group = True
                break

        if not found_group:
            groups.append([array])

    return groups

def find_matching_keys_with_absolute_values(beam_surfaces, reference_plan):
    """
    Finds keys in a dictionary where the values match a reference plan, considering absolute values.

    :param beam_surfaces: Dictionary where keys are tags and values are arrays of surface normals.
    :param reference_plan: Numpy array to compare against.
    :return: List of matching keys.
    """
    matching_keys = []
    for key, value in beam_surfaces.items():
        if np.allclose(np.abs(np.array(value)), np.abs(reference_plan), atol=1e-9):  # Use np.allclose for numerical stability
            matching_keys.append(key)
    return matching_keys

def close_prism(surfaces):

# Step 1: Get boundary edges of all provided surfaces
    boundary_edges = []
    for surface in surfaces:
        edges = gmsh.model.getBoundary([(2, surface)], oriented=False)
        boundary_edges.extend(edges)

    # Step 2: Find unique edges (those that appear only once are part of the missing surface)
    edge_counts = {}
    for edge in boundary_edges:
        edge_tag = edge[1]
        edge_counts[edge_tag] = edge_counts.get(edge_tag, 0) + 1
    
    open_edges = [edge for edge, count in edge_counts.items() if count == 1]

    if len(open_edges) < 3:
        raise ValueError("Insufficient open edges to define a missing surface.")

    # Step 3: Create a new surface from the open edges
    wire = gmsh.model.occ.addWire(open_edges)
    missing_surface = gmsh.model.occ.addPlaneSurface([wire])
    gmsh.model.occ.synchronize()

    # Step 4: Combine all surfaces into a shell
    all_surfaces = surfaces + [missing_surface]
    shell = gmsh.model.occ.addShell(all_surfaces)
    gmsh.model.occ.synchronize()

    # Step 5: Create a solid from the shell
    solid = gmsh.model.occ.addVolume([shell])
    gmsh.model.occ.synchronize()

    # Return the created solid tag
    return solid

def close_prism_with_surface_loop(surfaces):
    """
    Close a prism by inferring and creating the missing surface from 5 input surfaces.

    Parameters:
    surfaces (list of int): List of tags of the 5 surfaces that partially define the prism.

    Returns:
    int: The tag of the created solid (volume) after closing the prism.
    """
    if len(surfaces) != 5:
        raise ValueError("Exactly 5 surface tags must be provided.")


    # Step 1: Get boundary edges of all provided surfaces
    boundary_edges = []
    for surface in surfaces:
        edges = gmsh.model.getBoundary([(2, surface)], oriented=False)
        boundary_edges.extend(edges)
        #print(boundary_edges)

    # Step 2: Find unique edges (those that appear only once are part of the missing surface)
    edge_counts = {}
    for edge in boundary_edges:
        edge_tag = edge[1]
        edge_counts[edge_tag] = edge_counts.get(edge_tag, 0) + 1

    open_edges = [edge for edge, count in edge_counts.items() if count == 1]
    print(open_edges)

    if len(open_edges) < 3:
        raise ValueError("Insufficient open edges to define a missing surface.")

    # Step 3: Create a new surface from the open edges
    wire = gmsh.model.occ.addWire(open_edges)
    print(wire)
    missing_surface = gmsh.model.occ.addPlaneSurface([wire])
    gmsh.model.occ.synchronize()

    # # Step 4: Create a surface loop
    # all_surfaces = surfaces + [missing_surface]
    # surface_loop = gmsh.model.geo.addSurfaceLoop(all_surfaces)
    # gmsh.model.occ.synchronize()

    # # Step 5: Create a solid from the surface loop
    # volume = gmsh.model.geo.addVolume([surface_loop])
    # gmsh.model.occ.synchronize()

    # Return the created solid tag
    return missing_surface


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

        print(wall_vertices_tags)
        wall_bound = wall_tag, wall_vertices_tags
        
        wall_tuples.append(wall_bound)

        

    print("####################[Beams]####################")
    for beam_tag in beams:
        beam_vertices = gmsh.model.getBoundary([(3, beam_tag)], oriented=False, recursive=False)
        beam_vertices_tags =  [sublist[1] for sublist in beam_vertices]

        beam_tuple = beam_tag, beam_vertices_tags
        
        common = find_common_numbers(beam_tuple, wall_tuples)
        #print(common)
        # others = find_unique_numbers(beam_tuple, wall_tuples)
        if common != {}:
            print(common)
            
            
            for key, value in common.items():
                my_set = value
                print(my_set)
                print(type(my_set))
                my_list = list(my_set)
                print(type(my_list))
            missing_surface = close_prism_with_surface_loop(my_list)
            gmsh.model.occ.fragment([(3, beam_tag)], [(2, missing_surface)])
            gmsh.model.occ.synchronize()
            # print(list)
            # print(type(list))

        #     normals = group_normals(list)
        #     grouped = group_arrays_by_absolute_values(normals)
        #     #print(grouped)
        #     for group in grouped:
        #         if len(group) == 1:
        #             reference_plan = group 
        #             print("Ref_plan")
        #             print(reference_plan)
        #             print(len(reference_plan))
        #             print(reference_plan[0])
        #             print("##################################")
        #             # print(group)
        #             # #print(group)
        #             # print(others)
        #             # print(type(others))
        #             beam_surfaces = get_normals(others)
        #             print(beam_surfaces)
        #             print("###############################")

        #             matching_keys = find_matching_keys_with_absolute_values(beam_surfaces, reference_plan)
        #             print(matching_keys)
                











    # Run the Gmsh GUI to observe the result
    gmsh.fltk.run()




