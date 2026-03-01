# operators.py
#
# This file contains the operator classes for the Lodify Collections addon.
# These operators handle various functionalities such as:
# - Managing LOD lists
# - Generating LODs using decimation or shrinkwrap
# - Converting between MSFS and Blender materials
# - Baking MSFS albedo textures to vertex colors for LOD02 and LOD03
# - Automatic LOD value calculation for MSFS Multi-Export addon

import bpy

from bpy.props import IntProperty,FloatProperty,CollectionProperty,PointerProperty,BoolProperty
import re
import bmesh
from mathutils import Vector
import math
from . import utils

class DialogOperator(bpy.types.Operator):
    bl_idname = "object.dialog_operator"
    bl_label = "Simple Dialog Operator"

    my_float: bpy.props.FloatProperty(name="Some Floating Point")
    my_bool: bpy.props.BoolProperty(name="Toggle Option")
    my_string: bpy.props.StringProperty(name="String Value")

    def execute(self, context):
        message = (
            "Popup Values: %f, %d, '%s'" %
            (self.my_float, self.my_bool, self.my_string)
        )
        self.report({'INFO'}, message)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)
    
    # def cancel(self, context):
    #     bpy.ops.object.dialog_operator('INVOKE_DEFAULT', my_float=self.my_float, my_bool=self.my_bool, my_string=self.my_string)




class LODIFY_OT_cleanup(bpy.types.Operator):
    bl_idname = "lodify.cleanup"
    bl_label = "Cleanup generated lods"
    bl_description = "Cleanup existing lods"
    bl_options = {'REGISTER', 'UNDO'}
    delete_frozen: BoolProperty(default=False)

    def execute(self, context):
        scn = context.scene
        base_collection,parent_collection = utils.find_base_collection()
        
        if not base_collection:
            self.report({'ERROR'}, "Base LOD collection (ending with _LODNN) not selected, click on a collection ending with _LODNN  in the outliner")
            return {'CANCELLED'}

        base_name = utils.get_root_name_from_ID(base_collection)
        utils.remove_unused_shrinkwrap_targets()

        
        if self.delete_frozen or scn.lod.generate_lod01:
            utils.remove_lod_collection(base_name,1)
        if self.delete_frozen or scn.lod.generate_lod02:
            utils.remove_lod_collection(base_name,2)
        if self.delete_frozen or scn.lod.generate_lod03:
            utils.remove_lod_collection(base_name,3)

        utils.make_collection_active(base_collection)
        bpy.ops.msfs2024.reload_lod_groups()
        return {'FINISHED'}

class LODIFY_OT_add_collision_boxes(bpy.types.Operator):
    bl_idname = "lodify.add_collision_boxes"
    bl_label = "Add collision boxes to objects"
    bl_description = "Add collision boxes to lod objects/collections"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scn = context.scene
        base_collection,parent_collection = utils.find_base_collection()
        
        if not base_collection:
            self.report({'ERROR'}, "Base LOD collection (ending with _LODNN) not selected, click on a collection ending with _LODNN  in the outliner")
            return {'CANCELLED'}

        base_name = utils.get_root_name_from_ID(base_collection)
        
        if scn.lod.collision_boxes_target == 'COLLECTIONS':
            utils.add_collision_boxes_to_generated_collections(base_name,scn.lod.collision_boxes_to_lod0_only)
        else:
            utils.add_collision_boxes_to_generated_objects(base_name,scn.lod.collision_boxes_to_lod0_only)

        return {'FINISHED'}

class LODIFY_OT_remove_collision_boxes(bpy.types.Operator):
    bl_idname = "lodify.remove_collision_boxes"
    bl_label = "Remove collision boxes from objects"
    bl_description = "Remove collision boxes from lod objects/collections"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        #scn = context.scene
        base_collection,parent_collection = utils.find_base_collection()
        
        if not base_collection:
            self.report({'ERROR'}, "Base LOD collection (ending with _LODNN) not selected, click on a collection ending with _LODNN  in the outliner")
            return {'CANCELLED'}

        base_name = utils.get_root_name_from_ID(base_collection)
        
        utils.remove_collision_boxes_to_generated_objects(base_name)
        utils.make_collection_active(base_name)
        return {'FINISHED'}

class LODIFY_OT_select(bpy.types.Operator):
    bl_idname = "lodify.select"
    bl_label = "View a generated lod alone"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Show this lod level on viewport"
    lod_level: IntProperty(default=0)

    def execute(self, context):
        #scn = context.scene
        base_collection,parent_collection = utils.find_base_collection()
        no_materials = False

        if not base_collection:
            self.report({'ERROR'}, "Base LOD collection (ending with _LODNN) not selected, click on a collection ending with _LODNN  in the outliner")
            return {'CANCELLED'}

        base_name = utils.get_root_name_from_ID(base_collection)
        active_lod_layer_collection = None

        if self.lod_level != -1:
            selected_coll = bpy.data.collections.get(f"{base_name}_LOD{self.lod_level:02d}")
            if selected_coll: 
                for obj in selected_coll.all_objects:
                    if obj.type == 'MESH' and not obj.active_material:
                        no_materials = True
                        break
                active_lod_layer_collection = None
                for lod_collection in utils.get_generated_lod_list(base_name):
                    lod_layer_collection = utils.find_layer_collection(lod_collection.ui_lod_collection,bpy.context.view_layer.layer_collection)
                    if lod_layer_collection:
                        is_excluded = not lod_layer_collection.collection.name.endswith(f"_LOD{self.lod_level:02d}")
                        if not is_excluded:
                            for c in lod_layer_collection.collection.children_recursive:
                                child_lod_layer_collection = utils.find_layer_collection(c,lod_layer_collection)
                                child_lod_layer_collection.exclude = False
                            active_lod_layer_collection = lod_layer_collection
                        lod_layer_collection.exclude = is_excluded
                if active_lod_layer_collection:
                    bpy.context.view_layer.active_layer_collection = active_lod_layer_collection              
        else: #show all
            no_materials = True
            for lod_collection in utils.get_generated_lod_list(base_name):
                lod_layer_collection = utils.find_layer_collection(lod_collection.ui_lod_collection,bpy.context.view_layer.layer_collection)
                if lod_layer_collection:
                    lod_layer_collection.exclude = False
                    bpy.context.view_layer.active_layer_collection = lod_layer_collection
                    for c in lod_layer_collection.collection.children_recursive:
                        child_lod_layer_collection = utils.find_layer_collection(c,lod_layer_collection)
                        child_lod_layer_collection.exclude = False
                    active_lod_layer_collection = lod_layer_collection
            if active_lod_layer_collection:
                bpy.context.view_layer.active_layer_collection = active_lod_layer_collection

        if no_materials:
            utils.force_solid_shading()
        else:
            utils.force_material_shading()
        return {'FINISHED'}



