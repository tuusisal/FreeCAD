# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2016 - Bernd Hahnebach <bernd@bimstatik.org>            *
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License (LGPL)    *
# *   as published by the Free Software Foundation; either version 2 of     *
# *   the License, or (at your option) any later version.                   *
# *   for detail see the LICENCE text file.                                 *
# *                                                                         *
# *   This program is distributed in the hope that it will be useful,       *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Library General Public License for more details.                  *
# *                                                                         *
# *   You should have received a copy of the GNU Library General Public     *
# *   License along with this program; if not, write to the Free Software   *
# *   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
# *   USA                                                                   *
# *                                                                         *
# ***************************************************************************


__title__ = "Tools for the work with FEM meshes"
__author__ = "Bernd Hahnebach"
__url__ = "http://www.freecadweb.org"


import FreeCAD


def get_femelements_by_references(femmesh, femelement_table, references):
    '''get the femelements for a list of references
    '''
    references_femelements = []
    for ref in references:
        ref_femnodes = get_femnodes_by_refshape(femmesh, ref)  # femnodes for the current ref
        references_femelements += get_femelements_by_femnodes(femelement_table, ref_femnodes)  # femelements for all references
    return references_femelements


def get_femnodes_by_references(femmesh, references):
    '''get the femnodes for a list of references
    '''
    references_femnodes = []
    for ref in references:
        references_femnodes += get_femnodes_by_refshape(femmesh, ref)

    # return references_femnodes  # keeps duplicate nodes, keeps node order

    # if nodes are used for nodesets, duplicats should be removed
    return list(set(references_femnodes))  # removes duplicate nodes, sortes node order


def get_femnodes_by_refshape(femmesh, ref):
    nodes = []
    for refelement in ref[1]:
        if refelement:
            r = ref[0].Shape.getElement(refelement)  # Vertex, Edge, Face
        else:
            r = ref[0].Shape  # solid
        print('  ReferenceShape : ', r.ShapeType, ', ', ref[0].Name, ', ', ref[0].Label, ' --> ', refelement)
        if r.ShapeType == 'Vertex':
            nodes += femmesh.getNodesByVertex(r)
        elif r.ShapeType == 'Edge':
            nodes += femmesh.getNodesByEdge(r)
        elif r.ShapeType == 'Face':
            nodes += femmesh.getNodesByFace(r)
        elif r.ShapeType == 'Solid':
            nodes += femmesh.getNodesBySolid(r)
        else:
            print('  No Vertice, Edge, Face or Solid as reference shapes!')
    return nodes


def get_femelement_table(femmesh):
    """ get_femelement_table(femmesh): { elementid : [ nodeid, nodeid, ... , nodeid ] }"""
    femelement_table = {}
    if is_solid_femmesh(femmesh):
        for i in femmesh.Volumes:
            femelement_table[i] = femmesh.getElementNodes(i)
    elif is_face_femmesh(femmesh):
        for i in femmesh.Faces:
            femelement_table[i] = femmesh.getElementNodes(i)
    elif is_edge_femmesh(femmesh):
        for i in femmesh.Edges:
            femelement_table[i] = femmesh.getElementNodes(i)
    else:
        FreeCAD.Console.PrintError('Neither solid nor face nor edge femmesh!\n')
    return femelement_table


def get_femelements_by_femnodes(femelement_table, node_list):
    '''for every femelement of femelement_table
    if all nodes of the femelement are in node_list,
    the femelement is added to the list which is returned
    e: elementlist
    nodes: nodelist '''
    e = []  # elementlist
    for elementID in sorted(femelement_table):
        nodecount = 0
        for nodeID in femelement_table[elementID]:
            if nodeID in node_list:
                nodecount = nodecount + 1
        if nodecount == len(femelement_table[elementID]):   # all nodes of the element are in the node_list!
            e.append(elementID)
    return e


def get_femvolumeelements_by_femfacenodes(femelement_table, node_list):
    '''assume femelement_table only has volume elements
    for every femvolumeelement of femelement_table
    for tetra4 and tetra10 the C++ methods could be used --> test again to be sure
    if hexa8 volume element --> if exact 4 element nodes are in node_list --> add femelement
    if hexa20 volume element --> if exact 8 element nodes are in node_list --> add femelement
    if penta6 volume element --> if exact 3 or 6 element nodes are in node_list --> add femelement
    if penta15 volume element --> if exact 6 or 8 element nodes are in node_list --> add femelement
    e: elementlist
    nodes: nodelist '''
    e = []  # elementlist
    for elementID in sorted(femelement_table):
        nodecount = 0
        el_nd_ct = len(femelement_table[elementID])
        if el_nd_ct == 8:  # hexa8
            for nodeID in femelement_table[elementID]:
                if nodeID in node_list:
                    nodecount = nodecount + 1
            if nodecount == 4: 
                e.append(elementID)
        elif el_nd_ct == 20:  # hexa20
            for nodeID in femelement_table[elementID]:
                if nodeID in node_list:
                    nodecount = nodecount + 1
            if nodecount == 8:
                e.append(elementID)
        elif el_nd_ct == 6:  # penta6
            for nodeID in femelement_table[elementID]:
                if nodeID in node_list:
                    nodecount = nodecount + 1
            if nodecount == 3 or nodecount == 4:
                e.append(elementID)
        elif el_nd_ct == 15:  # penta15
            for nodeID in femelement_table[elementID]:
                if nodeID in node_list:
                    nodecount = nodecount + 1
            if nodecount == 6 or nodecount == 8:
                e.append(elementID)
        else:
            FreeCAD.Console.PrintError('Error in get_femvolumeelements_by_femfacenodes(): not known volume element: ' + el_nd_ct + '\n')
    # print sorted(e)
    return e


