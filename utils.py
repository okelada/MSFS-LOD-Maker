
import bpy
import re
from collections import defaultdict
from bisect import bisect_left
from mathutils import Vector,Matrix
import addon_utils
import bmesh

class LODIFY_list:
    ui_lod_collection = None
    ui_lod_level = -1

def force_solid_shading():
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if(area.type == 'VIEW_3D'):
                for space in area.spaces:
                    if(space.type == 'VIEW_3D'):
                        if(space.shading.type != 'SOLID'):
                            space.shading.type = 'SOLID'
                        if space.shading.color_type != 'VERTEX':
                            space.shading.color_type = 'VERTEX'

def force_material_shading():
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if(area.type == 'VIEW_3D'):
                for space in area.spaces:
                    if(space.type == 'VIEW_3D'):
                        if(space.shading.type != 'MATERIAL'):
                            space.shading.type = 'MATERIAL'


def get_lod_list(base_collection):
    base_name = get_root_name_from_ID(base_collection)
    return get_named_lod_list(base_name)

def get_named_lod_list(base_name):   
    lod_list = []
    for i in range(4):
        lod_coll_name = f"{base_name}_LOD{i:02d}"
        lod_coll = bpy.data.collections.get(lod_coll_name)
        if lod_coll:
            lod = LODIFY_list()
            lod.ui_lod_collection = lod_coll
            lod.ui_lod_level = i
            lod_list.append(lod)
    return lod_list

def get_generated_lod_list(base_name = None):   
    lod_list = bpy.context.window_manager.lod_list
    if base_name: #load selected on the fly
        new_lod_list = get_named_lod_list(base_name)
        lod_list.clear()
        for new_lod in new_lod_list:    
            item = lod_list.add()
            item.ui_lod_collection = new_lod.ui_lod_collection
            item.ui_lod_level = new_lod.ui_lod_level
    return lod_list


#io_scene_gltf2_msfs_2024
def list_all_addon_modules():
    modules = addon_utils.modules()
    for module in modules:
        module_name = module.__name__
        bl_info_name = getattr(module, "bl_info", {}).get("name", "Unknown Name")
        bl_info_version = getattr(module, "bl_info", {}).get("version", "0.0.0")
        is_enabled = addon_utils.check(module_name)[1]
        status = "Enabled" if is_enabled else "Disabled"
        print(f"{module_name}: {bl_info_name} {bl_info_version} — {status}")


def make_collection_active(collection):
    layer_collection = find_layer_collection(collection,bpy.context.view_layer.layer_collection)
    if layer_collection:#CHECKME
        layer_collection.exclude = False
        bpy.context.view_layer.active_layer_collection = layer_collection
        children_collections_flat = list(collection.children_recursive)
        for child_coll in children_collections_flat:
            child_layer_collection = find_layer_collection(child_coll,layer_collection)
            child_layer_collection.exclude = False
            bpy.context.view_layer.active_layer_collection = child_layer_collection
        return True
    return False


def remove_collision_boxes_to_generated_objects(base_name):
    lod_list = get_named_lod_list(base_name)
    for lod in lod_list:
        coll = lod.ui_lod_collection
        if coll:#CHECKME
            make_collection_active(coll)
            children_objects_flat = list(coll.all_objects)
            old_gizmo_objects_flat = []
            for child in children_objects_flat:
                if child.type == 'MESH':
                    for child_child in  child.children:
                        if is_asobo_gizmo(child_child):
                                old_gizmo_objects_flat.append(child_child)
            for gizmo in old_gizmo_objects_flat:
                bpy.data.objects.remove(gizmo,do_unlink=True,do_id_user=True,do_ui_user=True)


def is_asobo_gizmo(obj):
    if obj.type == 'EMPTY' and obj.name.startswith("Collision_Box_"):
        doc = bpy.ops.msfs2024.add_gizmo._get_doc()
        if "msfs_gizmo_type" in doc and  obj.msfs_gizmo_type == 'box':
            return True
        elif obj.original.display_bounds_type == 'BOX': #SU5 SDK > 1.6.4
            return True
    return False


def add_collision_boxes_to_generated_collections(base_name,lod0Only):
    lod_list = get_named_lod_list(base_name)
    bpy.ops.object.select_all(action='DESELECT')

    for lod in lod_list:
        if lod0Only and lod.ui_lod_level != 0:
            continue
        coll = lod.ui_lod_collection
        make_collection_active(coll)

        for child_obj in list(coll.all_objects):
            if is_asobo_gizmo(child_obj):
                bpy.data.objects.remove(child_obj,do_unlink=True,do_id_user=True,do_ui_user=True)
        children_collections_flat = [coll] + list(coll.children_recursive)
        for c in children_collections_flat:
            if len(c.objects) == 0:
                continue
            position,sizes = calculate_ID_bounds(c)
            for child_obj in c.all_objects:
                if child_obj.type == 'MESH':
                    child_obj.select_set(True)
                    bpy.context.view_layer.objects.active = child_obj
                    doc = bpy.ops.msfs2024.add_gizmo._get_doc()
                    if "msfs_gizmo_type" in doc:
                        bpy.ops.msfs2024.add_gizmo(msfs_gizmo_type = 'box')
                    else:
                        bpy.ops.msfs2024.add_gizmo(gizmo_type = 'BOX') #SU5 SDK > 1.6.4
                    gizmo =  bpy.context.view_layer.objects.active
                    gizmo.name = "Collision_Box_" + c.name
                    gizmo.location = Vector(position)
                    gizmo.scale = Vector(sizes)/2.0
                    break