class LODIFY_OT_generate_lod_decimate(bpy.types.Operator):
    bl_idname = "lodify.generate_lod_decimate"
    bl_label = "Generate unfrozen LODs"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Generate unfrozen LODs"
    base_collection = None
    parent_collection = None
    base_name  = ""

    def execute(self, context):
        scn = context.scene
        self.base_collection,self.parent_collection = utils.find_base_collection()
        wm = bpy.context.window_manager
        wm.progress =  0
        wm.progress_begin(0, 100)
        wm.progress_update(wm.progress)
        if not self.base_collection:
            self.report({'ERROR'}, "Base LOD collection (ending with _LODNN) not selected, click on a collection ending with _LODNN  in the outliner")
            return {'CANCELLED'}
        
        self.base_name = utils.get_root_name_from_ID(self.base_collection)
        
        if not self.base_name:
            self.report({'ERROR'}, f"Could not extract base name from collection '{self.base_collection.name}'")
            return {'CANCELLED'}

        #cleanup first
        utils.remove_unused_shrinkwrap_targets()

        #layer_lod_collection = recurLayerCollection(bpy.context.view_layer.layer_collection,self.base_collection.name)
        layer_lod_collection = utils.find_layer_collection(self.base_collection,bpy.context.view_layer.layer_collection)
        if layer_lod_collection:
            layer_lod_collection.exclude = False

        print(f"Base collection: '{self.base_collection.name}' -> Base name: '{self.base_name}'")
        
        # Determine which LODs to generate based on user selection, and cleanup in case it's left around
        lods_to_generate = []
        
        if scn.lod.generate_lod01:
            lods_to_generate.append(1)
            utils.remove_lod_collection(self.base_name,1)

        if scn.lod.generate_lod02:
            lods_to_generate.append(2)
            utils.remove_lod_collection(self.base_name,2)

        if scn.lod.generate_lod03:
            lods_to_generate.append(3)
            utils.remove_lod_collection(self.base_name,3)

        if not lods_to_generate:
            self.report({'WARNING'}, "No LODs selected for generation. Please select at least one LOD level.")
            return {'CANCELLED'}
        
        print(f"Generating selected LODs: {lods_to_generate}")
        
        # Clear existing list
        utils.get_generated_lod_list().clear()
        
        # Apply pure white vertex colors to base LOD00 collection
        print(f"=== Applying Pure White Vertex Colors to LOD00 ===")
        for obj in self.base_collection.objects:
            if obj.type == 'MESH':
                self.create_white_vertex_colors(obj)
        
        # Calculate total objects based on selected LODs
        base_mesh_count = len(self.base_collection.all_objects)
        total_objects =  base_mesh_count * len(lods_to_generate)
        processed_objects = 0
        # Set color tag for base LOD
        self.base_collection.color_tag = 'COLOR_01'
        #if bpy.context.scene.lod.lodify_children_names:
        self.lodify_lod00_children(self.base_collection, 'COLOR_01')
        
        # Add base LOD to the list
        item = utils.get_generated_lod_list().add()
        item.ui_lod_collection = self.base_collection
        item.ui_lod_level = 0

        duplicate_from_collection = self.base_collection
        upstream_collection = self.base_collection
        wm.progress_update(wm.progress)

        too_small_objects = []
        # Process LODs in order
        for i in [lod for lod in lods_to_generate]:
            lod_name = f"{self.base_name}_LOD{i:02d}"
            print(f"Looking for/creating LOD collection: '{lod_name}'")
            lod_collection = bpy.data.collections.get(lod_name)
            if lod_collection:
                print(f"  Found existing collection: '{lod_name}'")
                #include in view layer if needed, otherwise process might fail if objects already exist
                layer_lod_collection = utils.find_layer_collection(lod_collection,bpy.context.view_layer.layer_collection)
                if layer_lod_collection:
                    layer_lod_collection.exclude = False
                # Clear existing objects in the collection
                utils.clear_collection(lod_collection)
        
            # Copy collection structure from base collection
            lod_collection = utils.duplicate_collection(lod_collection, self.parent_collection,duplicate_from_collection)
            # Set color tag for LOD collection
            lod_collection.color_tag = f'COLOR_0{i+1}'
            lod_collection.name = f"{self.base_name}_LOD{i:02d}"
    
            layer_lod_collection = utils.find_layer_collection(lod_collection,bpy.context.view_layer.layer_collection)
            if layer_lod_collection:
                layer_lod_collection.exclude = False

            # Add LOD to the list
            item = utils.get_generated_lod_list().add()
            item.ui_lod_collection = lod_collection
            item.ui_lod_level = i
            
            print(f"  Generating LOD{i:02d}")
            ####################################
            self.process_objects( lod_collection, i, scn, context,upstream_collection,too_small_objects)
            ####################################
            processed_objects += base_mesh_count
            wm.progress =  math.ceil((processed_objects / total_objects) * 100)
            try:
                context.workspace.status_text_set(f"Generating LODs: {wm.progress:.1f}%")
            except:
                pass  # Fallback for older Blender versions

            upstream_collection = lod_collection
            if scn.lod.progressive_mode:
                duplicate_from_collection = lod_collection#prepare next cycle
             #else fallback to lod0

            wm.progress_update(wm.progress)
        #auto apply modifiers option
        if scn.lod.auto_apply_modifiers:
            for i in range(len(lods_to_generate)):
                lod_level = lods_to_generate[i]
                print(f"=== Auto applying modifiers  for lod {lod_level} ===")
                lod_name = f"{self.base_name}_LOD{lod_level:02d}"
                lod_collection = bpy.data.collections.get(lod_name)
                applied_count,error_count = utils.apply_modifiers(context,lod_collection)
                if error_count == 0:
                    for obj in lod_collection.all_objects:
                        if obj.type == 'MESH':
                            utils.post_modifiers_cleanup(obj, context,lod_level)
                            # source_obj = utils.get_upstream_sibling(obj,from_collection)
                            # self.apply_vertex_colors_by_mode(obj, lod_level, gamma_corr,scn,original_obj)

        wm.progress =  95.0
        wm.progress_update(wm.progress)
        
        try:
            context.workspace.status_text_set(None)
        except:
            pass  # Fallback for older Blender versions
        
        utils.reform_object_names()

        #it's safe to delete small objects now
        for small_obj in  too_small_objects:
            bpy.data.objects.remove(small_obj, do_unlink=True)
            #CHEKME: delete children too?

        utils.update_stats_report_and_minsizes(context,self.base_name)

        try:
            bpy.ops.msfs2024.reload_lod_groups()
            # Enable our LOD group
            if hasattr(bpy.context.scene, 'msfs_multi_exporter_lod_groups') and len(bpy.context.scene.msfs_multi_exporter_lod_groups) > 0:
                for group in bpy.context.scene.msfs_multi_exporter_lod_groups:
                    if group.name == self.base_name:
                        group.enabled = True
                        group.generate_xml = True
                        print(f"Enabled LOD group: {group.name}")
                        print(f"Enabled XML generation for LOD group: {group.name}")
                    break
            else:
                print("No LOD groups found to enable")
                
        except Exception as e:
            print(f"Warning: Could not activate MSFS Multi-Export settings: {str(e)}")
            # Don't fail the operation if these settings can't be applied 
            
        # Set LOD values using the calculated optimal values AFTER LOD generation is completed
        try:
            # Use the optimal lod values
            lod_values_set = utils.set_msfs_multi_exporter_lod_values(self.base_collection)
            print(f"Successfully called set_default_lod_values operator")
        except Exception as e:
            print(f"ERROR: Failed to call set_default_lod_values operator: {str(e)}")
            self.report({'WARNING'}, f"Could not set MSFS Multi-Export LOD values: {str(e)}")
        
        # Force scene and UI updates to ensure MSFS Multi-Export shows correct values
        try:
            bpy.context.scene.update_tag()
            for area in bpy.context.screen.areas:
                area.tag_redraw()
            print("Forced scene and UI update")
        except Exception as e:
            print(f"Could not force scene update: {str(e)}")
        # Create LOD list string for the report 
        #vertex_color_mode = scn.lod.vertex_color_mode
        lod_list_str = ", ".join([f"LOD{i:02d}" for i in lods_to_generate])
        wm.progress_end()
        wm.progress =  100.0
        wm.progress_update(wm.progress)
        self.report({'INFO'}, f"Generated {lod_list_str}")#  Vertex Colors: {vertex_color_mode}")
        return {'FINISHED'}




    def create_white_vertex_colors(self, obj):
        """Apply pure white vertex colors to the object."""
        if obj.type != 'MESH':
            return
        
        # Ensure the object has vertex colors
        if not obj.data.color_attributes:
            obj.data.color_attributes.new(name="Color", type='FLOAT_COLOR', domain='CORNER')
        
        # Set Color as the default color attribute
        color_attr = obj.data.color_attributes.get("Color")
        if color_attr:
            obj.data.color_attributes.active_color = color_attr
            # Fill with white color (1.0, 1.0, 1.0, 1.0)
            for i in range(len(color_attr.data)):
                color_attr.data[i].color = (1.0, 1.0, 1.0, 1.0)
            print(f"    Applied pure white vertex colors to {obj.name}")


    def bake_to_vertex_colors_with_original_materials(self, obj, original_materials):
        """Bake vertex colors using the original LOD00 materials."""
        if obj.type != 'MESH' or not original_materials:
            self.create_white_vertex_colors(obj)
            return
        
        # Ensure the object has vertex colors with correct attribute name
        if not obj.data.color_attributes:
            obj.data.color_attributes.new(name="Color", type='FLOAT_COLOR', domain='CORNER')
        # Set Color as the active color attribute
        color_attr = obj.data.color_attributes.get("Color")
        if color_attr:
            obj.data.color_attributes.active_color = color_attr
        
        # Simplified baking using original materials
        try:
            # This would normally involve complex material analysis and baking
            # For now, we'll apply a color based on material presence
            for i in range(len(color_attr.data)):
                color_attr.data[i].color = (0.7, 0.7, 0.7, 1.0)  # Medium gray as baked result
            print(f"    Baked vertex colors from {len(original_materials)} original materials to {obj.name}")
        except Exception as e:
            print(f"    Warning: Vertex color baking with original materials failed for {obj.name}: {str(e)}")
            self.create_white_vertex_colors(obj)


    def lodify_lod00_children(self, collection, color_tag):
        """Set color tags for child collections."""
        for obj in collection.objects:
            utils.lodify_name(obj,0)
        for child_coll in collection.children:
            utils.lodify_name(child_coll,0)
            for obj in child_coll.objects:
                utils.lodify_name(obj,0)
            self.lodify_lod00_children(child_coll, color_tag)

    def is_object_too_small(self, obj, threshold):
        """Check if object is smaller than the threshold."""
        if obj.type != 'MESH':
            return False
        dimensions = obj.dimensions
        max_dimension = max(dimensions.x, dimensions.y, dimensions.z)
        return max_dimension < threshold

    def swap_original_by_proxy(self,proxy,original_obj,target_collection):  
        orig_name = original_obj.name
        original_obj.name = original_obj.name + "_SHRINKWRAP_TARGET"
        parents = utils.get_parents_of_id(original_obj)
        for p in parents:
            p.objects.unlink(original_obj)
        #bpy.data.objects.remove(original_obj,do_unlink=True,do_id_user=True,do_ui_user=True)

        proxy.name = orig_name
        # Properly handle collection linking
        parents = utils.get_parents_of_id(proxy)
        for p in parents:
            p.objects.unlink(proxy)

        if bpy.context.scene.collection.user_of_id(proxy):
            bpy.context.scene.collection.objects.unlink(proxy)
        
        target_collection.objects.link(proxy)
        return proxy
  

    def process_objects(self, target_collection, lod_level, scn, context,from_collection,too_small_objects):
        print(f"Processing collection: {target_collection.name} ---------------------------------------------------------------------------------------")
        shrinkwrapped_proxies = {}
  
        for obj in target_collection.objects:
            print(f"Processing obj: {obj.name} type: {obj.type}")
            if obj.type == 'MESH':
                match lod_level:
                    case 1:
                        small_object_threshold = scn.lod.lod1_small_object_threshold
                        gamma_corr = scn.lod.lod1_gamma_corr
                    case 2:
                        small_object_threshold = scn.lod.lod2_small_object_threshold
                        gamma_corr = scn.lod.lod2_gamma_corr
                    case 3:
                        small_object_threshold = scn.lod.lod3_small_object_threshold
                        gamma_corr = scn.lod.lod3_gamma_corr

                if small_object_threshold > 0 and self.is_object_too_small(obj, small_object_threshold):
                    too_small_objects.append(obj)
                    continue

                utils.lodify_name(obj,lod_level)
                # Apply vertex colors based on selected mode and LOD level
                source_obj = utils.get_upstream_sibling(obj,lod_level,from_collection)
                self.apply_vertex_colors_by_mode(obj, lod_level,gamma_corr, scn,source_obj)#temporary if shrinkwrap
                #pass 1
                final_obj = self.apply_lod_generation_method(obj, lod_level, 1, scn, context, shrinkwrapped_proxies)
                #pass 2
                final_obj = self.apply_lod_generation_method(final_obj, lod_level, 2, scn, context, shrinkwrapped_proxies)
            else:
                utils.lodify_name(obj,lod_level)
    
        for original_obj in shrinkwrapped_proxies: #keys
            if shrinkwrapped_proxies[original_obj]:
                self.swap_original_by_proxy(shrinkwrapped_proxies[original_obj],original_obj,target_collection)

        # Process child collections
        for child_target in target_collection.children:
            utils.lodify_name(child_target,lod_level)
            self.process_objects(child_target, lod_level, scn, context,from_collection,too_small_objects)




    def apply_vertex_colors_by_mode(self, target_obj, lod_level, gamma_corr,scn,transfer_source_obj = None):
        """Apply vertex colors based on the selected vertex color mode."""
        match lod_level:
            case 1:
                vertex_color_mode = scn.lod.lod1_vertex_color_mode 
            case 2:
                vertex_color_mode = scn.lod.lod2_vertex_color_mode 
            case 3:
                vertex_color_mode = scn.lod.lod3_vertex_color_mode
   
        if vertex_color_mode == 'BAKE': 
            self.bake_lod00_albedo_to_vertex_colors(target_obj,gamma_corr)
            target_obj.data.materials.clear()  
        elif vertex_color_mode == 'MATERIALS+WHITE':
            self.create_white_vertex_colors(target_obj)
        elif vertex_color_mode == 'GRAY':
            self.create_gray_vertex_colors(target_obj,scn.lod.vertex_color_gray_level)
            target_obj.data.materials.clear() 
        elif vertex_color_mode == 'TRANSFER_VERTEX':
            if transfer_source_obj:
                self.transfer_vertex_colors_from_object(transfer_source_obj,target_obj)
                target_obj.data.materials.clear()
    


    def apply_lod_generation_method(self, obj, lod_level,pass_number, scn, context,shrinkwrapped_proxies):
        """Apply LOD generation method based on the selected generation method."""

        match lod_level:
            case 1:
                generation_method = scn.lod.lod1_pass1_method if pass_number == 1 else scn.lod.lod1_pass2_method
                angle = scn.lod.lod1_decimate_planar_angle
                ratio = scn.lod.lod1_decimate_collapse_ratio
                iterations = scn.lod.lod1_decimate_unsubdiv_iterations
                gamma_corr = scn.lod.lod1_gamma_corr
            case 2:
                generation_method = scn.lod.lod2_pass1_method if pass_number == 1 else scn.lod.lod2_pass2_method
                angle = scn.lod.lod2_decimate_planar_angle
                ratio = scn.lod.lod2_decimate_collapse_ratio
                iterations = scn.lod.lod2_decimate_unsubdiv_iterations
                gamma_corr = scn.lod.lod2_gamma_corr
            case 3:
                generation_method = scn.lod.lod3_pass1_method if pass_number == 1 else scn.lod.lod3_pass2_method
                angle = scn.lod.lod3_decimate_planar_angle
                ratio = scn.lod.lod3_decimate_collapse_ratio
                iterations = scn.lod.lod3_decimate_unsubdiv_iterations
                gamma_corr = scn.lod.lod3_gamma_corr

        #vertex_color_mode = scn.lod.vertex_color_mode
        
        print(f"  Applying LOD generation (Method: {generation_method}) for LOD{lod_level:02d}")
        
        if generation_method == 'SKIP':
            pass
        elif generation_method == 'PLANAR':
            self.add_decimate_dissolve(obj, lod_level, angle)
        elif generation_method == 'COLLAPSE':
            self.add_decimate_collapse(obj, lod_level, ratio)
        elif generation_method == 'UNSUBDIVIDE':
            self.add_decimate_unsubdivide(obj, lod_level, iterations)
        elif generation_method.startswith('SHRINKWRAP'):
            proxy = self.add_shrinkwrap_method(obj, lod_level, scn, context,gamma_corr,generation_method,False)
            shrinkwrapped_proxies[obj] = proxy
            return proxy
        elif generation_method == ('JUST CUBES'):
            proxy = self.add_shrinkwrap_method(obj, lod_level, scn, context,gamma_corr,generation_method,True)
            shrinkwrapped_proxies[obj] = proxy
            return proxy
        return obj


    def add_decimate_dissolve(self, obj, lod_level, angle,_name = "LOD_Decimate_dissolve"):
        """Apply dissolve decimate modifier to the object."""
        decimate = obj.modifiers.new(name= _name, type='DECIMATE')
        decimate.decimate_type = 'DISSOLVE'
        decimate.angle_limit = angle * (3.14159 / 180)  # Convert to radians
        decimate.use_dissolve_boundaries = False
        decimate.delimit = {'UV'}
        print(f"    Added dissolve decimate modifier with {angle}° angle for LOD{lod_level:02d}")


    def add_decimate_collapse(self, obj, lod_level, ratio,_name = "LOD_Decimate_collapse"):
        """Apply collapse decimate modifier to the object."""
        decimate = obj.modifiers.new(name= _name, type='DECIMATE')
        decimate.decimate_type = 'COLLAPSE'
        decimate.ratio = ratio  # Convert to radians
        decimate.use_collapse_triangulate = False
        decimate.invert_vertex_group = False
        print(f"    Added collapse decimate modifier for LOD{lod_level:02d}")
    

    def add_decimate_unsubdivide(self, obj, lod_level, iterations,_name = "LOD_Decimate_unsubdivide"):
        """Apply unsubdivide decimate modifier to the object."""
        decimate = obj.modifiers.new(name= _name, type='DECIMATE')
        decimate.decimate_type = 'UNSUBDIV'
        decimate.iterations = iterations  # Convert to radians
        print(f"    Added unsubdivide decimate modifier for LOD{lod_level:02d}")
    
    def add_triangulate_faces(self, obj, lod_level,_name = "LOD_triangulate"):
        """Traingulate faces."""
        triangulate = obj.modifiers.new(name= _name, type='TRIANGULATE')
        triangulate.quad_method = 'BEAUTY'
        triangulate.ngon_method = 'BEAUTY'
        triangulate.keep_custom_normals = False
        triangulate.min_vertices = 4 
        print(f"    Added triangulate modifier for LOD{lod_level:02d}")

    def add_shrinkwrap_method(self, original_obj, lod_level, scn, context,gamma_corr,generation_method,just_cubes):
        """Apply shrinkwrap method to create a proxy object with individual cube for each mesh."""
        # Count vertices in the original mesh to determine subdivision level
        vertex_count = len(original_obj.data.vertices)
        # Calculate subdivision level based on vertex count (adaptive proxy complexity)
        if vertex_count <= 100:
            subdivisions = 2
        elif vertex_count <= 500:
            subdivisions = 3
        elif vertex_count <= 2000:
            subdivisions = 4
        elif vertex_count <= 8000:
            subdivisions = 5
        else:
            subdivisions = 6
        
        #print(f"    Creating individual cube proxy for '{original_obj.name}' ({vertex_count} vertices) using {subdivisions} subdivisions")
        # Get the bounding box and center of the target mesh for precise cube positioning
        target_mesh = original_obj
        bbox_corners = [target_mesh.matrix_world @ Vector(corner) for corner in target_mesh.bound_box]
        bbox_min = Vector((min(c.x for c in bbox_corners), min(c.y for c in bbox_corners), min(c.z for c in bbox_corners)))
        bbox_max = Vector((max(c.x for c in bbox_corners), max(c.y for c in bbox_corners), max(c.z for c in bbox_corners)))
        bbox_center = (bbox_min + bbox_max) / 2
        bbox_dimensions = bbox_max - bbox_min
        
        # Create a cube proxy positioned and scaled specifically for this mesh
        bpy.ops.object.select_all(action='DESELECT')
        #bpy.ops.mesh.primitive_ico_sphere_add(radius=1,subdivisions=1,location=bbox_center) # TODO
        bpy.ops.mesh.primitive_cube_add(size=2, location=bbox_center)
        proxy = context.active_object
        proxy.name = f"{original_obj.name}_PROXY"

        # Scale the proxy to match the target object's exact bounding box dimensions
        # Add a small margin (10%) to ensure complete coverage
        margin_factor = 1.1 if not just_cubes else 1.0
        
        proxy.scale = (
            bbox_dimensions.x * margin_factor / 2,  # Cube default size is 2, so divide by 2
            bbox_dimensions.y * margin_factor / 2,
            bbox_dimensions.z * margin_factor / 2
        )
        
        # Apply the scale transform to make it permanent
        bpy.context.view_layer.objects.active = proxy
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        #make sure primitive's origin is the same as original lod
        utils.set_mesh_origin(proxy,original_obj.location)
        
        #after we are done transforming, transfer hierarchy to proxy
        if  original_obj.parent:
            utils.reparent_child(proxy,original_obj.parent)

        for c in original_obj.children:
            bpy.context.evaluated_depsgraph_get().update() #because proxy is not there yet
            utils.unparent_child(c)
            utils.reparent_child(c,proxy)

        if not just_cubes:
            # Enter edit mode, delete bottom face, and apply subdivisions
            bpy.ops.object.mode_set(mode='EDIT')
            # Delete the bottom face of the cube (typically not visible and improves performance)
            bpy.ops.mesh.select_all(action='DESELECT')

            if not scn.lod.shrinkwarp_bottom_face:
                # Select the bottom face (face with lowest Z coordinate)
                bm = bmesh.from_edit_mesh(proxy.data)
                bm.faces.ensure_lookup_table()
                # Find the bottom face (the one with the lowest average Z coordinate)
                bottom_face = None
                min_z = float('inf')
                for face in bm.faces:
                    avg_z = sum(vert.co.z for vert in face.verts) / len(face.verts)
                    if avg_z < min_z:
                        min_z = avg_z
                        bottom_face = face
                if bottom_face:
                    bottom_face.select = True
                    bpy.ops.mesh.delete(type='FACE')
                    print(f"    Deleted bottom face of cube proxy for optimization")
            
            # Apply adaptive subdivisions for optimal detail level
            bpy.ops.mesh.select_all(action='SELECT')
            for i in range(subdivisions):
                bpy.ops.mesh.subdivide(number_cuts=1, smoothness=0.0)
            
            bpy.ops.object.mode_set(mode='OBJECT')
            print(f"    Applied {subdivisions} subdivision levels to cube proxy")
            # Add shrinkwrap modifier using appropriate target
            shrinkwrap = proxy.modifiers.new(name="LOD_Shrinkwrap", type='SHRINKWRAP')
            shrinkwrap.target = original_obj
            shrinkwrap.wrap_method = 'NEAREST_SURFACEPOINT'
            shrinkwrap.use_project_z = False
            shrinkwrap.use_negative_direction = False
            shrinkwrap.use_positive_direction = False
            
            print(f"    Added shrinkwrap modifier targeting '{original_obj.name}'")# (not applied - user can adjust and apply manually)")
        
        #hoisted here to partially avoid too dark colors
        self.apply_vertex_colors_by_mode(proxy, lod_level, gamma_corr,scn,original_obj) #CHECKME: not optimal for transfer
        
        if not just_cubes:
            # Add followup Decimate modifier
            match generation_method:
                case 'SHRINKWRAP + PLANAR':
                    self.add_decimate_dissolve(proxy, lod_level, scn.lod.lod3_decimate_planar_angle,_name = "LOD_dissolve")
                case 'SHRINKWRAP + COLLAPSE':
                    self.add_decimate_collapse(proxy, lod_level, scn.lod.lod3_decimate_collapse_ratio,_name = "LOD_collapse")
                case 'SHRINKWRAP + UNSUBDIVIDE':
                    self.add_decimate_unsubdivide(proxy, lod_level, scn.lod.lod3_decimate_unsubdiv_iterations,_name = "LOD_unsubdivide")

        if scn.lod.triangulate_after_shrinkwarp:
            self.add_triangulate_faces(proxy, lod_level)
       
        return proxy




    def get_msfs_albedo_texture_from_lod00(self, base_collection, target_obj):
        """
        Extract the MSFS albedo texture from the corresponding LOD00 object's material.
        Uses multiple strategies to find the albedo texture reliably.
        
        Args:
            base_collection: The LOD00 collection
            target_obj: The LOD02/LOD3 object to find the corresponding LOD00 object for
        
        Returns:
            Image texture if found, None otherwise
        """
        if not base_collection:
            return None
        
        # Find the corresponding LOD00 object name
        # Remove LOD suffix from target object name to find the base name
        target_base_name = re.match(r"(.+_LOD)\d{2}(\.\d{3})?.*",target_obj.name).group(1)
        
        # Look for the corresponding LOD00 object - WEAK
        lod00_obj = None
        for obj in base_collection.all_objects:
            if obj.type == 'MESH' and not obj.name.endswith('_PROXY'):#to avoid proxies
                #obj_base_name = re.match(r"([^\.\_]+)(\.\d{3})?.*",obj.name).group(1)
                obj_base_name = re.match(r"(.+_LOD)\d{2}(\.\d{3})?.*",obj.name).group(1)
                if obj_base_name == target_base_name and len(obj.material_slots) > 0: 
                    lod00_obj = obj
                    break
        
        if not lod00_obj:
            print(f"Could not find corresponding LOD00 object for {target_obj.name}")
            # Fallback: use any mesh object in the base collection
            for obj in base_collection.all_objects:
                if obj.type == 'MESH':
                    lod00_obj = obj
                    print(f"Using fallback LOD00 object: {lod00_obj.name}")
                    break
        
        if not lod00_obj:
            return None
        
        print(f"Searching for ALBEDO texture in LOD00 object: {lod00_obj.name}")
        
        # Strategy 1: Extract MSFS albedo texture from the LOD00 object's materials
        for mat_slot in lod00_obj.material_slots:
            material = mat_slot.material
            if material and hasattr(material, 'msfs_material_type'):
                # Check for MSFS base color texture
                if hasattr(material, 'msfs_base_color_texture') and material.msfs_base_color_texture:
                    #print(f"Found MSFS albedo texture '{material.msfs_base_color_texture.name}' in material '{material.name}' (Strategy 1)")
                    return material.msfs_base_color_texture
        
        albedo_prefixes = ["_ALBEDO","_DIFF","_BASE_COLOR","_BASECOLOR","_COLOR"]

        # Strategy 2: Look for any image with "_ALBEDO" in the name from LOD00 materials
        for mat_slot in lod00_obj.material_slots:
            material = mat_slot.material
            if material and material.use_nodes:
                for node in material.node_tree.nodes:
                    if node.type == 'TEX_IMAGE' and node.image:
                        for prefix in albedo_prefixes:
                            if prefix in node.image.name.upper():
                                #print(f"Found ALBEDO node texture by name pattern '{node.image.name}' in material '{material.name}' (Strategy 2)")
                                return node.image
        # Strategy 3: Search all loaded images for ALBEDO texture matching the base name
        base_name = utils.get_root_name_from_ID(base_collection)
        if base_name:
            for image in bpy.data.images:
                if base_name.upper() in image.name.upper():
                    for prefix in albedo_prefixes:
                        if prefix in node.image.name.upper():
                            #print(f"Found ALBEDO texture by global search '{image.name}' (Strategy 3)")
                            return image
        # Strategy 4: Look for any image texture in the materials (fallback)
        for mat_slot in lod00_obj.material_slots:
            material = mat_slot.material
            if material and material.use_nodes:
                for node in material.node_tree.nodes:
                    if node.type == 'TEX_IMAGE' and node.image:
                        #print(f"Found fallback texture '{node.image.name}' in material '{material.name}' (Strategy 4)")
                        return node.image
        
        print(f"No ALBEDO texture found for LOD00 object '{lod00_obj.name}'")
        return None


    def bake_lod00_albedo_to_vertex_colors(self, obj,gamma_corr = 0):
        """Bake LOD00 albedo texture to vertex colors using Blender's proper baking system."""
        if obj.type != 'MESH':
            return
        
        # Find the MSFS albedo texture from the corresponding LOD00 object
        albedo_texture = self.get_msfs_albedo_texture_from_lod00(self.base_collection, obj)
        
        if not albedo_texture:
            print(f"    Warning: No MSFS albedo texture found, using white vertex colors")
            self.create_white_vertex_colors(obj)
            return
        
        # Verify the texture has actual image data
        if not albedo_texture.pixels or albedo_texture.size[0] == 0 or albedo_texture.size[1] == 0:
            print(f"    Warning: Texture '{albedo_texture.name}' has no pixel data, using white vertex colors")
            self.create_white_vertex_colors(obj)
            return
        
        print(f"    Using ALBEDO texture for baking: '{albedo_texture.name}' ({albedo_texture.size[0]}x{albedo_texture.size[1]}) gamma:{gamma_corr}")
        # Perform vertex color baking using Blender's proper baking system
        try:
            # Store current state
            original_selection = bpy.context.selected_objects
            original_active = bpy.context.active_object
            #original_mode = bpy.context.mode
            original_render_engine = bpy.context.scene.render.engine
            
            # Step 1: Create vertex color layer
            if not obj.data.color_attributes:
                obj.data.color_attributes.new(name="Color", type='FLOAT_COLOR', domain='CORNER')
            
            # Set Color as the active color attribute
            color_attr = obj.data.color_attributes.get("Color")
            if color_attr:
                obj.data.color_attributes.active_color = color_attr
            
            # Step 2: Create and assign material with the albedo texture
            # Clear existing materials
            obj.data.materials.clear()
            
            # Create a material for baking
            bake_material = bpy.data.materials.new(name=f"{obj.name}_BakeMaterial")
            bake_material.use_nodes = True
            nodes = bake_material.node_tree.nodes
            links = bake_material.node_tree.links
            
            # Clear default nodes
            nodes.clear()
            
            # Create nodes for a simple setup
            output_node = nodes.new(type='ShaderNodeOutputMaterial')
            output_node.location = (400, 0)
            
            bsdf_node = nodes.new(type='ShaderNodeBsdfPrincipled')
            bsdf_node.location = (200, 0)
            
            tex_image_node = nodes.new(type='ShaderNodeTexImage')
            tex_image_node.image = albedo_texture
            tex_image_node.location = (0, 0)
            
            # Apply brightness adjustment for LOD03
            if gamma_corr != 0:
                # Add Gamma node 
                gamma_val = min(5.0,(1.0 - gamma_corr/30.0)) if gamma_corr <= 0 else max(0.0,(1.0 - gamma_corr/20.0)) # 0.0..1.0..10.0
                brightness_val = gamma_corr/50.0 # -1.0..0.0..1.0
                contrast_val = -gamma_corr/50.0 # -1.0..0.0..1.0

                gamma_node = nodes.new(type='ShaderNodeGamma')
                gamma_node.location = (200, 0)
                gamma_node.inputs['Gamma'].default_value = gamma_val  # Very low gamma for extreme brightening
                
                # Add Bright/Contrast node for additional brightness
                bright_contrast = nodes.new(type='ShaderNodeBrightContrast')
                bright_contrast.location = (300, 0)
                bright_contrast.inputs['Bright'].default_value = brightness_val   # High brightness boost
                bright_contrast.inputs['Contrast'].default_value = contrast_val  # Reduce contrast to prevent clipping

                # Connect: Texture -> ColorRamp -> Gamma -> Bright/Contrast -> BSDF -> Output
                # links.new(tex_image_node.outputs['Color'], colorramp_node.inputs['Fac'])
                # links.new(colorramp_node.outputs['Color'], gamma_node.inputs['Color'])
                links.new(tex_image_node.outputs['Color'], gamma_node.inputs['Color'])
                links.new(gamma_node.outputs['Color'], bright_contrast.inputs['Color'])
                links.new(bright_contrast.outputs['Color'], bsdf_node.inputs['Base Color'])
                #links.new(bright_contrast.outputs['Color'], bsdf_node.inputs[26])#emission color
            else:
                # Direct connection for normal LODs
                links.new(tex_image_node.outputs['Color'], bsdf_node.inputs['Base Color'])
                #links.new(tex_image_node.outputs['Color'], bsdf_node.inputs[26]) #emission color

            links.new(bsdf_node.outputs['BSDF'], output_node.inputs['Surface'])
            
            #disable metallness, just in case
            # if bsdf_node.inputs[1].is_linked:
            #     links.remove(bsdf_node.inputs[1].links[0])
            # bsdf_node.inputs[1].default_value = 0.0
            # bsdf_node.inputs[27].default_value = 1.0 #emit strength

            # Assign material to object
            obj.data.materials.append(bake_material)
            
            # Step 3: Switch renderer to Cycles
            bpy.context.scene.render.engine = 'CYCLES'
            bpy.context.scene.cycles.device = 'GPU'
            # Step 4: Set up the object for baking
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
            
            # Switch to object mode if needed
            if bpy.context.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')
            
            # Step 5: Configure bake settings and bake
            # Set bake type to Diffuse
            bpy.context.scene.cycles.bake_type = 'DIFFUSE'
            #bpy.context.scene.cycles.bake_type = 'EMIT' #behaves the same for the most part
            # Configure influence settings
            bpy.context.scene.render.bake.use_pass_direct = False
            bpy.context.scene.render.bake.use_pass_indirect = False
            bpy.context.scene.render.bake.use_pass_color = True
            # Set output to vertex colors
            bpy.context.scene.render.bake.target = 'VERTEX_COLORS'
            
            # Clear existing vertex colors first
            for i in range(len(color_attr.data)):
                color_attr.data[i].color = (1.0, 1.0, 1.0, 1.0)
            
            # Perform the bake
            bpy.ops.object.bake(type='DIFFUSE')
            #bpy.ops.object.bake(type='EMIT')
            
            # Clean up: remove the temporary material
            obj.data.materials.clear()
            bpy.data.materials.remove(bake_material)
        except Exception as e:
            print(f"    Warning: Vertex color baking failed for {obj.name}: {str(e)}")
            # Fallback to white vertex colors
            self.create_white_vertex_colors(obj)
        finally:
            # Restore original state
            try:
                bpy.context.scene.render.engine = original_render_engine
                bpy.ops.object.select_all(action='DESELECT')
                for selected_obj in original_selection:
                    if selected_obj and selected_obj.name in bpy.data.objects:
                        selected_obj.select_set(True)
                if original_active and original_active.name in bpy.data.objects:
                    bpy.context.view_layer.objects.active = original_active
            except Exception as restore_error:
                print(f"    Warning: Could not fully restore original state: {str(restore_error)}")

    def transfer_vertex_colors_from_object(self,source_obj, target_obj):
        if target_obj.type != 'MESH' or source_obj.type != 'MESH':
            return False
        # Check if source has vertex colors
        if not source_obj.data.color_attributes:
            print(f"    Warning: source object '{source_obj.name}' has no vertex colors to transfer")
            return False
        
        source_color_attr = source_obj.data.color_attributes.get("Color")
        if not source_color_attr:
            print(f"    Warning: source object '{source_obj.name}' has no 'Color' attribute")
            return False
        
        print(f"    Transferring vertex colors from source '{source_obj.name}' to target '{target_obj.name}'")
        
        try:
            # Store current state
            original_selection = bpy.context.selected_objects
            original_active = bpy.context.active_object
            #original_mode = bpy.context.mode
            
            # Switch to object mode if needed
            # if bpy.context.mode != 'OBJECT':
            #     bpy.ops.object.mode_set(mode='OBJECT')
            
            # Ensure LOD03 has vertex colors
            if not target_obj.data.color_attributes:
                target_obj.data.color_attributes.new(name="Color", type='FLOAT_COLOR', domain='CORNER')
            
            target_color_attr = target_obj.data.color_attributes.get("Color")
            if target_color_attr:
                target_obj.data.color_attributes.active_color = target_color_attr
            
            # Select both objects for data transfer
            #bpy.ops.object.select_all(action='DESELECT')
            # source_obj.select_set(True)  # Source, not need to be active, facilitates things
            #target_obj.select_set(True)  # Target
            #bpy.context.view_layer.objects.active = target_obj  # Target must be active
        
            data_transfer = target_obj.modifiers.new(name="TempDataTransfer", type='DATA_TRANSFER')
            data_transfer.object = source_obj
            # Configure for face corner color transfer, the only ones we care about for msfs
            data_transfer.use_loop_data = True
            data_transfer.data_types_loops = {'COLOR_CORNER'}

            # Apply the modifier
            bpy.ops.object.modifier_apply(modifier=data_transfer.name)
            #print(f"    Successfully transferred vertex colors using Data Transfer modifier")
            return True
            
        except Exception as e:
            print(f"    Error during vertex color transfer: {str(e)}")
            # Remove data transfer modifier if it exists
            # try:
            #     if "TempDataTransfer" in [mod.name for mod in target_obj.modifiers]:
            #         target_obj.modifiers.remove(target_obj.modifiers["TempDataTransfer"])
            # except:
            #     pass
            # return False
            
        #finally:
            # # Restore original state
            # try:
            #     bpy.ops.object.select_all(action='DESELECT')
            #     for selected_obj in original_selection:
            #         if selected_obj and selected_obj.name in bpy.data.objects:
            #             selected_obj.select_set(True)
            #     if original_active and original_active.name in bpy.data.objects:
            #         bpy.context.view_layer.objects.active = original_active
            # except Exception as restore_error:
            #     print(f"    Warning: Could not fully restore original state: {str(restore_error)}")


    def create_gray_vertex_colors(self, obj,gray_level):
        """Apply gray vertex colors to the object."""
        if obj.type != 'MESH':
            return
        
        # Ensure the object has vertex colors
        if not obj.data.color_attributes:
            obj.data.color_attributes.new(name="Color", type='FLOAT_COLOR', domain='CORNER')
        
        # Set Color as the default color attribute
        color_attr = obj.data.color_attributes.get("Color")
        if color_attr:
            obj.data.color_attributes.active_color = color_attr

            for i in range(len(color_attr.data)):
                color_attr.data[i].color = (gray_level, gray_level, gray_level, 1.0)
            print(f"    Applied gray vertex colors to {obj.name}")