def get_femelement_sets(femmesh, femelement_table, fem_objects):  # fem_objects = FreeCAD FEM document objects
    # get femelements for reference shapes of each obj.References
    count_femelements = 0
    referenced_femelements = []
    has_remaining_femelements = None
    for fem_object_i, fem_object in enumerate(fem_objects):
        obj = fem_object['Object']
        fem_object['ShortName'] = get_elset_short_name(obj, fem_object_i)  # unique short identifier
        if obj.References:
            ref_shape_femelements = []
            ref_shape_femelements = get_femelements_by_references(femmesh, femelement_table, obj.References)
            referenced_femelements += ref_shape_femelements
            count_femelements += len(ref_shape_femelements)
            fem_object['FEMElements'] = ref_shape_femelements
        else:
            has_remaining_femelements = obj.Name
    # get remaining femelements for the fem_objects
    if has_remaining_femelements:
        remaining_femelements = []
        for elemid in femelement_table:
            if elemid not in referenced_femelements:
                remaining_femelements.append(elemid)
        count_femelements += len(remaining_femelements)
        for fem_object in fem_objects:
            obj = fem_object['Object']
            if obj.Name == has_remaining_femelements:
                fem_object['FEMElements'] = sorted(remaining_femelements)
    # check if all worked out well
    if not femelements_count_ok(femelement_table, count_femelements):
        FreeCAD.Console.PrintError('Error in get_femelement_sets -- > femelements_count_ok() failed!\n')


def get_elset_short_name(obj, i):
    if hasattr(obj, "Proxy") and obj.Proxy.Type == 'MechanicalMaterial':
        return 'Mat' + str(i)
    elif hasattr(obj, "Proxy") and obj.Proxy.Type == 'FemBeamSection':
        return 'Beam' + str(i)
    elif hasattr(obj, "Proxy") and obj.Proxy.Type == 'FemShellThickness':
        return 'Shell' + str(i)
    else:
        print('Error: ', obj.Name, ' --> ', obj.Proxy.Type)


def get_force_obj_vertex_nodeload_table(femmesh, frc_obj):
    # force_obj_node_load_table = [('refshape_name.elemname',node_load_table), ..., ('refshape_name.elemname',node_load_table)]
    force_obj_node_load_table = []
    node_load = frc_obj.Force / len(frc_obj.References)
    for o, elem_tup in frc_obj.References:
        node_count = len(elem_tup)
        for elem in elem_tup:
            ref_node = o.Shape.getElement(elem)
            node = femmesh.getNodesByVertex(ref_node)
            elem_info_string = 'node load on shape: ' + o.Name + ':' + elem
            force_obj_node_load_table.append((elem_info_string, {node[0]: node_load / node_count}))

    return force_obj_node_load_table


def get_force_obj_edge_nodeload_table(femmesh, femelement_table, femnodes_mesh, frc_obj):
    # force_obj_node_load_table = [('refshape_name.elemname',node_load_table), ..., ('refshape_name.elemname',node_load_table)]
    force_obj_node_load_table = []
    sum_ref_edge_length = 0
    sum_ref_edge_node_length = 0  # for debugging
    sum_node_load = 0  # for debugging
    for o, elem_tup in frc_obj.References:
        for elem in elem_tup:
            sum_ref_edge_length += o.Shape.getElement(elem).Length
    if sum_ref_edge_length != 0:
        force_per_sum_ref_edge_length = frc_obj.Force / sum_ref_edge_length
    for o, elem_tup in frc_obj.References:
        for elem in elem_tup:
            ref_edge = o.Shape.getElement(elem)

            # edge_table = { meshedgeID : ( nodeID, ... , nodeID ) }
            edge_table = get_ref_edgenodes_table(femmesh, femelement_table, ref_edge)

            # node_length_table = [ (nodeID, length), ... , (nodeID, length) ]  some nodes will have more than one entry
            node_length_table = get_ref_edgenodes_lengths(femnodes_mesh, edge_table)

            # node_sum_length_table = { nodeID : Length, ... , nodeID : Length }  LengthSum for each node, one entry for each node
            node_sum_length_table = get_ref_shape_node_sum_geom_table(node_length_table)

            # node_load_table = { nodeID : NodeLoad, ... , nodeID : NodeLoad }  NodeLoad for each node, one entry for each node
            node_load_table = {}
            sum_node_lengths = 0  # for debugging
            for node in node_sum_length_table:
                sum_node_lengths += node_sum_length_table[node]  # for debugging
                node_load_table[node] = node_sum_length_table[node] * force_per_sum_ref_edge_length
            ratio_refedge_lengths = sum_node_lengths / ref_edge.Length
            if ratio_refedge_lengths < 0.99 or ratio_refedge_lengths > 1.01:
                FreeCAD.Console.PrintError('Error on: ' + frc_obj.Name + ' --> ' + o.Name + '.' + elem + '\n')
                print('  sum_node_lengths:', sum_node_lengths)
                print('  refedge_length:  ', ref_edge.Length)
                bad_refedge = ref_edge
            sum_ref_edge_node_length += sum_node_lengths

            elem_info_string = 'node loads on shape: ' + o.Name + ':' + elem
            force_obj_node_load_table.append((elem_info_string, node_load_table))

    for ref_shape in force_obj_node_load_table:
        for node in ref_shape[1]:
            sum_node_load += ref_shape[1][node]  # for debugging

    ratio = sum_node_load / frc_obj.Force
    if ratio < 0.99 or ratio > 1.01:
        print('Deviation  sum_node_load to frc_obj.Force is more than 1% :  ', ratio)
        print('  sum_ref_edge_node_length: ', sum_ref_edge_node_length)
        print('  sum_ref_edge_length:      ', sum_ref_edge_length)
        print('  sum_node_load:          ', sum_node_load)
        print('  frc_obj.Force:          ', frc_obj.Force)
        print('  the reason could be simply a circle length --> see method get_ref_edge_node_lengths')
        print('  the reason could also be an problem in retrieving the ref_edge_node_length')

        # try debugging of the last bad refedge
        print('DEBUGGING')
        print(bad_refedge)

        print('bad_refedge_nodes')
        bad_refedge_nodes = femmesh.getNodesByEdge(bad_refedge)
        print(len(bad_refedge_nodes))
        print(bad_refedge_nodes)
        # import FreeCADGui
        # FreeCADGui.ActiveDocument.Compound_Mesh.HighlightedNodes = bad_refedge_nodes

        print('bad_edge_table')
        # bad_edge_table = { meshedgeID : ( nodeID, ... , nodeID ) }
        bad_edge_table = get_ref_edgenodes_table(femmesh, femelement_table, bad_refedge)
        print(len(bad_edge_table))
        bad_edge_table_nodes = []
        for elem in bad_edge_table:
            print(elem, ' --> ', bad_edge_table[elem])
            for node in bad_edge_table[elem]:
                if node not in bad_edge_table_nodes:
                    bad_edge_table_nodes.append(node)
        print('sorted(bad_edge_table_nodes)')
        print(sorted(bad_edge_table_nodes))   # should be == bad_refedge_nodes
        # import FreeCADGui
        # FreeCADGui.ActiveDocument.Compound_Mesh.HighlightedNodes = bad_edge_table_nodes
        # bad_node_length_table = [ (nodeID, length), ... , (nodeID, length) ]  some nodes will have more than one entry

        print('good_edge_table')
        good_edge_table = delete_duplicate_mesh_elements(bad_edge_table)
        for elem in good_edge_table:
            print(elem, ' --> ', bad_edge_table[elem])

        print('bad_node_length_table')
        bad_node_length_table = get_ref_edgenodes_lengths(femnodes_mesh, bad_edge_table)
        for n, l in bad_node_length_table:
            print(n, ' --> ', l)

    return force_obj_node_load_table