def add_collision_boxes_to_generated_objects(base_name,lod0Only):
    lod_list = get_named_lod_list(base_name)
    bpy.ops.object.select_all(action='DESELECT')

    for lod in lod_list:
        if lod0Only and lod.ui_lod_level != 0:
            continue
        coll = lod.ui_lod_collection
        make_collection_active(coll)
        children_objects_flat = list(coll.all_objects)
        gizmo_objects_flat = []
        for child in children_objects_flat:
            if child.type == 'MESH':
                for child_child in  child.children:
                    #if child_child.type == 'EMPTY' and child_child.original.display_bounds_type == 'BOX' and child_child.name.startswith("Collision_Box_"):
                    #if child_child.type == 'EMPTY' and child_child.msfs_gizmo_type == 'box' and child_child.name.startswith("Collision_Box_"):
                    if is_asobo_gizmo(child_child):
                        gizmo_objects_flat.append(child_child)
                child.select_set(True)
                bpy.context.view_layer.objects.active = child        
                bpy.ops.msfs2024.add_gizmo(msfs_gizmo_type = 'box') 
                #bpy.ops.msfs2024.add_gizmo(gizmo_type = 'BOX')
                bpy.context.view_layer.objects.active.name = "Collision_Box_" + child.name
        for gizmo in gizmo_objects_flat:
            bpy.data.objects.remove(gizmo,do_unlink=True,do_id_user=True,do_ui_user=True)




def is_ID_collection_child(_id,base_collection):
    children_collections_flat = list(base_collection.children_recursive)
    children_objects_flat = list(base_collection.all_objects)
    if type(_id) is bpy.types.Collection and _id in children_collections_flat:
        return True    
    if type(_id) is bpy.types.Object and _id in children_objects_flat:
        return True    
    return False