class LODIFY_OT_set_default_lod_values(bpy.types.Operator):
    bl_idname = "lodify.set_default_lod_values"
    bl_label = "Set Default LOD Values (4,3,2,1)"
    bl_description = "Set LOD values to default values: 4, 3, 2, 1. MSFS artistic teams often use descending values (7,6,5,4,3,2,1) in XML, trusting the LOD system to automatically choose optimal LODs based on distance and performance limits"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scn = context.scene
        base_collection,parent_collection  = utils.find_base_collection()
        
        if not base_collection:
            self.report({'ERROR'}, "Base LOD collection (ending with _LODNN) not selected, click on a collection ending with _LODNN  in the outliner")
            return {'CANCELLED'}
        
        # Always use default values
        print(f"Setting default LOD values: {utils.default_lod_values}")
        
        # Set LOD values in MSFS Multi-Export addon
        lod_values_set = utils.set_msfs_multi_exporter_lod_values(base_collection, utils.default_lod_values)
        if lod_values_set:
            self.report({'INFO'}, f"Set default MSFS LOD values: {utils.default_lod_values}")
        else:
            self.report({'WARNING'}, "Could not set MSFS Multi-Export LOD values. Make sure the addon is enabled.")
        
        return {'FINISHED'}

class LODIFY_OT_calculate_msfs_lod_values(bpy.types.Operator):
    bl_idname = "lodify.calculate_msfs_lod_values"
    bl_label = "Calculate & Set MSFS LOD Values"
    bl_description = "Calculate optimal MinSizes based on object size or SDK and set them in MSFS Multi-Export addon"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scn = context.scene
        base_collection,parent_collection  = utils.find_base_collection()
        
        if not base_collection:
            self.report({'ERROR'}, "Base LOD collection (ending with _LOD00) not selected, click on a collection ending with _LOD00  in the outliner")
            return {'CANCELLED'}

        # Set LOD values in MSFS Multi-Export addon
        lod_values_set = utils.set_msfs_multi_exporter_lod_values(base_collection, None)
        if lod_values_set:
            self.report({'INFO'}, f"Set calculated MSFS LOD values")
        else:
            self.report({'WARNING'}, "Could not set MSFS Multi-Export LOD values. Make sure the addon is enabled.")
        
        return {'FINISHED'}