def get_force_obj_face_nodeload_table(femmesh, femelement_table, femnodes_mesh, frc_obj):
    # force_obj_node_load_table = [('refshape_name.elemname',node_load_table), ..., ('refshape_name.elemname',node_load_table)]
    force_obj_node_load_table = []
    sum_ref_face_area = 0
    sum_ref_face_node_area = 0  # for debugging
    sum_node_load = 0  # for debugging
    for o, elem_tup in frc_obj.References:
        for elem in elem_tup:
            sum_ref_face_area += o.Shape.getElement(elem).Area
    if sum_ref_face_area != 0:
        force_per_sum_ref_face_area = frc_obj.Force / sum_ref_face_area
    for o, elem_tup in frc_obj.References:
        for elem in elem_tup:
            ref_face = o.Shape.getElement(elem)

            # face_table = { meshfaceID : ( nodeID, ... , nodeID ) }
            face_table = get_ref_facenodes_table(femmesh, femelement_table, ref_face)

            # node_area_table = [ (nodeID, Area), ... , (nodeID, Area) ]  some nodes will have more than one entry
            node_area_table = get_ref_facenodes_areas(femnodes_mesh, face_table)

            # node_sum_area_table = { nodeID : Area, ... , nodeID : Area }  AreaSum for each node, one entry for each node
            node_sum_area_table = get_ref_shape_node_sum_geom_table(node_area_table)

            # node_load_table = { nodeID : NodeLoad, ... , nodeID : NodeLoad }  NodeLoad for each node, one entry for each node
            node_load_table = {}
            sum_node_areas = 0  # for debugging
            for node in node_sum_area_table:
                sum_node_areas += node_sum_area_table[node]  # for debugging
                node_load_table[node] = node_sum_area_table[node] * force_per_sum_ref_face_area
            ratio_refface_areas = sum_node_areas / ref_face.Area
            if ratio_refface_areas < 0.99 or ratio_refface_areas > 1.01:
                FreeCAD.Console.PrintError('Error on: ' + frc_obj.Name + ' --> ' + o.Name + '.' + elem + '\n')
                print('  sum_node_areas:', sum_node_areas)
                print('  ref_face_area:  ', ref_face.Area)
            sum_ref_face_node_area += sum_node_areas

            elem_info_string = 'node loads on shape: ' + o.Name + ':' + elem
            force_obj_node_load_table.append((elem_info_string, node_load_table))

    for ref_shape in force_obj_node_load_table:
        for node in ref_shape[1]:
            sum_node_load += ref_shape[1][node]  # for debugging

    ratio = sum_node_load / frc_obj.Force
    if ratio < 0.99 or ratio > 1.01:
        print('Deviation  sum_node_load to frc_obj.Force is more than 1% :  ', ratio)
        print('  sum_ref_face_node_area: ', sum_ref_face_node_area)
        print('  sum_ref_face_area:      ', sum_ref_face_area)
        print('  sum_node_load:          ', sum_node_load)
        print('  frc_obj.Force:          ', frc_obj.Force)
        print('  the reason could be simply a circle area --> see method get_ref_face_node_areas')
        print('  the reason could also be an problem in retrieving the ref_face_node_area')

    return force_obj_node_load_table