def set_msfs_multi_exporter_lod_values(base_collection, forced_lod_values = None):
    """
    Set LOD values in the MSFS Multi-Export addon.
    Args:
        base_collection_name: Name of the base collection (without _LOD00 suffix)
        lod_values: List of 4 LOD values to set
    """
    try:
        print(f"=== Setting MSFS LOD Values ===")
        # Check if MSFS Multi-Export addon is available
        if not hasattr(bpy.context.scene, 'msfs_multi_exporter_lod_groups'):
            print("ERROR: MSFS Multi-Export addon not found or not enabled")
            return False
        
        msfs_lod_groups = bpy.context.scene.msfs_multi_exporter_lod_groups
        print(f"Found {len(msfs_lod_groups)} existing LOD groups in MSFS Multi-Export")
        
        # Find or create the LOD group for this collection
        base_root_name = get_root_name_from_ID(base_collection)
        generated_lods = list(get_generated_lod_list(base_root_name))

        for msfs_lod_group in msfs_lod_groups:    
            if not msfs_lod_group or not msfs_lod_group.lods or len(msfs_lod_group.lods) == 0:
                continue
            
            linked_id = None
            if msfs_lod_group.lods[0].collection == base_collection:
                linked_id = base_collection
            else:
                if msfs_lod_group.lods[0].collection is None:
                    if msfs_lod_group.lods[0].objectLOD is None:
                        print(f"Ignoring LOD group: '{msfs_lod_group.name}' , empty")
                        if hasattr(msfs_lod_group, 'enabled'):
                            msfs_lod_group.enabled = False
                        continue
                    else:
                        linked_id = msfs_lod_group.lods[0].objectLOD
                else:
                    linked_id = msfs_lod_group.lods[0].collection

                if not is_ID_collection_child(linked_id,base_collection):
                    print(f"Ignoring LOD group: '{msfs_lod_group.name}' , not our Lod")
                    if hasattr(msfs_lod_group, 'enabled'):
                        msfs_lod_group.enabled = False
                    continue
            
            if forced_lod_values is None:
                lod_values,obj_size = get_lod_values(bpy.context,linked_id) #caculated or manual
            else:
                lod_values = forced_lod_values

            # Enable the LOD group (if it has the enabled attribute)
            if hasattr(msfs_lod_group, 'enabled'):
                msfs_lod_group.enabled = True
                print(f"Enabled LOD group: '{msfs_lod_group.name}'")
            else:
                print(f"Warning: LOD group doesn't have 'enabled' attribute - MSFS Multi-Export version mismatch")
                return False
            # Ensure we have 4 LOD entries (if lods attribute exists)
            if hasattr(msfs_lod_group, 'lods'):
                while len(msfs_lod_group.lods) < max(4,len(generated_lods)):
                    msfs_lod_group.lods.add()
                    print(f"Added LOD entry, now have {len(msfs_lod_group.lods)} LODs")
                
                print(f"LOD group '{msfs_lod_group.name}' now has {len(msfs_lod_group.lods)} LOD entries")
                # Set the LOD values and verify they're set
                i = 0
                for lod_item in generated_lods:
                    addon_lod_level = lod_item.ui_lod_level
                    value = lod_values[addon_lod_level]
                    #lod_base_collection_name = root_name + f"_LOD{i:02d}"
                    if value != -1.0 and i < len(msfs_lod_group.lods) and hasattr(msfs_lod_group.lods[i], 'lod_value'):
                        msfs_lod_group.lods[i].lod_value = value
                        new_value = getattr(msfs_lod_group.lods[i], 'lod_value', 0.0)
                        # Verify the value was set correctly
                        if abs(new_value - value) > 0.001:
                            print(f"WARNING: LOD{i} value not set correctly! Expected {value}, got {new_value}")
                        msfs_lod_group.lods[i].enabled = True
                    else:
                        print(f"WARNING: LOD{i} entry missing or no lod_value attribute")
                    i += 1
                # Force an update of the UI
                try:
                    bpy.context.area.tag_redraw()
                except:
                    pass
                
                #Final verification
                print(f"=== Final LOD Values ===")
                for i in range(4):
                    if i < len(msfs_lod_group.lods) and hasattr(msfs_lod_group.lods[i], 'lod_value'):
                        print(f"LOD{i}: {msfs_lod_group.lods[i].lod_value:.01f}")
                    else:
                        print(f"LOD{i}: NOT SET")
            else:
                print(f"Warning: LOD group doesn't have 'lods' attribute - MSFS Multi-Export version mismatch")
                return False
        bpy.ops.msfs2024.reload_lod_groups() #1.6.4 compat
        print(f"Successfully set MSFS LOD values for '{base_root_name}' and children")
        return True
        
    except Exception as e:
        print(f"ERROR setting MSFS Multi-Export LOD values: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def merge_vertices_by_distance(obj, context,lod_level):
    """Merge vertices by distance for the given object."""
    if not obj.type == 'MESH':
        return

    match lod_level:
        case 1:
            merge_threshold = context.scene.lod.lod1_merge_threshold 
        case 2:
            merge_threshold = context.scene.lod.lod2_merge_threshold 
        case 3:
            merge_threshold = context.scene.lod.lod3_merge_threshold
    if merge_threshold > 0.0:
        # if context.view_layer.objects.active:
        #     bpy.ops.object.mode_set(mode='OBJECT')
        # bpy.ops.object.select_all(action='DESELECT')
        # obj.select_set(True)
        # context.view_layer.objects.active = obj
        # # Enter edit mode and merge vertices by distance
        # bpy.ops.object.mode_set(mode='EDIT')
        # bpy.ops.mesh.select_mode(type='VERT')
        # bpy.ops.mesh.select_all(action='SELECT')
        # bpy.ops.mesh.remove_doubles(threshold=merge_threshold)  # 0.0001m threshold
        # bpy.ops.object.mode_set(mode='OBJECT')
        

        bm = bmesh.new()
        m  = obj.data
        bm.from_mesh(m)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=merge_threshold)
        bm.to_mesh(m)
        m.update()
        bm.clear()
        bm.free()
        print(f"    Merged vertices by distance ({merge_threshold}m) for {obj.name}")




def get_parents_of_id(id):
    collections_in_scene = [c for c in bpy.data.collections if bpy.context.scene.user_of_id(c)]
    parents = [c for c in collections_in_scene if c.user_of_id(id)]
    return parents