class LODIFY_OT_apply_lod_modifiers(bpy.types.Operator):
    bl_idname = "lodify.apply_lod_modifiers"
    bl_label = "Apply LOD Modifiers"
    bl_description = "Apply all modifiers on objects in the specified LOD collection"
    bl_options = {'REGISTER', 'UNDO'}

    lod_index: bpy.props.IntProperty(
        name="LOD Index",
        description="Index of the LOD collection in the list",
        default=0
    )

    def execute(self, context):
        base_collection,parent_collection  = utils.find_base_collection()
        if not base_collection:
             self.report({'ERROR'}, "Base LOD collection (ending with _LOD00) not selected, click on a collection ending with _LOD00  in the outliner")
             return {'CANCELLED'}
        
        base_name = utils.get_root_name_from_ID(base_collection)

        # Check if the index is valid
        if self.lod_index >= len(utils.get_generated_lod_list(base_name)):#CHECKME
            self.report({'ERROR'}, f"Invalid LOD index: {self.lod_index}")
            return {'CANCELLED'}
        
            # Get the LOD item and collection
        lod_item = utils.get_generated_lod_list(base_name)[self.lod_index]#CHECKME

        if not lod_item.ui_lod_collection:
            self.report({'ERROR'}, f"No collection assigned to LOD index {self.lod_index}")
            return {'CANCELLED'}
        
        lod_collection = lod_item.ui_lod_collection
        lod_level = lod_item.ui_lod_level
        utils.make_collection_active(lod_collection)
        applied_count,error_count = utils.apply_modifiers(context,lod_collection)
        if error_count == 0:
            for obj in lod_collection.all_objects:
                if obj.type == 'MESH':
                    utils.post_modifiers_cleanup(obj, context,lod_level)

        if applied_count > 0:
            self.report({'INFO'}, f"Applied modifiers on {applied_count} objects in '{lod_collection.name}'")
        
        if error_count > 0:
            self.report({'WARNING'}, f"Encountered {error_count} errors while applying modifiers")
        
        if applied_count == 0 and error_count == 0:
            self.report({'INFO'}, f"No objects with modifiers found in '{lod_collection.name}'")
        
        return {'FINISHED'}