def get_ref_edgenodes_table(femmesh, femelement_table, refedge):
    edge_table = {}  # { meshedgeID : ( nodeID, ... , nodeID ) }
    refedge_nodes = femmesh.getNodesByEdge(refedge)
    if is_solid_femmesh(femmesh):
        refedge_fem_volumeelements = []
        # if at least two nodes of a femvolumeelement are in refedge_nodes the volume is added to refedge_fem_volumeelements
        for elem in femelement_table:
            nodecount = 0
            for node in femelement_table[elem]:
                if node in refedge_nodes:
                    nodecount += 1
            if nodecount > 1:
                refedge_fem_volumeelements.append(elem)
        # for every refedge_fem_volumeelement look which of his nodes is in refedge_nodes --> add all these nodes to edge_table
        for elem in refedge_fem_volumeelements:
            fe_refedge_nodes = []
            for node in femelement_table[elem]:
                if node in refedge_nodes:
                    fe_refedge_nodes.append(node)
                edge_table[elem] = fe_refedge_nodes  # { volumeID : ( edgenodeID, ... , edgenodeID  )} # only the refedge nodes
        #  FIXME duplicate_mesh_elements: as soon as contact ans springs are supported the user should decide on which edge the load is applied
        edge_table = delete_duplicate_mesh_elements(edge_table)
    elif is_face_femmesh(femmesh):
        refedge_fem_faceelements = []
        # if at least two nodes of a femfaceelement are in refedge_nodes the volume is added to refedge_fem_volumeelements
        for elem in femelement_table:
            nodecount = 0
            for node in femelement_table[elem]:
                if node in refedge_nodes:
                    nodecount += 1
            if nodecount > 1:
                refedge_fem_faceelements.append(elem)
        # for every refedge_fem_faceelement look which of his nodes is in refedge_nodes --> add all these nodes to edge_table
        for elem in refedge_fem_faceelements:
            fe_refedge_nodes = []
            for node in femelement_table[elem]:
                if node in refedge_nodes:
                    fe_refedge_nodes.append(node)
                edge_table[elem] = fe_refedge_nodes  # { faceID : ( edgenodeID, ... , edgenodeID  )} # only the refedge nodes
        #  FIXME duplicate_mesh_elements: as soon as contact ans springs are supported the user should decide on which edge the load is applied
        edge_table = delete_duplicate_mesh_elements(edge_table)
    elif is_edge_femmesh(femmesh):
        refedge_fem_edgeelements = get_femelements_by_femnodes(femelement_table, refedge_nodes)
        for elem in refedge_fem_edgeelements:
            edge_table[elem] = femelement_table[elem]  # { edgeID : ( nodeID, ... , nodeID  )} # all nodes off this femedgeelement
    return edge_table


def get_ref_edgenodes_lengths(femnodes_mesh, edge_table):
    # calulate the appropriate node_length for every node of every mesh edge (me)
    # G. Lakshmi Narasaiah, Finite Element Analysis, p206ff

    #  [ (nodeID, length), ... , (nodeID, length) ]  some nodes will have more than one entry
    if (not femnodes_mesh) or (not edge_table):
        FreeCAD.Console.PrintError("Error in get_ref_edgenodes_lengths(): Empty femnodes_mesh or edge_table!\n")
        return []
    node_length_table = []
    mesh_edge_length = 0
    # print(len(edge_table))
    for me in edge_table:
        femmesh_edgetype = len(edge_table[me])
        if femmesh_edgetype == 2:  # 2 node femmesh edge
            # end_node_length = mesh_edge_length / 2
            #    ______
            #  P1      P2
            P1 = femnodes_mesh[edge_table[me][0]]
            P2 = femnodes_mesh[edge_table[me][1]]
            edge_vec = P2 - P1
            mesh_edge_length = edge_vec.Length
            # print(mesh_edge_length)
            end_node_length = mesh_edge_length / 2.0
            node_length_table.append((edge_table[me][0], end_node_length))
            node_length_table.append((edge_table[me][1], end_node_length))

        elif femmesh_edgetype == 3:  # 3 node femmesh edge
            # end_node_length = mesh_edge_length / 6
            # middle_node_length = mesh_face_area * 2 / 3
            #   _______ _______
            # P1       P3      P2
            P1 = femnodes_mesh[edge_table[me][0]]
            P2 = femnodes_mesh[edge_table[me][1]]
            P3 = femnodes_mesh[edge_table[me][2]]
            edge_vec1 = P3 - P1
            edge_vec2 = P2 - P3
            mesh_edge_length = edge_vec1.Length + edge_vec2.Length
            # print(me, ' --> ', mesh_edge_length)
            end_node_length = mesh_edge_length / 6.0
            middle_node_length = mesh_edge_length * 2.0 / 3.0
            node_length_table.append((edge_table[me][0], end_node_length))
            node_length_table.append((edge_table[me][1], end_node_length))
            node_length_table.append((edge_table[me][2], middle_node_length))
    return node_length_table


def get_ref_facenodes_table(femmesh, femelement_table, ref_face):
    face_table = {}  # { meshfaceID : ( nodeID, ... , nodeID ) }
    if is_solid_femmesh(femmesh):
        if has_no_face_data(femmesh):
            print('No face date in volume mesh. We try to use getccxVolumesByFace() to retrive the volume elments of the ref_face!')
            # there is no face data
            # the problem if we retrive the nodes ourself is they are not sorted we just have the nodes. We need to sourt them according 
            # the shell mesh notaion of tria3, tria6, quad4, quad8
            ref_face_nodes = femmesh.getNodesByFace(ref_face)
            # try to use getccxVolumesByFace() to get the volume ids of element with elementfaces on the ref_face --> should work for tetra4 and tetra10
            ref_face_volume_elements = femmesh.getccxVolumesByFace(ref_face)  # list of tupels (mv, ccx_face_nr)
            if ref_face_volume_elements: # mesh with tetras
                print('Use of getccxVolumesByFace() has returned volume elements of the ref_face!')
                for ve in ref_face_volume_elements:
                    veID = ve[0]
                    ve_ref_face_nodes = []
                    for nodeID in femelement_table[veID]:
                        if nodeID in ref_face_nodes:
                            ve_ref_face_nodes.append(nodeID)
                    face_table[veID] = ve_ref_face_nodes  # { volumeID : ( facenodeID, ... , facenodeID ) } only the ref_face nodes
            else:  # mesh with hexa or penta
                print('Use of getccxVolumesByFace() has NOT returned volume elements of the ref_face! We try to use get_femvolumeelements_by_femfacenodes()!')
                ref_face_volume_elements = get_femvolumeelements_by_femfacenodes(femelement_table, ref_face_nodes) # list of integer [mv]
                for veID in ref_face_volume_elements:
                    ve_ref_face_nodes = []
                    for nodeID in femelement_table[veID]:
                        if nodeID in ref_face_nodes:
                            ve_ref_face_nodes.append(nodeID)
                    face_table[veID] = ve_ref_face_nodes  # { volumeID : ( facenodeID, ... , facenodeID ) } only the ref_face nodes
                face_table = build_mesh_faces_of_volume_elements(face_table, femelement_table)  # we need to resort the nodes to make them build a element face
        else:  # the femmesh has face_data
            faces = femmesh.getFacesByFace(ref_face)   # (mv, mf)
            for mf in faces:
                face_table[mf] = femmesh.getElementNodes(mf)
    elif is_face_femmesh(femmesh):
        ref_face_nodes = femmesh.getNodesByFace(ref_face)
        ref_face_elements = get_femelements_by_femnodes(femelement_table, ref_face_nodes)
        for mf in ref_face_elements:
            face_table[mf] = femelement_table[mf]
    # print face_table
    return face_table