def find_base_collection(strict = False):
    """Find the first outliner selected LODNN collection in the current scene."""
    selected_collection = None

    scr = bpy.context.screen
    areas = [area for area in scr.areas if area.type == 'OUTLINER']
    regions = [region for region in areas[0].regions if region.type == 'WINDOW']

    #try with the outliner selected one
    if hasattr(bpy.context,'selected_ids'):
        with bpy.context.temp_override(area=areas[0], region=regions[0], screen=scr):
            if len(bpy.context.selected_ids) > 0:
                if type(bpy.context.selected_ids[0]) == bpy.types.Collection:
                    selected_collection = bpy.context.selected_ids[0]
                elif type(bpy.context.selected_ids[0]) == bpy.types.Object:
                    selected_collection =  bpy.context.selected_ids[0].users_collection[0]

    if not selected_collection:
        if bpy.context.active_object:
            selected_collection = bpy.context.active_object.users_collection[0]

    if not selected_collection: #try with the active one
        selected_collection = bpy.context.view_layer.active_layer_collection.collection

    if not selected_collection:
        return None,None
    
    collections_in_scene = [c for c in bpy.data.collections if bpy.context.scene.user_of_id(c)]

    if selected_collection and re.search(r"_LOD00$" if strict else r"_LOD\d{2}$",selected_collection.name):
        lod_ending = selected_collection.name[-6:]
        while True:
            parents = [c for c in collections_in_scene if c.user_of_id(selected_collection)]
            if len(parents) and parents[0].name.endswith(lod_ending):
                selected_collection = parents[0]
            else:
                break

        selected_base_name = get_root_name_from_ID(selected_collection)
        #print(f"Found selected LODNN collection: '{selected_collection.name}'")
        selected_collection = bpy.data.collections.get(selected_base_name + "_LOD00")

        if selected_collection:
            parents = [c for c in collections_in_scene if c.user_of_id(selected_collection)]
            parent = parents[0] if len(parents) > 0 else None
            if parent is None and bpy.context.scene.collection.user_of_id(selected_collection):
                parent = bpy.context.scene.collection
            return selected_collection,parent
    
    #print("No selected LODNN collection found")
    return None,None


def reform_object_names():
    #eliminate .001 cases after duplication / process
    #it can't be just pruned off as the name exists somewhere else
    #shouldn't affect collections
    generated_lods = list(get_generated_lod_list())
    children_objects_flat_list = []
    lod_level_list = []
    
    for lod in generated_lods: 
        lod_collection = lod.ui_lod_collection
        lod_level = lod.ui_lod_level
        lod_level_list.append(lod_level)
        children_objects_flat = list(lod_collection.all_objects)
        children_objects_flat.sort(key=lambda obj: obj.name)
        children_objects_flat_list.append(children_objects_flat)

    num_lod_levels = len(lod_level_list)
    lod0_children_objects_flat = children_objects_flat_list[0]
    num_children_objects = len(lod0_children_objects_flat)
    troubled_name_collections = {}

    for i in range(num_children_objects):     
        o_names = []
        needs_reform = False
        for j in range(num_lod_levels):
            o = children_objects_flat_list[j][i]
            o_names.append(o.name)
            level = lod_level_list[j]
            if not o.name.endswith(f"_LOD{level:02d}"):
                needs_reform = True  
                print(f"obj l{level}:{i} {o.name} needs reform")
        if needs_reform:
            troubled_name_collections[(i,j)] = o_names
    
    for k in troubled_name_collections:
        names = troubled_name_collections[k]
        i,j = k
        root_name = get_root_name(names[0])
        tries = 0
        while tries < 99:     
            name_is_free = True
            tries += 1
            for ll in lod_level_list:
                new_name = root_name +f"_{tries:03d}_LOD{ll:02d}"
                if new_name in bpy.data.objects or new_name in bpy.data.collections:#look everywhere
                    name_is_free = False
                    break
            if name_is_free:
                for ll in range(num_lod_levels):
                    level = lod_level_list[ll]
                    new_name = root_name + f"_{tries:03d}_LOD{level:02d}"
                    print(f"reform {children_objects_flat_list[ll][i].name} -> {new_name}")
                    children_objects_flat_list[ll][i].name = new_name
                break

                   
def is_same_name_root(name0,name1):
        root0 = name0.split('.')[0]
        root1 = name1.split('.')[0]
        return root0 == root1

def get_root_name(name):
    #strip auto copy suffix from duplication
    nn = name
    if re.search(r".\d{3}$",nn) and "_LOD" in nn: #if duplicated suffix, remove it
        nn = nn[:-4]

    nn =  nn.replace('.', '_') # just in case, msfs export incompatible
    nn = nn.rstrip('_')

    #check if already lodified
    lodpos = re.search(r"_LOD\d{2}$",nn)
    if lodpos:
        nn = nn[0:lodpos.start()] #strip lod suffix for now

    if lodpos:
        nn = nn[0:lodpos.start()] #strip lod suffix for now

    lodpos = re.search(r"_\d{3}$",nn)
    while lodpos:
        nn = nn[:-4]
        lodpos = re.search(r"_\d{3}$",nn)

    return nn

def get_root_name_from_ID(id):
    if not id:
        return None
    return get_root_name(id.name)