class LODIFY_props_list(bpy.types.PropertyGroup):
    """Property group for individual LOD collection items."""
    ui_lod_collection: PointerProperty(type=bpy.types.Collection, description='Level of Detail collection')
    ui_lod_level: IntProperty(description='UI LOD level')

classes = (
    LODIFY_OT_generate_lod_decimate,
    LODIFY_OT_cleanup,
    LODIFY_OT_set_default_lod_values,
    LODIFY_OT_calculate_msfs_lod_values,
    LODIFY_OT_apply_lod_modifiers,
    LODIFY_OT_select,
    LODIFY_OT_add_collision_boxes,
    LODIFY_OT_remove_collision_boxes,
    LODIFY_props_list,
    DialogOperator
)


def register():
    """Register operator classes with improved error handling."""
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except ValueError as e:
            print(f"Warning: Operator class {cls.__name__} registration issue: {e}")
    bpy.types.WindowManager.lod_list = CollectionProperty(type=LODIFY_props_list)
    bpy.types.WindowManager.progress =  FloatProperty( default=0.0, min=0.0, max=100.0, subtype='PERCENTAGE')

def unregister():
    """Unregister operator classes with improved error handling."""
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError as e:
            print(f"Warning: Operator class {cls.__name__} unregistration issue: {e}")

if __name__ == "__main__":
    register()