def build_mesh_faces_of_volume_elements(face_table, femelement_table):
    # node index of facenodes in femelementtable volume element
    # if we know the position of the node we can build the element face out of the unsorted face nodes
    face_nodenumber_table = {}  # { volumeID : ( index, ... , index ) }
    for veID in face_table:
        face_nodenumber_table[veID] = []
        for n in face_table[veID]:
            index = femelement_table[veID].index(n)
            # print(index)
            face_nodenumber_table[veID].append(index + 1)  # lokale node number = index + 1
        # print 'VolElement:', veID
        # print '  --> ', femelement_table[veID]
        # print '  --> ', face_table[veID]
        # print '  --> ', face_nodenumber_table[veID]
    for veID in face_nodenumber_table:
        vol_node_ct = len(femelement_table[veID])
        face_node_indexs = sorted(face_nodenumber_table[veID])
        if vol_node_ct == 10:  # tetra10 --> tria6 face
            if face_node_indexs == [1, 2, 3, 5, 6, 7]:  # node order of face  in tetra10 volume element
                node_numbers = (1, 2, 3, 5, 6, 7)       # node order of a tria6 face of tetra10
            elif face_node_indexs == [1, 2, 4, 5, 8, 9]:
                node_numbers = (1, 4, 2, 8, 9, 5)
            elif face_node_indexs == [1, 3, 4, 7, 8, 10]:
                node_numbers = (1, 3, 4, 7, 10, 8)
            elif face_node_indexs == [2, 3, 4, 6, 9, 10]:
                node_numbers = (2, 4, 3, 9, 10, 6)
            else:
                FreeCAD.Console.PrintError("Error in build_mesh_faces_of_volume_elements(): hexa20: face not found!" + str(face_node_indexs) + "\n")
        elif vol_node_ct == 4:  # tetra4 --> tria3 face
            if face_node_indexs == [1, 2, 3]:  # node order of face  in tetra4 volume element
                node_numbers = (1, 2, 3)       # node order of a tria3 face of tetra4
            elif face_node_indexs == [1, 2, 4]:
                node_numbers = (1, 4, 2, 8)
            elif face_node_indexs == [1, 3, 4]:
                node_numbers = (1, 3, 4)
            elif face_node_indexs == [2, 3, 4]:
                node_numbers = (2, 4, 3)
            else:
                FreeCAD.Console.PrintError("Error in build_mesh_faces_of_volume_elements(): hexa20: face not found!" + str(face_node_indexs) + "\n")
        elif vol_node_ct == 20:  # hexa20 --> quad8 face
            if face_node_indexs == [1, 2, 3, 4, 9, 10, 11, 12]:  # node order of face  in hexa20 volume element
                node_numbers = (1, 2, 3, 4, 9, 10, 11, 12)       # node order of a quad8 face of hexa20
            elif face_node_indexs == [5, 6, 7, 8, 13, 14, 15, 16]:
                node_numbers = (5, 8, 7, 6, 16, 15, 14, 13)
            elif face_node_indexs == [1, 2, 5, 6, 9, 13, 17, 18]:
                node_numbers = (1, 5, 6, 2, 17, 13, 18, 9)
            elif face_node_indexs == [3, 4, 7, 8, 11, 15, 19, 20]:
                node_numbers = (3, 7, 8, 4, 19, 15, 20, 11)
            elif face_node_indexs == [1, 4, 5, 8, 12, 16, 17, 20]:
                node_numbers = (1, 4, 8, 5, 12, 20, 16, 17)
            elif face_node_indexs == [2, 3, 6, 7, 10, 14, 18, 19]:
                node_numbers = (2, 6, 7, 3, 18, 14, 19, 10)
            else:
                FreeCAD.Console.PrintError("Error in build_mesh_faces_of_volume_elements(): hexa20: face not found!" + str(face_node_indexs) + "\n")
        elif vol_node_ct == 8:  # hexa8 --> quad4 face
            face_node_indexs = sorted(face_nodenumber_table[veID])
            if face_node_indexs == [1, 2, 3, 4]:  # node order of face  in hexa8 volume element
                node_numbers = (1, 2, 3, 4)       # node order of a quad8 face of hexa8
            elif face_node_indexs == [5, 6, 7, 8]:
                node_numbers = (5, 8, 7, 6)
            elif face_node_indexs == [1, 2, 5, 6]:
                node_numbers = (1, 5, 6, 2)
            elif face_node_indexs == [3, 4, 7, 8]:
                node_numbers = (3, 7, 8, 4)
            elif face_node_indexs == [1, 4, 5, 8]:
                node_numbers = (1, 4, 8, 5)
            elif face_node_indexs == [2, 3, 6, 7]:
                node_numbers = (2, 6, 7, 3)
            else:
                FreeCAD.Console.PrintError("Error in build_mesh_faces_of_volume_elements(): hexa20: face not found!" + str(face_node_indexs) + "\n")
        elif vol_node_ct == 15:  # penta15 --> tria6 and quad8 faces
            if face_node_indexs == [1, 2, 3, 7, 8, 9]:  # node order of face  in penta15 volume element
                node_numbers = (1, 2, 3, 7, 8, 9)       # node order of a tria6 face of penta15
            elif face_node_indexs == [4, 5, 6, 10, 11, 12]:
                node_numbers = (4, 6, 5, 12, 11, 10)  # tria6
            elif face_node_indexs == [1, 2, 4, 5, 7, 10, 13, 14]:
                node_numbers = (1, 4, 5, 2, 13, 10, 14, 7)  # quad8
            elif face_node_indexs == [1, 3, 4, 6, 9, 12, 13, 15]:
                node_numbers = (1, 3, 6, 4, 9, 15, 12, 13)  # quad8
            elif face_node_indexs == [2, 3, 5, 6, 8, 11, 14, 15]:
                node_numbers = (2, 5, 6, 3, 14, 11, 15, 8)  # quad8
            else:
                FreeCAD.Console.PrintError("Error in build_mesh_faces_of_volume_elements(): penta15: face not found!" + str(face_node_indexs) + "\n")
        elif vol_node_ct == 6:  # penta6 --> tria3 and quad4 faces
            if face_node_indexs == [1, 2, 3]:  # node order of face  in penta6 volume element
                node_numbers = (1, 2, 3)       # node order of a tria3 face of penta6
            elif face_node_indexs == [4, 5, 6]:
                node_numbers = (4, 6, 5)  # tria3
            elif face_node_indexs == [1, 2, 4, 5]:
                node_numbers = (1, 4, 5, 2)  # quad4
            elif face_node_indexs == [1, 3, 4, 6]:
                node_numbers = (1, 3, 6, 4)  # quad4
            elif face_node_indexs == [2, 3, 5, 6]:
                node_numbers = (2, 5, 6, 3)  # quad4
            else:
                FreeCAD.Console.PrintError("Error in build_mesh_faces_of_volume_elements(): pent6: face not found!" + str(face_node_indexs) + "\n")
        else:
             FreeCAD.Console.PrintError("Error in build_mesh_faces_of_volume_elements(): Volume not implemented: volume node count" + str(vol_node_ct) + "\n")
        face_nodes = []
        for i in node_numbers:
            i -= 1  # node_number starts with 1, index starts with 0 --> index = node number - 1
            face_nodes.append(femelement_table[veID][i])
        face_table[veID] = face_nodes  # reset the entry in face_table
        # print '  --> ', face_table[veID]
    return face_table


