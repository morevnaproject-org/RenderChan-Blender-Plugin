import importlib
import bpy
import renderchan_importer
importlib.reload(renderchan_importer)
from renderchan_importer import *
from bpy.app.handlers import persistent

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

def add_import_button(self, context):
    self.layout.operator(RenderChanImporter.bl_idname, text="RenderChan Dependency")

def add_add_button(self, context):
    self.layout.operator_context = "INVOKE_REGION_WIN"
    self.layout.operator(RenderChanSequenceAdd.bl_idname, text="RenderChan Dependency")

class LoadDialog(bpy.types.Operator):
    bl_idname = "object.rc_load_dialog"
    bl_label = "RenderChan"
 
    should_update = BoolProperty(name="Update?", description="Should dependencies be updated?")
    
    def draw(self, context):
        self.layout.label("Modified dependencies detected.")
        self.layout.prop(self, "should_update")
 
    def execute(self, context):
        if self.should_update:
            try:
                subprocess.check_call(["renderchan", "--deps", context.blend_data.filepath])
            except subprocess.CalledProcessError as e:
                self.report({"ERROR"}, "RenderChan encountered an error")
        return {'FINISHED'}
 
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

class RCRefreshImage(bpy.types.Operator):
    bl_idname = "image.rc_refresh"
    bl_label = "Rerender"
    
    def execute(self, context):
        try:
            print("Refresh from " + context.edit_image.filepath_from_user())
            subprocess.check_call(["renderchan", context.edit_image.filepath_from_user()])
        except subprocess.CalledProcessError as e:
            self.report({"ERROR"}, "RenderChan encountered an error")
        bpy.ops.image.reload()
        return {"FINISHED"}

class ImageEditorPanel(bpy.types.Panel):
    bl_label = "RenderChan"
    bl_space_type = "IMAGE_EDITOR"
    bl_region_type = "UI"
    
    @classmethod
    def poll(self, context):
        return context.edit_image is not None
    
    def draw(self, context):
        self.layout.row().operator("image.rc_refresh")

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
    bpy.utils.register_class(RenderChanImporter)
    bpy.utils.register_class(RenderChanSequenceAdd)
    bpy.utils.register_class(LoadDialog)
    bpy.utils.register_class(RCRefreshImage)
    bpy.utils.register_class(ImageEditorPanel)
    bpy.types.INFO_MT_file_import.append(add_import_button)
    bpy.types.SEQUENCER_MT_add.append(add_add_button)
    bpy.app.handlers.load_post.append(load_handler)

def unregister():
    bpy.utils.unregister_class(RenderChanImporter)
    bpy.utils.unregister_class(RenderChanSequenceAdd)
    bpy.utils.unregister_class(LoadDialog)
    bpy.utils.unregister_class(RCRefreshImage)
    bpy.utils.unregister_class(ImageEditorPanel)
    bpy.types.INFO_MT_mesh_add.remove(add_import_button)
    bpy.types.SEQUENCER_MT_add.remove(add_add_button)

if __name__ == "__main__":
    register()