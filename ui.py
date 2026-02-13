# ui.py

import bpy
import mathutils
from bpy.types import Panel, UIList
from . import utils



class LODIFY_PT_main_panel(bpy.types.Panel):
    """Main LOD system panel with modern design."""
    bl_label = "MSFS LOD Maker"
    bl_idname = "LODIFY_PT_main_panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        layout = self.layout
        scn = context.scene
        #layout.prop(scn.lod, "lod_enabled", text="")

    def draw(self, context):
        layout = self.layout
        scn = context.scene
        lod_props = scn.lod
        main = layout.column()



class LODIFY_PT_generation_settings(bpy.types.Panel):
    """LOD generation settings panel."""
    bl_label = "Generation Settings"
    bl_idname = "LODIFY_PT_generation_settings"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"
    bl_parent_id = "LODIFY_PT_main_panel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scn = context.scene
        lod_props = scn.lod

        # Generation Method
        box = layout.box()
        col = box.column()

        # LOD Selection
        col.separator() 
        col.label(text="LOD Generation Method", icon='MODIFIER')
        # Create a row with checkboxes for LOD selection
        row = col.row(align=True)
        row.prop(lod_props, "generate_lod01", text="LOD01")
        row.prop(lod_props, "generate_lod02", text="LOD02") 
        row.prop(lod_props, "generate_lod03", text="LOD03")

        # Basic Settings
        col.separator()
        row = col.row(align=True)
        row.prop(lod_props, "lod1_small_object_threshold", text="Small Obj. Thresh.")
        row.prop(lod_props, "lod2_small_object_threshold", text="Small Obj. Thresh.")
        row.prop(lod_props, "lod3_small_object_threshold", text="Small Obj. Thresh.")

        col.separator(factor = 2.0,type = 'LINE')
        row = col.row(align=True)
        split = row.split(factor = 0.2)
        split.label(text = "pass 1")
        split.prop(lod_props, "lod1_pass1_method", text="")
        split = row.split(factor = 0.2)
        split.label(text = "")
        split.prop(lod_props, "lod2_pass1_method", text="")
        split = row.split(factor = 0.2)
        split.label(text = "")
        split.prop(lod_props, "lod3_pass1_method", text="")

        col.separator(factor = 2.0,type = 'LINE')
        row = col.row(align=True)
        split = row.split(factor = 0.2)
        split.label(text = "pass 2")
        split.prop(lod_props, "lod1_pass2_method", text="")
        split = row.split(factor = 0.2)
        split.label(text = "")
        split.prop(lod_props, "lod2_pass2_method", text="")
        split = row.split(factor = 0.2)
        split.label(text = "")
        split.prop(lod_props, "lod3_pass2_method", text="")

        col.separator(factor = 2.0,type = 'LINE')
        row = col.row(align=True)
        row.prop(lod_props, "lod1_decimate_planar_angle", text="Decimate Angle")
        row.prop(lod_props, "lod2_decimate_planar_angle", text="Decimate Angle")
        row.prop(lod_props, "lod3_decimate_planar_angle", text="Decimate Angle")

        row = col.row(align=True)
        row.prop(lod_props, "lod1_decimate_collapse_ratio", text="Collapse ratio")
        row.prop(lod_props, "lod2_decimate_collapse_ratio", text="Collapse ratio")
        row.prop(lod_props, "lod3_decimate_collapse_ratio", text="Collapse ratio")

        row = col.row(align=True)
        row.prop(lod_props, "lod1_decimate_unsubdiv_iterations", text="Un-Subdiv. iters.")
        row.prop(lod_props, "lod2_decimate_unsubdiv_iterations", text="Un-Subdiv. iters.")
        row.prop(lod_props, "lod3_decimate_unsubdiv_iterations", text="Un-Subdiv. iters.")
        
        row = col.row(align=True)
        row.prop(lod_props, "show_advanced_settings", icon='TRIA_DOWN' if lod_props.show_advanced_settings else 'TRIA_RIGHT')

        if lod_props.show_advanced_settings:
            #col.separator(factor = 2.0,type = 'LINE')
            #col.label(text="Advanced Settings", icon='PREFERENCES')
            row = col.row(align=True)
            row.prop(lod_props, "lod1_gamma_corr", text="Gamma corr.")
            row.prop(lod_props, "lod2_gamma_corr", text="Gamma corr.")
            row.prop(lod_props, "lod3_gamma_corr", text="Gamma corr.")
            row = col.row(align=True)
            row.prop(lod_props, "lod1_merge_threshold", text="Merge thresh.")
            row.prop(lod_props, "lod2_merge_threshold", text="Merge thresh.")
            row.prop(lod_props, "lod3_merge_threshold", text="Merge thresh.") 
            row = col.row(align=True)
            row.prop(lod_props, "auto_apply_modifiers", text="Auto apply modifiers")
            row = col.row(align=True)
            row.alignment = 'LEFT'
            row.prop(lod_props, "vertex_color_mode", text="Vertex Colors")
            row = col.row(align=True)
            row.alignment = 'LEFT'
            row.prop(lod_props, "triangulate_after_shrinkwarp", text="Triangulate after shrinkwrap")
            row = col.row(align=True)
            row.prop(lod_props, "shrinkwarp_bottom_face", text="Shrinkwrap bottom face too")
            # row = col.row(align=True)
            # row.alignment = 'LEFT'
            # row.prop(lod_props, "lodify_children_names", text="Lodify children's names")
            #row.prop(lod_props, "lodify_leave_lod0_alone", text="Leave lod0 alone")
            row = col.row(align=True)
            row.alignment = 'LEFT'
            row.prop(lod_props, "minsizes_method", text="MinSize calculation method",expand = True)
            if scn.lod.get("minsizes_method", 1) == 1:
                row.prop(lod_props, "lod_minsizes_quality", text=" MSFS LOD curve")
            row = col.row()
            row.alignment = 'LEFT'
            row.prop(lod_props, "insert_token", text="Inserted token")
            row.label(text = "(To revert: cleanup and manually remove it from lod0 names)")
            row = col.row()
            row.alignment = 'LEFT'
            row.prop(lod_props, "collision_boxes_to_lod0_only", text="Collision boxes to lod0 only")

            