def get_ref_facenodes_areas(femnodes_mesh, face_table):
    # calulate the appropriate node_areas for every node of every mesh face (mf)
    # G. Lakshmi Narasaiah, Finite Element Analysis, p206ff
    # FIXME only gives exact results in case of a real triangle. If for S6 or C3D10 elements
    # the midnodes are not on the line between the end nodes the area will not be a triangle
    # see http://forum.freecadweb.org/viewtopic.php?f=18&t=10939&start=40#p91355  and ff
    # same applies for the quads, results are exact only if mid nodes are on the line between corner nodes

    #  [ (nodeID,Area), ... , (nodeID,Area) ]  some nodes will have more than one entry
    if (not femnodes_mesh) or (not face_table):
        FreeCAD.Console.PrintError("Error: Empty femnodes_mesh or face_table!\n")
        return []
    node_area_table = []
    mesh_face_area = 0
    for mf in face_table:
        femmesh_facetype = len(face_table[mf])
        # nodes in face_table need to be in the right node order for the following calcualtions
        if femmesh_facetype == 3:  # 3 node femmesh face triangle
            # corner_node_area = mesh_face_area / 3.0
            #      P3
            #      /\
            #     /  \
            #    /____\
            #  P1      P2
            P1 = femnodes_mesh[face_table[mf][0]]
            P2 = femnodes_mesh[face_table[mf][1]]
            P3 = femnodes_mesh[face_table[mf][2]]

            mesh_face_area = get_triangle_area(P1, P2, P3)
            corner_node_area = mesh_face_area / 3.0

            node_area_table.append((face_table[mf][0], corner_node_area))
            node_area_table.append((face_table[mf][1], corner_node_area))
            node_area_table.append((face_table[mf][2], corner_node_area))

        elif femmesh_facetype == 4:  # 4 node femmesh face quad
            # corner_node_area = mesh_face_area / 4.0
            #  P4_______P3
            #    |     /|
            #    | t2 / |
            #    |   /  |
            #    |  /   |
            #    | / t1 |
            #    |/_____|
            #  P1       P2
            P1 = femnodes_mesh[face_table[mf][0]]
            P2 = femnodes_mesh[face_table[mf][1]]
            P3 = femnodes_mesh[face_table[mf][2]]
            P4 = femnodes_mesh[face_table[mf][3]]

            mesh_face_t1_area = get_triangle_area(P1, P2, P3)
            mesh_face_t2_area = get_triangle_area(P1, P3, P4)
            mesh_face_area = mesh_face_t1_area + mesh_face_t1_area
            corner_node_area = mesh_face_area / 4.0

            node_area_table.append((face_table[mf][0], corner_node_area))
            node_area_table.append((face_table[mf][1], corner_node_area))
            node_area_table.append((face_table[mf][2], corner_node_area))
            node_area_table.append((face_table[mf][3], corner_node_area))

        elif femmesh_facetype == 6:  # 6 node femmesh face triangle
            # corner_node_area = 0
            # middle_node_area = mesh_face_area / 3.0
            #         P3
            #         /\
            #        /t3\
            #       /    \
            #     P6------P5
            #     / \ t4 / \
            #    /t1 \  /t2 \
            #   /_____\/_____\
            # P1      P4      P2
            P1 = femnodes_mesh[face_table[mf][0]]
            P2 = femnodes_mesh[face_table[mf][1]]
            P3 = femnodes_mesh[face_table[mf][2]]
            P4 = femnodes_mesh[face_table[mf][3]]
            P5 = femnodes_mesh[face_table[mf][4]]
            P6 = femnodes_mesh[face_table[mf][5]]

            mesh_face_t1_area = get_triangle_area(P1, P4, P6)
            mesh_face_t2_area = get_triangle_area(P2, P5, P4)
            mesh_face_t3_area = get_triangle_area(P3, P6, P5)
            mesh_face_t4_area = get_triangle_area(P4, P5, P6)
            mesh_face_area = mesh_face_t1_area + mesh_face_t2_area + mesh_face_t3_area + mesh_face_t4_area
            middle_node_area = mesh_face_area / 3.0

            node_area_table.append((face_table[mf][0], 0))
            node_area_table.append((face_table[mf][1], 0))
            node_area_table.append((face_table[mf][2], 0))
            node_area_table.append((face_table[mf][3], middle_node_area))
            node_area_table.append((face_table[mf][4], middle_node_area))
            node_area_table.append((face_table[mf][5], middle_node_area))

        elif femmesh_facetype == 8:  # 8 node femmesh face quad
            # corner_node_area = -mesh_face_area / 12.0  (negativ!)
            # mid-side nodes = mesh_face_area / 3.0
            #  P4_________P7________P3
            #    |      / |  \      |
            #    | t4 /   |    \ t3 |
            #    |  /     |      \  |
            #    |/       |        \|
            #  P8|    t5  |   t6    |P6
            #    |\       |       / |
            #    |  \     |     /   |
            #    | t1 \   |   /  t2 |
            #    |______\_|_/_______|
            #  P1         P5        P2
            P1 = femnodes_mesh[face_table[mf][0]]
            P2 = femnodes_mesh[face_table[mf][1]]
            P3 = femnodes_mesh[face_table[mf][2]]
            P4 = femnodes_mesh[face_table[mf][3]]
            P5 = femnodes_mesh[face_table[mf][4]]
            P6 = femnodes_mesh[face_table[mf][5]]
            P7 = femnodes_mesh[face_table[mf][6]]
            P8 = femnodes_mesh[face_table[mf][7]]

            mesh_face_t1_area = get_triangle_area(P1, P5, P8)
            mesh_face_t2_area = get_triangle_area(P5, P2, P6)
            mesh_face_t3_area = get_triangle_area(P6, P3, P7)
            mesh_face_t4_area = get_triangle_area(P7, P4, P8)
            mesh_face_t5_area = get_triangle_area(P5, P7, P8)
            mesh_face_t6_area = get_triangle_area(P5, P6, P7)
            mesh_face_area = mesh_face_t1_area + mesh_face_t2_area + mesh_face_t3_area + mesh_face_t4_area + mesh_face_t5_area + mesh_face_t6_area
            corner_node_area = -mesh_face_area / 12.0
            middle_node_area = mesh_face_area / 3.0

            node_area_table.append((face_table[mf][0], corner_node_area))
            node_area_table.append((face_table[mf][1], corner_node_area))
            node_area_table.append((face_table[mf][2], corner_node_area))
            node_area_table.append((face_table[mf][3], corner_node_area))
            node_area_table.append((face_table[mf][4], middle_node_area))
            node_area_table.append((face_table[mf][5], middle_node_area))
            node_area_table.append((face_table[mf][6], middle_node_area))
            node_area_table.append((face_table[mf][7], middle_node_area))
    return node_area_table