def lodify_name(id,lod_level):
    if type(id) is bpy.types.Collection:
        id.color_tag = f'COLOR_0{lod_level+1}'

    stripped_name = get_root_name(id.name)
    insert_token = ''

    if lod_level == 0:
        insert_token = bpy.context.scene.lod.insert_token
        if insert_token != '' and not stripped_name.endswith(insert_token):
            insert_token = "_" + insert_token.replace('.', '_')
        else:
            insert_token = ''

    new_name = stripped_name + insert_token + f"_LOD{lod_level:02d}" #new lod suffix

    if type(id) is bpy.types.Object:
        while True:
            if new_name in bpy.data.objects:
                oldobj = bpy.data.objects[new_name]
                if oldobj.users == 0:
                    bpy.data.objects.remove(oldobj, do_unlink=True,do_id_user=True,do_ui_user= True)#try to set the name free
                    break
                else:
                    print(f"----- obj name:{new_name} already present somewhere")#blender will add.001,we will fix later
                    break
            else:
                break
    if type(id) is bpy.types.Collection:
        while True:
            if new_name in bpy.data.collections:
                oldcoll = bpy.data.collections[new_name]
                if oldcoll.users == 0:
                    bpy.data.collections.remove(oldcoll,do_unlink=True,do_id_user=True,do_ui_user= True)#try to set the name free
                    break
                else:
                   print(f"----- obj name:{new_name} already present somewhere")#blender will add.001,we will fix later
                   break
            else:
                break
        #id.color_tag = f'COLOR_0{lod_level+1}'
    id.name = new_name


def remove_lod_collection(base_name,lod_level):
    lod_name = f"{base_name}_LOD{lod_level:02d}"
    #print(f"Removing LOD collection: '{lod_name}'")
    lod_collection = bpy.data.collections.get(lod_name)
    if lod_collection:
        for obj in lod_collection.objects:
            bpy.data.objects.remove(obj, do_unlink=True,do_id_user=True,do_ui_user= True)
        for childcoll in lod_collection.children_recursive:
            for obj in childcoll.objects:
                bpy.data.objects.remove(obj, do_unlink=True,do_id_user=True,do_ui_user= True)
            bpy.data.collections.remove(childcoll,do_unlink=True,do_id_user=True,do_ui_user= True)
            
        bpy.data.collections.remove(lod_collection,do_unlink=True,do_id_user=True,do_ui_user= True)

        for block in bpy.data.meshes:
            if block.users == 0:
                bpy.data.meshes.remove(block,do_unlink=True,do_id_user=True,do_ui_user= True)

        for block in bpy.data.lights:
            if block.users == 0:
                bpy.data.lights.remove(block,do_unlink=True,do_id_user=True,do_ui_user= True)

        for block in bpy.data.materials:
            if block.users == 0:
                bpy.data.materials.remove(block,do_unlink=True,do_id_user=True,do_ui_user= True)

        for block in bpy.data.textures:
            if block.users == 0:
                bpy.data.textures.remove(block,do_unlink=True,do_id_user=True,do_ui_user= True)

        for block in bpy.data.images:
            if block.users == 0:
                bpy.data.images.remove(block,do_unlink=True,do_id_user=True,do_ui_user= True)

        lod_list = list(get_generated_lod_list())
        lod_list[:] = [x for x in lod_list if x.ui_lod_level == lod_level]
        for lod in lod_list:
            lod_list.remove(lod)


#https://blenderartists.org/t/modifying-object-origin-with-python/507305/7
def set_mesh_origin(ob, pos):
    '''Given a mesh object set it's origin to a given position.'''
    # Casting pos to vector so you can pass in tuples or lists
    pos = Vector(pos)
    mat = Matrix.Translation(pos - ob.location)
    ob.location = pos
    ob.data.transform(mat.inverted())
    ob.data.update()

def reparent_child(child,new_parent):
    # parent_inverse_world_matrix = new_parent.matrix_world.inverted()
    # child.parent = new_parent
    # child.matrix_parent_inverse =  parent_inverse_world_matrix @ child.matrix_world
    child.parent = new_parent 
    child.matrix_parent_inverse = new_parent.matrix_world.inverted()

def unparent_child(child):
    parented_wm = child.matrix_world.copy()
    child.parent = None
    child.matrix_world = parented_wm


#https://blender.stackexchange.com/questions/104886/how-do-i-copy-children-of-an-object-using-copy-method-without-messing-up-thei
def copy_ob(ob, parent, collection):
    copy = ob.copy()
    if parent:
        copy.parent = parent
        copy.matrix_parent_inverse = ob.matrix_parent_inverse.copy()

    if ob.data:
        copy.data = ob.data.copy()
    if ob.animation_data:
        copy.animation_data.action = ob.animation_data.action.copy()

    for ps in copy.particle_systems:
        ps.settings = ps.settings.copy()
    if collection:
        collection.objects.link(copy)
    return copy

def tree_copy(ob, root_parent, collection):
    def recurse(ob, parent, collection):
        copy = copy_ob(ob, parent,collection)
        for child in ob.children:
            recurse(child, copy, collection)
    recurse(ob, root_parent,collection)


def duplicate_collection(new_collection, parent_collection,source_collection,linked=False):
    dupe_lut = defaultdict(lambda : None)
    def _copy_coll(new_coll,parent_coll,source_coll, linked=False):
        if not new_coll:
            new_coll = bpy.data.collections.new(source_coll.name)

        root_objs = [o for o in source_coll.objects if o.parent == None]
        for obj in root_objs:
            tree_copy(obj,None,new_coll)

        if not parent_coll.children is None and new_coll not in list(parent_coll.children):
            parent_coll.children.link(new_coll)

        for c in source_coll.children:
            _copy_coll(None,new_coll, c, linked)

        return new_coll

    new_collection = _copy_coll(new_collection,parent_collection, source_collection, linked)

    for obj, dupe in tuple(dupe_lut.items()):
        parent_collection = dupe_lut[obj.parent]
        if parent_collection:
            dupe.parent = parent_collection
    return new_collection