class LODIFY_PT_msfs_optimization(bpy.types.Panel):
    """MSFS optimization settings panel."""
    bl_label = "MSFS LOD MinSizes"
    bl_idname = "LODIFY_PT_msfs_optimization"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"
    bl_parent_id = "LODIFY_PT_main_panel"

    def draw(self, context):
        layout = self.layout
        scn = context.scene
        lod_props = scn.lod

        base_collection,parent_collection = utils.find_base_collection()
        # LOD Value Calculation
        box = layout.box()
        col = box.column()
        col.label(text="MinSizes Calculation", icon='DRIVER_DISTANCE')
        
        col.prop(lod_props, "use_automatic_lod_calculation", text="Automatic Calculation")
        
        if not lod_props.use_automatic_lod_calculation:
            col.prop(lod_props, "manual_lod_values", text="Manual Values")
        
        # Action Buttons
        col.separator()
        row = col.row(align=True)
        row.scale_y = 1.2
        
        if base_collection and  len(list(utils.get_generated_lod_list())) > 0:
            # Set Default button with enhanced styling
            default_op = row.operator("lodify.set_default_lod_values", text="Set Default MinSizes", icon='PRESET')
            # Calculate button
            calc_op = row.operator("lodify.calculate_msfs_lod_values", text="Calculate & Apply", icon='AUTO')

        #row.active = not base_collection  is None