def get_ref_shape_node_sum_geom_table(node_geom_table):
    # shape could be Edge or Face, geom could be lenght or area
    # summ of legth or area for each node of the ref_shape
    node_sum_geom_table = {}
    for n, A in node_geom_table:
        # print(n, ' --> ', A)
        if n in node_sum_geom_table:
            node_sum_geom_table[n] = node_sum_geom_table[n] + A
        else:
            node_sum_geom_table[n] = A
    return node_sum_geom_table


def femelements_count_ok(femelement_table, count_femelements):
    if count_femelements == len(femelement_table):
        # print('Count FEM elements for the calculated node load distribution: ', count_femelements)
        # print('Count FEM elements of the FreeCAD FEM mesh:  ', len(femelement_table))
        return True
    else:
        print('ERROR: femelement_table != count_femelements')
        print('Count FEM elements for the calculated node load distribution: ', count_femelements)
        print('Count FEM Elements of the FreeCAD FEM Mesh:  ', len(femelement_table))
        return False


def delete_duplicate_mesh_elements(refelement_table):
    new_refelement_table = {}  # duplicates deleted
    for elem, nodes in refelement_table.items():
        if sorted(nodes) not in sortlistoflistvalues(new_refelement_table.values()):
            new_refelement_table[elem] = nodes
    return new_refelement_table


def get_triangle_area(P1, P2, P3):
    # import Part
    # W = Part.Wire([Part.makeLine(P1,P2), Part.makeLine(P2,P3), Part.makeLine(P3,P1)])
    # Part.show(Part.Face(W))
    vec1 = P2 - P1
    vec2 = P3 - P1
    vec3 = vec1.cross(vec2)
    return 0.5 * vec3.Length


def sortlistoflistvalues(listoflists):
    new_list = []
    for l in listoflists:
        new_list.append(sorted(l))
    return new_list


def is_solid_femmesh(femmesh):
    if femmesh.VolumeCount > 0:  # solid femmesh
        return True


def has_no_face_data(femmesh):
    if femmesh.FaceCount == 0:   # femmesh has no face data, could be a edge femmesh or a solid femmesh without face data
        return True


def is_face_femmesh(femmesh):
    if femmesh.VolumeCount == 0 and femmesh.FaceCount > 0:  # face femmesh
        return True


def is_edge_femmesh(femmesh):
    if femmesh.VolumeCount == 0 and femmesh.FaceCount == 0 and femmesh.EdgeCount > 0:  # edge femmesh
        return True