def remove_unused_shrinkwrap_targets():
    for obj in bpy.data.objects:
        if "_SHRINKWRAP_TARGET" in obj.name and obj.users == 0:
            bpy.data.objects.remove(obj, do_unlink=True) 

minSizes_FS2024 = [[150, 300, 2500, 5000, 30000, 60000, 150000, 250000, 500000, 1000000, 2000000],#nvertices
[0,1,5,7,18,25,39,50,71,100,142],# Ultra	
[0,1,9,14,34,49,77,100,141,200,283],# High 
[0,2,18,28,68,98,154,200,282,400,566],# Medium	
[0,4,36,56,136,196,308,400,564,800,1132]]# Low

default_lod_values = [4.0, 3.0, 2.0, 1.0]

#https://stackoverflow.com/questions/50508262/using-look-up-tables-in-python
def lookup(x, xs, ys):
    if x <= xs[0]:  return ys[0]
    if x >= xs[-1]: return ys[-1]

    i = bisect_left(xs, x)
    k = (x - xs[i-1])/(xs[i] - xs[i-1])
    y = k*(ys[i]-ys[i-1]) + ys[i-1]
    return y


def get_ID_Totals(context,id):
    if not id:
        return (0,0,0)

    sumvertices = 0
    sumpolygons = 0
    summaterials = 0
    
    try:
        depsgraph = context.evaluated_depsgraph_get()  
        if not depsgraph:
            return (0,0,0)
        
        if type(id) is bpy.types.Collection:
            for obj in id.all_objects:
                if obj.type == 'MESH':
                    object_eval = obj.evaluated_get(depsgraph)
                    numvertices = len(object_eval.data.vertices)
                    sumvertices += numvertices
                    numpolygons = len(object_eval.data.polygons)
                    sumpolygons += numpolygons
                    nummaterials = len(object_eval.data.materials)
                    summaterials += nummaterials
        elif type(id) is bpy.types.Object:
            if id.type == 'MESH':
                object_eval = id.evaluated_get(depsgraph)
                numvertices = len(object_eval.data.vertices)
                sumvertices += numvertices
                numpolygons = len(object_eval.data.polygons)
                sumpolygons += numpolygons
                nummaterials = len(object_eval.data.materials)
                summaterials += nummaterials
    except:
        pass
    return (sumvertices,sumpolygons,summaterials)



def update_stats_report_and_minsizes(context,base_name):
    stats_report = []
    for i in range(4):

        coll = bpy.data.collections.get(base_name + f"_LOD{i:02d}")
        if not coll is None and context.scene.user_of_id(coll):
            sumvertices,sumpolygons,summaterials = get_ID_Totals(context,coll)
            level_totals = list((sumvertices,sumpolygons,summaterials))
            stats_report.append(level_totals)
        else:
            stats_report.append((-1.0,-1.0,-1.0))

    return stats_report

def calculate_ID_bounds(id):
    """
    Calculate the bounding box dimensions of all objects in a collection.
    Returns the maximum dimension (length, width, or height) in meters.
    """
    if not id:
        return 0.0
    
    min_coords = Vector((float('inf'), float('inf'), float('inf')))
    max_coords = Vector((float('-inf'), float('-inf'), float('-inf')))
    
    if type(id) is bpy.types.Collection:
        for obj in id.all_objects:
            if obj.type == 'MESH':
                # Get object's bounding box in world coordinates
                bbox_corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
                for corner in bbox_corners:
                    min_coords.x = min(min_coords.x, corner.x)
                    min_coords.y = min(min_coords.y, corner.y)
                    min_coords.z = min(min_coords.z, corner.z)
                    max_coords.x = max(max_coords.x, corner.x)
                    max_coords.y = max(max_coords.y, corner.y)
                    max_coords.z = max(max_coords.z, corner.z)
    elif type(id) is bpy.types.Object:
        if id.type == 'MESH':
             # Get object's bounding box in world coordinates
            bbox_corners = [id.matrix_world @ Vector(corner) for corner in id.bound_box]
            for corner in bbox_corners:
                min_coords.x = min(min_coords.x, corner.x)
                min_coords.y = min(min_coords.y, corner.y)
                min_coords.z = min(min_coords.z, corner.z)
                max_coords.x = max(max_coords.x, corner.x)
                max_coords.y = max(max_coords.y, corner.y)
                max_coords.z = max(max_coords.z, corner.z)
    
    if min_coords.x == float('inf'):
        return 0.0
    
    position = (max_coords + min_coords)/2
    
    dimensions = max_coords - min_coords
    return (position.x,position.y,position.z),(dimensions.x, dimensions.y, dimensions.z)


