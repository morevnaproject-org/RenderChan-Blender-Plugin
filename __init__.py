import bpy
from bpy.app.handlers import persistent
from bpy.types import Operator
from bpy_extras.io_utils import ImportHelper
import subprocess
import os.path
from bpy.props import *

bl_info = {
    "name": "Import rendered files with RenderChan",
    "author": "scribblemaniac",
    "version": (0, 1),
    "blender": (2, 76, 0),
    "location": "File > Import > RenderChan Dependency",
    "description": "Imports various file types and renders them with RenderChan so they can be imported into Blender.",
    "warning": "This requires RenderChan, and may require other binaries depending on the file being rendered",
    "category": "Import-Export"
}

def draw_render_options(layout, scene):
    layout.prop(scene.renderchan, "profile")
    layout.prop(scene.renderchan, "stereo")
    layout.prop(scene.renderchan, "render_farm")
    
    if scene.renderchan.render_farm == "puli":
        layout.prop(scene.renderchan, "host")
        layout.prop(scene.renderchan, "port")
    elif scene.renderchan.render_farm == "afantasy":
        layout.prop(scene.renderchan, "cgru_location")

def add_import_button(self, context):
    self.layout.operator(RenderChanImporter.bl_idname, text="RenderChan Dependency")

def add_add_button(self, context):
    self.layout.operator_context = "INVOKE_REGION_WIN"
    self.layout.operator(RenderChanSequenceAdd.bl_idname, text="RenderChan Dependency")

class LoadDialog(bpy.types.Operator):
    bl_idname = "object.rc_load_dialog"
    bl_label = "RenderChan"
 
    should_update = BoolProperty(name="Update?", description="Should dependencies be updated?", default=True)
    
    def draw(self, context):
        self.layout.label("Modified dependencies detected.")
        self.layout.prop(self, "should_update")
        # Draw does not appear to be called on property updates for dialogs, so we can't use draw_render_options
        self.layout.prop(context.scene.renderchan, "profile")
        self.layout.prop(context.scene.renderchan, "stereo")
        self.layout.separator()
        self.layout.prop(context.scene.renderchan, "render_farm")
        renderfarm_row = self.layout.row()
        puli_column = renderfarm_row.column()
        puli_column.label("Puli")
        puli_column.prop(context.scene.renderchan, "host")
        puli_column.prop(context.scene.renderchan, "port")
        afantasy_column = renderfarm_row.column()
        afantasy_column.label("Afantasy")
        afantasy_column.label("Cgru Location:")
        afantasy_column.prop(context.scene.renderchan, "cgru_location", text="") 
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
 
    def execute(self, context):
        if self.should_update:
            try:
                subprocess.check_call(["renderchan", "--deps", context.blend_data.filepath])
            except subprocess.CalledProcessError as e:
                self.report({"ERROR"}, "RenderChan encountered an error")
        return {'FINISHED'}

class RCRefreshImage(bpy.types.Operator):
    bl_idname = "image.rc_refresh"
    bl_label = "Rerender"
    
    def execute(self, context):
        try:
            subprocess.check_call(["renderchan", context.edit_image.filepath_from_user()])
        except subprocess.CalledProcessError as e:
            self.report({"ERROR"}, "RenderChan encountered an error")
        bpy.ops.image.reload()
        return {"FINISHED"}

class RenderOptions(bpy.types.PropertyGroup):
    profile = StringProperty(name="Profile", description="What profile RenderChan should use. Leave blank to use the project's default.")
    stereo = EnumProperty(items=[("none", "None", "Do not render with stereo-3D."), ("v", "Vertical", "Vertical stereo-3D"), ("h", "Horizontal", "Horizontal stereo-3D"), \
        ("l", "Left", "Left stereo image"), ("r", "Right", "Right stereo image")], name="Stereo", description="The type of stereoscopic 3D rendering to use.", default="none")
    render_farm = EnumProperty(items=[("none", "None", "Do not use a render farm"), ("puli", "Puli render farm", "Use Puli render farm"), \
        ("afantasy", "Afantasy render farm", "Use Afantasy render farm")], name="Render farm", description="Determines what render farm, if any, to use.", default="none")
    # Puli render farm only
    host = StringProperty(name="Host", description="Renderfarm server host for Puli renderfarm", default="127.0.0.1")
    port = IntProperty(name="Port", description="Renderfarm server port for Puli renderfarm", default=8004)
    # Afantasy render farm only
    cgru_location = StringProperty(name="Cgru Location", description="Cgru directory for Afantasy renderfarm.", default="/opt/cgru", subtype="DIR_PATH")

class ImageEditorPanel(bpy.types.Panel):
    bl_label = "RenderChan"
    bl_space_type = "IMAGE_EDITOR"
    bl_region_type = "UI"
    
    render_options = PointerProperty(type=RenderOptions)
    
    @classmethod
    def poll(self, context):
        return context.edit_image is not None
    
    def draw(self, context):
        draw_render_options(self.layout, context.scene)
        self.layout.operator("image.rc_refresh")