class LODIFY_PT_generation_actions(bpy.types.Panel):
    """LOD generation action buttons panel."""
    bl_label = "Generate LODs"
    bl_idname = "LODIFY_PT_generation_actions"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"
    bl_parent_id = "LODIFY_PT_main_panel"

    def draw(self, context):
        layout = self.layout
        scn = context.scene
        lod_props = scn.lod

        # Main Generation Button
        box = layout.box()
        col = box.column()
        
        # Primary action button
        row = col.row()
        row.scale_y = 1.5
        
        base_collection,parent_collection = utils.find_base_collection()
        if base_collection:
            generated  = len(list(utils.get_generated_lod_list())) > 0

            button_text = "Generate LODs - " +  (base_collection.name if base_collection else "no selection")
            row.operator("lodify.generate_lod_decimate", text=button_text, icon='MOD_DECIM')
            #row.alignment = 'CENTER'
            #row.active = not base_collection  is None
            #cleanup
            col.separator(factor = 2.0,type = 'LINE')
            row = col.row()
            row.scale_y = 1.5
            button_text = "Cleanup - " +  (base_collection.name if base_collection else "no selection")
            row.operator("lodify.cleanup", text = button_text, icon='TRASH')
            #row.alignment = 'CENTER'
            col.separator(factor = 2.0,type = 'LINE')
            row = col.row()
            row.scale_y = 1.5
            
            button_text = "Add collision boxes to lod0" if scn.lod.collision_boxes_to_lod0_only else "Add collision boxes"
            row.operator("lodify.add_collision_boxes", text = button_text, icon='CUBE')
            row.operator("lodify.remove_collision_boxes", text = "Remove collision boxes", icon='EMPTY_DATA')
            #row.alignment = 'CENTER'
            #row.active = not base_collection  is None

            stats_report = utils.update_stats_report_and_minsizes(context,utils.get_root_name_from_ID(base_collection))
            minsizes,obj_size = utils.get_lod_values(context, base_collection)
            srp0 = stats_report[0]
            srp1 = stats_report[1]
            srp2 = stats_report[2]
            srp3 = stats_report[3]

            #minsizes_v = mathutils.Vector(minsizes)

            col.separator(factor = 2.0,type = 'LINE')
            row = col.row()
            row.active = generated
            col = row.column()
            col.alignment = 'LEFT'
            col.operator("lodify.select",text = "Show all").lod_level = -1
            col.label(text = "Vertices")
            col.label(text = "Polygons")
            col.label(text = "Materials")

            col = row.column(align=True)
            col.alignment = 'RIGHT'
            col.operator("lodify.select",text = "LOD0" if minsizes[0] == -1.0 else f"LOD0 ({minsizes[0]:.01f})").lod_level = 0
            col.label(text=f"{srp0[0] if srp0[0] != -1.0 else 'N/A'}")
            col.label(text=f"{srp0[1] if srp0[1] != -1.0 else 'N/A'}")
            col.label(text=f"{srp0[2] if srp0[2] != -1.0 else 'N/A'}")

            col = row.column(align=True)
            col.alignment = 'RIGHT'
            col.operator("lodify.select",text = "LOD1" if minsizes[1] == -1.0 else f"LOD1 ({minsizes[1]:.01f})").lod_level = 1
            col.label(text=f"{srp1[0] if srp1[0] != -1.0 else 'N/A'}")
            col.label(text=f"{srp1[1] if srp1[1] != -1.0 else 'N/A'}")
            col.label(text=f"{srp1[2] if srp1[2] != -1.0 else 'N/A'}")

            col = row.column(align=True)
            col.alignment = 'RIGHT'
            col.operator("lodify.select",text = "LOD2" if minsizes[2] == -1.0 else f"LOD2 ({minsizes[2]:.01f})").lod_level = 2
            col.label(text=f"{srp2[0] if srp2[0] != -1.0 else 'N/A'}")
            col.label(text=f"{srp2[1] if srp2[1] != -1.0 else 'N/A'}")
            col.label(text=f"{srp2[2] if srp2[2] != -1.0 else 'N/A'}")

            col = row.column(align=True)
            col.alignment = 'RIGHT'
            col.operator("lodify.select",text = "LOD3" if minsizes[3] == -1.0 else f"LOD3 ({minsizes[3]:.01f})").lod_level = 3
            col.label(text=f"{srp3[0] if srp3[0] != -1.0 else 'N/A'}")
            col.label(text=f"{srp3[1] if srp3[1] != -1.0 else 'N/A'}")
            col.label(text=f"{srp3[2] if srp3[2] != -1.0 else 'N/A'}")
        else:
            row = col.row()
            row.alignment = 'CENTER'
            row.label(text="Please select a lod0 collection (name ending with '_LOD00') or one of its children")



class LODIFY_PT_modifier_tools(bpy.types.Panel):
    """Modifier application tools panel."""
    bl_label = "Modifier Tools"
    bl_idname = "LODIFY_PT_modifier_tools"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"
    bl_parent_id = "LODIFY_PT_main_panel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scn = context.scene
        lod_props = scn.lod

        # Modifier Application Section
        box = layout.box()
        col = box.column()
        col.label(text="Apply Modifiers (All Collection Objects)", icon='MODIFIER')
        
        base_collection,parent_collection = utils.find_base_collection()
        
        if base_collection:
            generated = len(list(utils.get_generated_lod_list())) > 0
            if generated:
                # Create buttons for each LOD
                for i, item in enumerate(utils.get_generated_lod_list()):
                    if item.ui_lod_collection:  # Only show if collection is assigned
                        row = col.row()
                        apply_op = row.operator("lodify.apply_lod_modifiers", text=f"Apply {item.ui_lod_collection.name} Modifiers")
                        row.active = not base_collection  is None
                        apply_op.lod_index = i


# Class registration
classes = (
    LODIFY_PT_main_panel,
    LODIFY_PT_generation_settings,
    LODIFY_PT_generation_actions,
    LODIFY_PT_modifier_tools,
    LODIFY_PT_msfs_optimization
)

def register():
    """Register UI classes with error handling."""
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except ValueError as e:
            print(f"Warning: UI class {cls.__name__} registration issue: {e}")

def unregister():
    """Unregister UI classes with error handling."""
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError as e:
            print(f"Warning: UI class {cls.__name__} unregistration issue: {e}")

if __name__ == "__main__":
    register()