def calculate_optimal_lod_values(object_size_meters):
    """
    Calculate optimal LOD values based on MSFS 2024 documentation and object size.
    
    The LOD values represent screen percentage when each LOD becomes visible.
    In MSFS, higher values mean the LOD is visible at greater distances.
    The pattern follows: LOD0 (highest value) > LOD1 > LOD2 > LOD3 (lowest value)
    
    Args:
        object_size_meters: Maximum dimension of the object in meters
    
    Returns:
        List of 4 LOD values [LOD0, LOD1, LOD2, LOD3]
    """
    
    # Base LOD values for medium-sized objects (around 5-20m)
    # These values follow the correct MSFS pattern: descending values
    base_lod_values = [12.0, 3.0, 2.0, 0.5]
    
    # Calculate scaling factor based on object size
    # Larger objects should be visible from further away (higher LOD values)
    # Smaller objects can disappear sooner (lower LOD values)
    if object_size_meters < 0.5:
        # Very small objects (< 0.5m) - disappear quickly
        scaling_factor = 0.3
    elif object_size_meters < 1.0:
        # Small objects (0.5-1m)
        scaling_factor = 0.5
    elif object_size_meters < 2.0:
        # Small-medium objects (1-2m)
        scaling_factor = 0.7
    elif object_size_meters < 5.0:
        # Medium objects (2-5m)
        scaling_factor = 0.85
    elif object_size_meters < 10.0:
        # Medium-large objects (5-10m) - use base values
        scaling_factor = 1.0
    elif object_size_meters < 20.0:
        # Large objects (10-20m)
        scaling_factor = 1.2
    elif object_size_meters < 50.0:
        # Very large objects (20-50m)
        scaling_factor = 1.5
    else:
        # Massive objects (>50m) - stay visible much longer
        scaling_factor = 2.0
    
    # Apply scaling to base values
    lod_values = [
        max(1.0, base_lod_values[0] * scaling_factor),  # LOD0 - minimum 1.0
        max(0.8, base_lod_values[1] * scaling_factor),  # LOD1 - minimum 0.8
        max(0.6, base_lod_values[2] * scaling_factor),  # LOD2 - minimum 0.6
        max(0.4, base_lod_values[3] * scaling_factor)   # LOD3 - minimum 0.4
    ]
    
    # Ensure descending order (LOD0 > LOD1 > LOD2 > LOD3)
    for i in range(1, len(lod_values)):
        if lod_values[i] >= lod_values[i-1]:
            lod_values[i] = lod_values[i-1] * 0.8  # Make it 20% smaller than previous
    
    # Round to reasonable precision
    lod_values = [round(val, 1) for val in lod_values]
    
    return lod_values


def calculate_optimal_lod_values_SDK_Curves(id):
    minsize0,minsize1,minsize2,minsize3 = -1.0,-1.0,-1.0,-1.0
    id0,id1,id2,id3 = None,None,None,None

    maxvertices = minSizes_FS2024[0]
    integer_value = bpy.context.scene.lod.get("lod_minsizes_quality", 1)
    minsizes_percent = minSizes_FS2024[int(integer_value+1)]

    root_name = get_root_name_from_ID(id)

    if type(id) == bpy.types.Object:
        id0 = bpy.data.objects.get(root_name + "_LOD00")
        id1 = bpy.data.objects.get(root_name + "_LOD01")
        id2 = bpy.data.objects.get(root_name + "_LOD02")
        id3 = bpy.data.objects.get(root_name + "_LOD03")
    elif type(id) == bpy.types.Collection:
        id0 = bpy.data.collections.get(root_name + "_LOD00")
        id1 = bpy.data.collections.get(root_name + "_LOD01")
        id2 = bpy.data.collections.get(root_name + "_LOD02")
        id3 = bpy.data.collections.get(root_name + "_LOD03")

    if not id0 is None:
        sumvertices,sumpolygons,summaterials = get_ID_Totals( bpy.context,id0)
        minsize0 = lookup(sumvertices, maxvertices, minsizes_percent)

    if not id1 is None:
        sumvertices,sumpolygons,summaterials = get_ID_Totals( bpy.context,id1)
        minsize1 = lookup(sumvertices, maxvertices, minsizes_percent)

    if not id2 is None:
        sumvertices,sumpolygons,summaterials = get_ID_Totals( bpy.context,id2)
        minsize2 = lookup(sumvertices, maxvertices, minsizes_percent)

    if not id3 is None:
        sumvertices,sumpolygons,summaterials = get_ID_Totals( bpy.context,id3)
        minsize3 = lookup(sumvertices, maxvertices, minsizes_percent)
  
    sdk_minSizes = [minsize0,minsize1, minsize2, minsize3]
    return sdk_minSizes



