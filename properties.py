# properties.py

import bpy
from bpy.props import FloatProperty, IntProperty, BoolProperty, PointerProperty, StringProperty, EnumProperty

class LODIFY_props_scn(bpy.types.PropertyGroup):
    """Main property group for LOD system settings."""

    # MSFS LOD Optimization Settings
    use_automatic_lod_calculation: BoolProperty(
        name="Use Automatic LOD Calculation",
        description="Automatically calculate optimal LOD values based on object size and MSFS 2024 standards",
        default=True
    )
    
    progressive_mode: BoolProperty(
        name="Inherit from higher lod",
        description="Inherit from closest more detailed lod instead of from lod0",
        default=True
    )

    collision_boxes_to_lod0_only: BoolProperty(
        name="collision boxes to lod0 only",
        description="Calculate collision boxes for lod0 only",
        default=True
    )

    collision_boxes_target: EnumProperty(
        name="collision boxes target",
        description="Create collision boxes around collections or objects",
        items=[
            ('COLLECTIONS', "Collections", "Create collisison boxes around collections containing objects"),
            ('OBJECTS', "Objects", "Create collisison boxes around objects"),
        ],
        default='COLLECTIONS'
    )

    manual_lod_values: StringProperty(
        name="Manual LOD Values",
        description="Comma-separated LOD values (e.g., '12,3,2,1') for manual override. Only used when automatic calculation is disabled",
        default="4.0,3.0,2.0,1.0"
    )
    
    insert_token: StringProperty(
        name="Insert token",
        description="Inserted in the middle of ID names, helps the multi-exporter to recognize our objects",
        default=""
    )

    # Advanced Settings
    show_advanced_settings: BoolProperty(
        name="Show Advanced Settings",
        description="Show advanced LOD generation and optimization settings",
        default=False
    )
    
    vertex_color_mode: EnumProperty(
        name="Vertex Color Mode",
        description="How to handle vertex colors in LOD generation",
        items=[
            ('AUTO', "Automatic", "LOD01: white, LOD02-03: baked from albedo"),
            ('WHITE_ONLY', "White Only", "Apply white vertex colors to all LOD01-03"),
            ('BAKE_ALL', "Bake All", "LOD01-03: baked from albedo"),
           # ('TRANSFER_ALL', "Transfer All", "Transferred vertex color from upstream")
        ],
        default='AUTO'
    )

    shrinkwarp_bottom_face: BoolProperty(
        name="shrinkwrap bottom face", 
        description="Use a closed cube for shrinkwrap",
        default=True
    )

    # LOD Selection Settings
    generate_lod01: BoolProperty(
        name="Generate LOD01",
        description="Generate or freeze LOD01 level",
        default=True
    )

    lod1_small_object_threshold: FloatProperty(
        name="Small Object Threshold - LOD1",
        description="Objects smaller than this size will be removed from this LOD. Set to 0 to keep all objects",
        default=0.1,
        min=0.0,
        max=10.0,
        precision=3,
        unit='LENGTH'
    )

    lod1_pass2_method: EnumProperty(
        name="LOD1 pass 2 generation Method",
        description="Choose the method for generating LODs",
        items=[
            ('PLANAR', "Planar", "Use decimate planar method for this LOD"),
            ('COLLAPSE', "Collapse", "Use decimate collapse method for this LOD"),
            ('UNSUBDIVIDE', "Un-Subdivide", "Use decimate un-subdivide method for this LOD"),
            ('SKIP', "Do nothing", "Do nothing for this LOD")
        ],
        default='SKIP'
    )

    lod1_pass1_method: EnumProperty(
        name="LOD1 pass 1 generation Method",
        description="Choose the method for generating LODs",
        items=[
            ('PLANAR', "Planar", "Use decimate planar method for this LOD"),
            ('COLLAPSE', "Collapse", "Use decimate collapse method for this LOD"),
            ('UNSUBDIVIDE', "Un-Subdivide", "Use decimate un-subdivide method for this LOD"),            
            ('SHRINKWRAP + UNSUBDIVIDE', "Shrinkwrap + Unsubdivide", "Use shrinkwrap method followed by unsubdivide for this LOD"),
            ('SHRINKWRAP + PLANAR', "Shrinkwrap + Planar", "Use shrinkwrap method followed by planar for this LOD"),
            ('SHRINKWRAP + COLLAPSE', "Shrinkwrap + Collapse", "Use shrinkwrap method followed by collapse for this LOD"),
            ('JUST CUBES', "Just cubes", "Only enclosing cubes for this LOD"),
            ('SKIP', "Do nothing", "Do nothing for this LOD")
        ],
        default='PLANAR'
    )

    lod1_decimate_planar_angle: IntProperty(
        name="Decimate Planar Angle - LOD1",
        description="Planar Angle Limit of the Decimate Modifier for this LOD",
        default=15,
        min=0,
        max=90,
        step=5
    )

    lod1_decimate_collapse_ratio: FloatProperty(
        name="Decimate Collapse Ratio - LOD1",
        description="Collapse ratio of the Decimate Modifier for this LOD",
        default=0.9,
        min=0.0,
        max=1.0,
        step=5
    )

    lod1_decimate_unsubdiv_iterations: IntProperty(
        name="Decimate Un-subdivide iterations - LOD1",
        description="Number of Un-subdivide iterations of the Decimate Modifier for this LOD",
        default=0,
        min=0,
        max=100,
        step=1
    )

    lod1_gamma_corr: IntProperty(
        name="Gamma correction - LOD1",
        description="Gamma correction for this LOD -10..10",
        default=0,
        min=-10,
        max=10,
        step=1
    )

    lod1_merge_threshold: FloatProperty(
        name="Merge Threshold - LOD1",
        description="Merge Threshold for this LOD (in meters)",
        default=0.0,
        precision = 4,
        min=0.0,
        unit='LENGTH'
    )
    #LOD2
    generate_lod02: BoolProperty(
        name="Generate LOD02", 
        description="Generate or freeze LOD02 level",
        default=True
    )
    
    lod2_small_object_threshold: FloatProperty(
        name="Small Object Threshold - LOD2",
        description="Objects smaller than this size will be removed from this LOD. Set to 0 to keep all objects",
        default=0.1,
        min=0.0,
        max=10.0,
        precision=3,
        unit='LENGTH'
    )

    lod2_pass2_method: EnumProperty(
        name="LOD2 pass 2 generation Method",
        description="Choose the method for generating this LOD",
        items=[
            ('PLANAR', "Planar", "Use decimate planar method for this LOD"),
            ('COLLAPSE', "Collapse", "Use decimate collapse method for this LOD"),
            ('UNSUBDIVIDE', "Un-Subdivide", "Use decimate un-subdivide method for this LOD"),
            ('SKIP', "Do nothing", "Do nothing for this LOD")
        ],
        default='SKIP'
    )

    lod2_pass1_method: EnumProperty(
        name="LOD2 pass 1 generation Method",
        description="Choose the method for generating this LOD",
        items=[
            ('PLANAR', "Planar", "Use decimate planar method for this LOD"),
            ('COLLAPSE', "Collapse", "Use decimate collapse method for this LOD"),
            ('UNSUBDIVIDE', "Un-Subdivide", "Use decimate un-subdivide method for this LOD"),
            ('SHRINKWRAP + UNSUBDIVIDE', "Shrinkwrap + Unsubdivide", "Use shrinkwrap method followed by unsubdivide for this LOD"),
            ('SHRINKWRAP + PLANAR', "Shrinkwrap + Planar", "Use shrinkwrap method followed by planar for this LOD"),
            ('SHRINKWRAP + COLLAPSE', "Shrinkwrap + Collapse", "Use shrinkwrap method followed by collapse for this LOD"),
            ('JUST CUBES', "Just cubes", "Only enclosing cubes for this LOD"),
            ('SKIP', "Do nothing", "Do nothing for this LOD")
        ],
        default='PLANAR'
    )

    lod2_decimate_planar_angle: IntProperty(
        name="Decimate Planar Angle - LOD2",
        description="Planar Angle Limit of the Decimate Modifier for this LOD",
        default=30,
        min=0,
        max=90,
        step=5
    )

    lod2_decimate_collapse_ratio: FloatProperty(
        name="Decimate Collapse Ratio - LOD2",
        description="Collapse ratio of the Decimate Modifier for this LOD",
        default=0.7,
        min=0.0,
        max=1.0,
        step=5
    )

    lod2_decimate_unsubdiv_iterations: IntProperty(
        name="Decimate Un-subdivide iterations - LOD2",
        description="Number of Un-subdivide iterations of the Decimate Modifier for this LOD",
        default=1,
        min=0,
        max=100,
        step=1
    )

    lod2_gamma_corr: IntProperty(
        name="Gamma correction - LOD2",
        description="Gamma correction for this LOD -10..10",
        default=0,
        min=-10,
        max=10,
        step=1
    )

    lod2_merge_threshold: FloatProperty(
        name="Merge Threshold - LOD2",
        description="Merge Threshold for this LOD (in meters)",
        default=0.0,
        precision = 4,
        min=0.0,
        unit='LENGTH'
    )
    #LOD3
    generate_lod03: BoolProperty(
        name="Generate LOD03",
        description="Generate or freeze LOD03 level", 
        default=True
    )

    lod3_small_object_threshold: FloatProperty(
        name="Small Object Threshold - LOD3",
        description="Objects smaller than this size will be removed from this LOD. Set to 0 to keep all objects",
        default=0.1,
        min=0.0,
        max=10.0,
        precision=3,
        unit='LENGTH'
    )

    lod3_pass2_method: EnumProperty(
        name="LOD3 pass 2 generation Method",
        description="Choose the method for generating this LOD",
        items=[
            ('PLANAR', "Planar", "Use decimate planar method for this LOD"),
            ('COLLAPSE', "Collapse", "Use decimate collapse method for this LOD"),
            ('UNSUBDIVIDE', "Un-Subdivide", "Use decimate un-subdivide method for this LOD"),
            ('SKIP', "Do nothing", "Do nothing for this LOD")
        ],
        default='PLANAR'
    )

    lod3_pass1_method: EnumProperty(
        name="LOD3 pass 1 generation Method",
        description="Choose the method for generating this LOD",
        items=[
            ('PLANAR', "Planar", "Use decimate planar method for this LOD"),
            ('COLLAPSE', "Collapse", "Use decimate collapse method for this LOD"),
            ('UNSUBDIVIDE', "Un-Subdivide", "Use decimate un-subdivide method for this LOD"),
            ('SHRINKWRAP + UNSUBDIVIDE', "Shrinkwrap + Unsubdivide", "Use shrinkwrap method followed by unsubdivide for this LOD"),
            ('SHRINKWRAP + PLANAR', "Shrinkwrap + Planar", "Use shrinkwrap method followed by planar for this LOD"),
            ('SHRINKWRAP + COLLAPSE', "Shrinkwrap + Collapse", "Use shrinkwrap method followed by collapse for this LOD"),
            ('JUST CUBES', "Just cubes", "Only enclosing cubes for this LOD"),
            ('SKIP', "Do nothing", "Do nothing for this LOD")
        ],
        default='SHRINKWRAP + UNSUBDIVIDE'
    )

    lod3_decimate_planar_angle: IntProperty(
        name="Decimate Planar Angle - LOD3",
        description="Planar Angle Limit of the Decimate Modifier for this LOD",
        default=60,
        min=0,
        max=90,
        step=5
    )

    lod3_decimate_collapse_ratio: FloatProperty(
        name="Decimate Collapse Ratio - LOD3",
        description="Collapse ratio of the Decimate Modifier for this LOD",
        default=0.3,
        min=0.0,
        max=1.0,
        step=5
    )

    lod3_decimate_unsubdiv_iterations: IntProperty(
        name="Decimate Un-subdivide iterations - LOD3",
        description="Number of Un-subdivide iterations of the Decimate Modifier for this LOD",
        default=2,
        min=0,
        max=100,
        step=1
    )

    lod3_gamma_corr: IntProperty(
        name="Gamma correction - LOD3",
        description="Gamma correction for this LOD -10..10",
        default=0,
        min=-10,
        max=10,
        step=1
    )

    lod3_merge_threshold: FloatProperty(
        name="Merge Threshold - LOD3",
        description="Merge Threshold for this LOD (in meters)",
        default=0.0,
        precision = 4,
        min=0.0,
        unit='LENGTH'
    )
    
    
    triangulate_after_shrinkwarp: BoolProperty(
        name="Triangulate after shrinkwrap",
        description="Apply triangulate modifier after shrinkwrap", 
        default=True
    )

    auto_apply_modifiers: BoolProperty(
        name="Auto apply modifiers",
        description="Apply modifiers automatically", 
        default=True
    )
    
    minsizes_method: EnumProperty(
        name="LOD minsizes calculation method",
        description="Choose the method for calculating minSizes",
        items=[
            ('NATIVE', "Native - size based", "Use the addon's formula based in size"),
            ('SDK TABLE', "SDK Table", "Lookup the table according by the vertices count and LOD quality")
        ],
        default='SDK TABLE'
    )

    lod_minsizes_quality: EnumProperty(
        name="LOD minsizes quality curve",
        description="Choose the overall LOD quality curve",
        items=[
            ('ULTRA', "Ultra", "Ultra quality curve"),
            ('HIGH', "High", "High quality curve"),
            ('MEDIUM', "Medium", "Medium quality curve"),
            ('LOW', "Low", "Low quality curve")
        ],
        default='HIGH'
    )

classes = (
    LODIFY_props_scn,
)

def register():
    """Register property classes with improved error handling."""
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except ValueError as e:
            print(f"Warning: Class {cls.__name__} registration issue: {e}")
    # Register the main scene property
    bpy.types.Scene.lod = PointerProperty(type=LODIFY_props_scn)

def unregister():
    """Unregister property classes with improved error handling."""
    # Remove scene property first
    if hasattr(bpy.types.Scene, "lod"):
        del bpy.types.Scene.lod
    # Unregister classes in reverse order
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError as e:
            print(f"Warning: Class {cls.__name__} unregistration issue: {e}")

if __name__ == "__main__":
    register()