class RenderChanImporter(Operator, ImportHelper):
    bl_idname = "import.renderchan"
    bl_label = "Import with RenderChan"
    
    def draw(self, context):
        draw_render_options(self.layout, context.scene)
    
    def execute(self, context):
        try:
            options = context.scene.renderchan
            command = ["renderchan", self.filepath]
            if options.render_farm != "none":
                command.append("--renderfarm")
                command.append(options.render_farm)
            if options.render_farm == "puli":
                command.append("--host")
                command.append(options.host)
                command.append("--port")
                command.append(options.port)
            elif options.render_farm == "afantasy":
                command.append("--cgru-location")
                command.append(options.cgru_location)
            subprocess.check_call(command)
            
            # Can't use this until RenderChan adds this feature
            # This operation relies on too much code to just copy it over from RenderChan's source
            #output_file = subprocess.check_output(["renderchan", "--dry-run", "--no-deps", self.filepath])
            # For the moment we can use this naive substitute that assumes the structure and format
            output_file = os.path.join(os.path.dirname(self.filepath), "render", os.path.basename(self.filepath) + ".png")
        except subprocess.CalledProcessError as e:
            self.report({"ERROR"}, "RenderChan encountered an error")
            return {"FINISHED"}
        bpy.ops.image.open(filepath=output_file)
        return {"FINISHED"}

class RenderChanSequenceAdd(Operator, ImportHelper):
    bl_idname = "sequencer.renderchan"
    bl_label = "Add with RenderChan"

    def draw(self, context):
        draw_render_options(self.layout, context.scene)
    
    def execute(self, context):
        try:
            options = context.scene.renderchan
            command = ["renderchan", self.filepath]
            if options.render_farm != "none":
                command.append("--renderfarm")
                command.append(options.render_farm)
            if options.render_farm == "puli":
                command.append("--host")
                command.append(options.host)
                command.append("--port")
                command.append(options.port)
            elif options.render_farm == "afantasy":
                command.append("--cgru-location")
                command.append(options.cgru_location)
            subprocess.check_call(command)
            
            # Can't use this until RenderChan adds this feature
            # This operation relies on too much code to just copy it over from RenderChan's source
            #output_file = subprocess.check_output(["renderchan", "--dry-run", "--no-deps", self.filepath])
            # For the moment we can use this naive substitute that assumes the structure and format
            output_file = os.path.join(os.path.dirname(self.filepath), "render", os.path.basename(self.filepath) + ".png")
        except subprocess.CalledProcessError as e:
            self.report({"ERROR"}, "RenderChan encountered an error")
            return {"FINISHED"}
        bpy.ops.sequencer.image_strip_add(directory=os.path.dirname(output_file), file=os.path.basename(self.filepath))
        return {"FINISHED"}

@persistent
def load_handler(something):
    #bpy.data.filepath
    # Can't use this until RenderChan adds this feature
    # This operation relies on too much code to just copy it over from RenderChan's source
    #file_to_update = subprocess.check_output(["renderchan", "--dry-run", "--deps", self.filepath])
    # For the moment we just assume that there are no updates
    file_to_update = ""
    file_to_update = file_to_update.strip()
    if file_to_update != "":
        bpy.ops.object.rc_load_dialog('INVOKE_DEFAULT')
        # Can't use this until RenderChan adds this feature
        # This operation relies on too much code to just copy it over from RenderChan's source
        #output_file = subprocess.check_output(["renderchan", "--dry-run", "--no-deps", self.filepath])
        # For the moment we can use this naive substitute that assumes the structure and format
        #output_file = os.path.join(os.path.dirname(self.filepath), "render", os.path.basename(self.filepath) + ".png")

def register():
    bpy.utils.register_class(RenderOptions)
    bpy.types.Scene.renderchan = PointerProperty(type=RenderOptions, name="RenderChan", description="Options for rendering with RenderChan")
    bpy.utils.register_class(RenderChanImporter)
    bpy.utils.register_class(RenderChanSequenceAdd)
    bpy.utils.register_class(LoadDialog)
    bpy.utils.register_class(RCRefreshImage)
    bpy.utils.register_class(ImageEditorPanel)
    bpy.types.INFO_MT_file_import.append(add_import_button)
    bpy.types.SEQUENCER_MT_add.append(add_add_button)
    bpy.app.handlers.load_post.append(load_handler)

def unregister():
    del bpy.types.Scene.renderchan
    bpy.utils.unregister_class(RenderOptions)
    bpy.utils.unregister_class(RenderChanImporter)
    bpy.utils.unregister_class(RenderChanSequenceAdd)
    bpy.utils.unregister_class(LoadDialog)
    bpy.utils.unregister_class(RCRefreshImage)
    bpy.utils.unregister_class(ImageEditorPanel)
    bpy.types.INFO_MT_mesh_add.remove(add_import_button)
    bpy.types.SEQUENCER_MT_add.remove(add_add_button)
    bpy.app.handlers.load_post.remove(load_handler)

if __name__ == "__main__":
    register()