def get_lod_values(context, id):
    """
    Get LOD values either from automatic calculation or manual settings.
    Args:
        context: Blender context
        id: object or collection for size calculation
    Returns:
        tuple: List of 4 LOD values [LOD0, LOD1, LOD2, LOD3],max object size
    """
    scn = context.scene
    object_position,object_sizes = calculate_ID_bounds(id)
    object_size = max(object_sizes[0],object_sizes[1],object_sizes[2])
    if scn.lod.use_automatic_lod_calculation:
        # Use automatic calculation based on object size
        if  bpy.context.scene.lod.get("minsizes_method", 1) == 1:
            optimal_lod_values = calculate_optimal_lod_values_SDK_Curves(id)
        else:
            optimal_lod_values = calculate_optimal_lod_values(object_size)            
    else:
        # Use manual values
        try:
            manual_values = [float(x.strip()) for x in scn.lod.manual_lod_values.split(',')]
            if len(manual_values) >= 4:
                print(f"Using manual LOD values: {manual_values[:4]}")
                optimal_lod_values = manual_values[:4]
            else:
                print(f"Warning: Manual LOD values must have at least 4 values, got {len(manual_values)}. Using defaults.")
                optimal_lod_values = default_lod_values
        except ValueError as e:
            print(f"Error parsing manual LOD values: {e}. Using defaults.")
            optimal_lod_values = default_lod_values
    
    generated_lods = list(get_generated_lod_list())
    #generated_lods_len = len(generated_lods)
    generated_lods_minsizes = []
    generated_lods_levels = []

    for lod in generated_lods:
        generated_lods_minsizes.append(optimal_lod_values[lod.ui_lod_level]) 
        generated_lods_levels.append(lod.ui_lod_level) 

    generated_lods_minsizes_len = len(generated_lods_minsizes)
  
    #apply SDK2024 conditions
    if generated_lods_minsizes_len > 0:
        generated_lods_minsizes[generated_lods_minsizes_len-1] = 0.5

    if generated_lods_minsizes_len > 1:
        generated_lods_minsizes[generated_lods_minsizes_len-2] = max(1.0, generated_lods_minsizes[generated_lods_minsizes_len-2])

    for i in range(0, generated_lods_minsizes_len - 1): 
        if generated_lods_minsizes[generated_lods_minsizes_len - i - 2] <= generated_lods_minsizes[generated_lods_minsizes_len - i - 1] * 1.5:
            generated_lods_minsizes[generated_lods_minsizes_len - i - 2] = generated_lods_minsizes[generated_lods_minsizes_len - i - 1] * 1.5  # Make it 20% bigger than previous

    #reform
    modified_optimal_lod_values = []
    j = 0
    for i in range(4):
        if i not in generated_lods_levels:
            modified_optimal_lod_values.append(-1.0)
        else:
            if j < generated_lods_minsizes_len:
                modified_optimal_lod_values.append(generated_lods_minsizes[j])
                j += 1

    #bpy.context.window_manager.stats_report_minsizes = Vector(modified_optimal_lod_values)
    return modified_optimal_lod_values,object_size



def find_layer_collection(collection,root_layer_collection):
    if root_layer_collection.collection == collection:
        return root_layer_collection
    
    if root_layer_collection.children and len(root_layer_collection.children):
        for child_layer_collection in root_layer_collection.children:
            if child_layer_collection.collection == collection:
                return child_layer_collection
            found_layer_collection = find_layer_collection(collection,child_layer_collection)
            if found_layer_collection:
                return found_layer_collection 
            else:
                continue
    else:
        return None
    

def apply_modifiers(context,collection):
    applied_count = 0
    error_count = 0
    layer_collection = find_layer_collection(collection,bpy.context.view_layer.layer_collection)
    
    if not layer_collection or layer_collection.exclude:
        return 0,0
    # Store current selection and active object
    original_selection = context.selected_objects
    original_active = context.active_object
    
    # Deselect all objects first
    bpy.ops.object.select_all(action='DESELECT')
    
    # Apply modifiers to all mesh objects in the collection
    for obj in collection.all_objects:
        if obj.type == 'MESH' and obj.modifiers:
            # Set as active object
            context.view_layer.objects.active = obj
            obj.select_set(True)
            
            # Apply all modifiers
            for modifier in obj.modifiers[:]:  # Use slice to avoid iteration issues
                try:
                    #print(f"Applying modifier '{modifier.name}' to object '{obj.name}'")
                    bpy.ops.object.modifier_apply(modifier=modifier.name)
                except Exception as e:
                    print(f"Failed to apply modifier '{modifier.name}' to '{obj.name}': {str(e)}")
                    error_count += 1
            #merge_vertices_by_distance(obj, context,self.lod_index)
                applied_count += 1
            obj.select_set(False)
                
    bpy.ops.object.select_all(action='DESELECT')
    for obj in original_selection:
        if obj:
            obj.select_set(True)
    
    context.view_layer.objects.active = original_active
    
    return applied_count,error_count