def get_three_non_colinear_nodes(nodes_coords):
    # Code to obtain three non-colinear nodes on the PlaneRotation support face
    # nodes_coords --> [(nodenumber, x, y, z), (nodenumber, x, y, z), ...]
    if not nodes_coords:
        print(len(nodes_coords))
        print('Error: No nodes in nodes_coords')
        return []
    dum_max = [1, 2, 3, 4, 5, 6, 7, 8, 0]
    for i in range(len(nodes_coords)):
        for j in range(len(nodes_coords) - 1 - i):
            x_1 = nodes_coords[j][1]
            x_2 = nodes_coords[j + 1][1]
            y_1 = nodes_coords[j][2]
            y_2 = nodes_coords[j + 1][2]
            z_1 = nodes_coords[j][3]
            z_2 = nodes_coords[j + 1][3]
            node_1 = nodes_coords[j][0]
            node_2 = nodes_coords[j + 1][0]
            distance = ((x_1 - x_2) ** 2 + (y_1 - y_2) ** 2 + (z_1 - z_2) ** 2) ** 0.5
            if distance > dum_max[8]:
                dum_max = [node_1, x_1, y_1, z_1, node_2, x_2, y_2, z_2, distance]
    node_dis = [1, 0]
    for i in range(len(nodes_coords)):
        x_1 = dum_max[1]
        x_2 = dum_max[5]
        x_3 = nodes_coords[i][1]
        y_1 = dum_max[2]
        y_2 = dum_max[6]
        y_3 = nodes_coords[i][2]
        z_1 = dum_max[3]
        z_2 = dum_max[7]
        z_3 = nodes_coords[i][3]
        node_3 = int(nodes_coords[j][0])
        distance_1 = ((x_1 - x_3) ** 2 + (y_1 - y_3) ** 2 + (z_1 - z_3) ** 2) ** 0.5
        distance_2 = ((x_3 - x_2) ** 2 + (y_3 - y_2) ** 2 + (z_3 - z_2) ** 2) ** 0.5
        tot = distance_1 + distance_2
        if tot > node_dis[1]:
            node_dis = [node_3, tot]
    node_1 = int(dum_max[0])
    node_2 = int(dum_max[4])
    print([node_1, node_2, node_3])
    return [node_1, node_2, node_3]


def make_femmesh(mesh_data):
    ''' makes an FreeCAD FEM Mesh object from FEM Mesh data
    '''
    import Fem
    mesh = Fem.FemMesh()
    m = mesh_data
    if ('Nodes' in m) and (len(m['Nodes']) > 0):
        print("Found: nodes")
        if (('Seg2Elem' in m) or
           ('Tria3Elem' in m) or
           ('Tria6Elem' in m) or
           ('Quad4Elem' in m) or
           ('Quad8Elem' in m) or
           ('Tetra4Elem' in m) or
           ('Tetra10Elem' in m) or
           ('Penta6Elem' in m) or
           ('Penta15Elem' in m) or
           ('Hexa8Elem' in m) or
           ('Hexa20Elem' in m)):

            nds = m['Nodes']
            print("Found: elements")
            for i in nds:
                n = nds[i]
                mesh.addNode(n[0], n[1], n[2], i)
            elms_hexa8 = m['Hexa8Elem']
            for i in elms_hexa8:
                e = elms_hexa8[i]
                mesh.addVolume([e[0], e[1], e[2], e[3], e[4], e[5], e[6], e[7]], i)
            elms_penta6 = m['Penta6Elem']
            for i in elms_penta6:
                e = elms_penta6[i]
                mesh.addVolume([e[0], e[1], e[2], e[3], e[4], e[5]], i)
            elms_tetra4 = m['Tetra4Elem']
            for i in elms_tetra4:
                e = elms_tetra4[i]
                mesh.addVolume([e[0], e[1], e[2], e[3]], i)
            elms_tetra10 = m['Tetra10Elem']
            for i in elms_tetra10:
                e = elms_tetra10[i]
                mesh.addVolume([e[0], e[1], e[2], e[3], e[4], e[5], e[6], e[7], e[8], e[9]], i)
            elms_penta15 = m['Penta15Elem']
            for i in elms_penta15:
                e = elms_penta15[i]
                mesh.addVolume([e[0], e[1], e[2], e[3], e[4], e[5], e[6], e[7], e[8], e[9],
                                e[10], e[11], e[12], e[13], e[14]], i)
            elms_hexa20 = m['Hexa20Elem']
            for i in elms_hexa20:
                e = elms_hexa20[i]
                mesh.addVolume([e[0], e[1], e[2], e[3], e[4], e[5], e[6], e[7], e[8], e[9],
                                e[10], e[11], e[12], e[13], e[14], e[15], e[16], e[17], e[18], e[19]], i)
            elms_tria3 = m['Tria3Elem']
            for i in elms_tria3:
                e = elms_tria3[i]
                mesh.addFace([e[0], e[1], e[2]], i)
            elms_tria6 = m['Tria6Elem']
            for i in elms_tria6:
                e = elms_tria6[i]
                mesh.addFace([e[0], e[1], e[2], e[3], e[4], e[5]], i)
            elms_quad4 = m['Quad4Elem']
            for i in elms_quad4:
                e = elms_quad4[i]
                mesh.addFace([e[0], e[1], e[2], e[3]], i)
            elms_quad8 = m['Quad8Elem']
            for i in elms_quad8:
                e = elms_quad8[i]
                mesh.addFace([e[0], e[1], e[2], e[3], e[4], e[5], e[6], e[7]], i)
            elms_seg2 = m['Seg2Elem']
            for i in elms_seg2:
                e = elms_seg2[i]
                mesh.addEdge(e[0], e[1])
            print("imported mesh: {} nodes, {} HEXA8, {} PENTA6, {} TETRA4, {} TETRA10, {} PENTA15".format(
                  len(nds), len(elms_hexa8), len(elms_penta6), len(elms_tetra4), len(elms_tetra10), len(elms_penta15)))
            print("imported mesh: {} HEXA20, {} TRIA3, {} TRIA6, {} QUAD4, {} QUAD8, {} SEG2".format(
                  len(elms_hexa20), len(elms_tria3), len(elms_tria6), len(elms_quad4), len(elms_quad8), len(elms_seg2)))
        else:
            FreeCAD.Console.PrintError("No Elements found!\n")
    else:
        FreeCAD.Console.PrintError("No Nodes found!\n")
    return mesh
