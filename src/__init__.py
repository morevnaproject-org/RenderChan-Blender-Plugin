import bpy
from bpy.app.handlers import persistent
from bpy.types import Operator
from bpy_extras.io_utils import ImportHelper
import subprocess
import os.path
from bpy.props import *
from shutil import which
import sys
# Add blender to PATH if its not already on there
if not which("blender"):
    os.environ["PATH"] += os.pathsep + os.path.dirname(bpy.app.binary_path)
# Use renderchan on path if it exists, fallback on packaged version
renderchan_exec_path = which("renderchan")
if renderchan_exec_path:
    module_path = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(renderchan_exec_path))))
    if os.path.exists(os.path.join(module_path, 'renderchan', '__init__.py')):
        sys.path.append(module_path)
    else:
        sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "RenderChan"))
else:
    sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "RenderChan"))

import renderchan
from renderchan.core import RenderChan
import importlib
importlib.reload(renderchan)

bl_info = {
    "name": "Import with RenderChan",
    "author": "scribblemaniac",
    "version": (0, 1),
    "blender": (2, 76, 0),
    "location": "File > Import > RenderChan Dependency",
    "description": "Imports various file types and renders them with RenderChan so they can be imported into Blender.",
    "warning": "This requires RenderChan, and may require other binaries depending on the file being rendered",
    "category": "Import-Export"
}

def reinit_renderchan():
    rcl.main = RenderChan()
    rcl.main.datadir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "RenderChan", "templates")
    if bpy.context.scene.renderchan.profile != "default":
        rcl.main.setProfile(bpy.context.scene.renderchan.profile)
    if bpy.context.scene.renderchan.render_farm != "none":
        rcl.main.renderfarm_engine = bpy.context.scene.renderchan.render_farm
    if bpy.context.scene.renderchan.render_farm == "afanasy" and bpy.context.scene.renderchan.cgru_location:
        rcl.main.cgru_location = bpy.context.scene.renderchan.cgru_location
    

def refresh_everything():
    bpy.ops.sequencer.refresh_all()
    # TODO refresh images

def draw_render_options(layout, scene):
    layout.prop(scene.renderchan, "profile")
    layout.prop(scene.renderchan, "stereo")
    layout.prop(scene.renderchan, "render_farm")
    
    if scene.renderchan.render_farm == "afanasy":
        layout.prop(scene.renderchan, "cgru_location")

def add_import_button(self, context):
    self.layout.operator(RenderChanImporter.bl_idname, text="RenderChan Dependency")

def add_add_button(self, context):
    self.layout.operator_context = "INVOKE_REGION_WIN"
    self.layout.operator(RenderChanSequenceAdd.bl_idname, text="RenderChan Dependency")

def render_file(file, scene, dependenciesOnly):
    global rcl
    if scene.renderchan.profile != "default":
        rcl.main.setProfile(scene.renderchan.profile)
    if scene.renderchan.render_farm != "none":
        rcl.main.renderfarm_engine = scene.renderchan.render_farm
    if scene.renderchan.render_farm == "afanasy" and scene.renderchan.cgru_location:
        rcl.main.cgru_location = scene.renderchan.cgru_location
    if scene.renderchan.stereo == "none":
        stereo = None
    else:
        stereo = scene.renderchan.stereo
    rcl.main.submit(file, dependenciesOnly, False, stereo)
    
    # Temporary fix
    reinit_renderchan()
    
    refresh_everything()

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
        self.layout.label("Afanasy Options")
        self.layout.prop(context.scene.renderchan, "cgru_location") 
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
 
    def execute(self, context):
        if self.should_update:
            global rcl
            render_file(rcl.blend, context.scene, True)
        return {'FINISHED'}

class RCRefreshImage(bpy.types.Operator):
    bl_idname = "image.rc_refresh"
    bl_label = "Rerender"
    
    def execute(self, context):
        from renderchan.file import RenderChanFile
        global rcl
        file = RenderChanFile(bpy.path.abspath(context.edit_image.filepath), rcl.main.modules, rcl.main.projects)
        print(file.getPath())
        render_file(file, context.scene, False)
        return {"FINISHED"}

def profile_items(scene, context):
    from renderchan.utils import ini_wrapper
    import configparser
    global rcl
    
    config = configparser.ConfigParser()
    config.read_file(ini_wrapper(os.path.join(rcl.blend.projectPath, "project.conf")))
    rcl.items = [("default", "Default", "The default profile")]
    for section in config.sections():
        if section != "default":
            rcl.items.append((section, section, ""))
    return rcl.items

class RenderOptions(bpy.types.PropertyGroup):
    profile = EnumProperty(items=profile_items, name="Profile", description="What profile RenderChan should use. Leave blank to use the project's default.")
    stereo = EnumProperty(items=[("none", "None", "Do not render with stereo-3D."), ("v", "Vertical", "Vertical stereo-3D"), ("h", "Horizontal", "Horizontal stereo-3D"), \
        ("l", "Left", "Left stereo image"), ("r", "Right", "Right stereo image")], name="Stereo", description="The type of stereoscopic 3D rendering to use.", default="none")
    render_farm = EnumProperty(items=[("none", "None", "Do not use a render farm"), ("afanasy", "Afanasy render farm", "Use Afanasy render farm")], \
        name="Render farm", description="Determines what render farm, if any, to use.", default="none")
    # Afanasy render farm only
    cgru_location = StringProperty(name="Cgru Location", description="Cgru directory for Afanasy renderfarm.", default="/opt/cgru", subtype="DIR_PATH")
    
    #def __init__(self):
        

class ImageEditorPanel(bpy.types.Panel):
    bl_label = "RenderChan"
    bl_space_type = "IMAGE_EDITOR"
    bl_region_type = "UI"
    
    render_options = PointerProperty(type=RenderOptions)
    
    @classmethod
    def poll(self, context):
        global rcl
        if not rcl.is_project or context.edit_image is None:
            return False
        
        from renderchan.file import RenderChanFile
        
        path = bpy.path.abspath(context.edit_image.filepath)
        file = RenderChanFile(path, rcl.main.modules, rcl.main.projects)
        return file.project != None and file.module and file.getRenderPath() == path
    
    def draw(self, context):
        draw_render_options(self.layout, context.scene)
        self.layout.operator("image.rc_refresh")

class RenderChanImporter(Operator, ImportHelper):
    bl_idname = "import.renderchan"
    bl_label = "Import with RenderChan"
    
    def draw(self, context):
        draw_render_options(self.layout, context.scene)
    
    def execute(self, context):
        """
        try:
            options = context.scene.renderchan
            command = ["renderchan", self.filepath]
            if options.render_farm != "none":
                command.append("--renderfarm")
                command.append(options.render_farm)
            if options.render_farm == "afanasy":
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
        """
        return {"FINISHED"}

class RenderChanSequenceAdd(Operator, ImportHelper):
    bl_idname = "sequencer.renderchan"
    bl_label = "Add with RenderChan"

    def draw(self, context):
        draw_render_options(self.layout, context.scene)
    
    def execute(self, context):
        #bpy.ops.sequencer.image_strip_add(directory="", files=["FirstAnim.0000.png", "FirstAnim.0001.png", "FirstAnim.0002.png"])
        return {"FINISHED"}

@persistent
def load_handler(something):
    from renderchan.file import RenderChanFile
    
    global rcl
    rcl.blend = RenderChanFile(bpy.data.filepath, rcl.main.modules, rcl.main.projects)
    rcl.is_project = rcl.blend.project != None
    if not rcl.is_project:
        return
    
    deps = rcl.main.parseDirectDependency(rcl.blend, False, False)
    # Temporary fix
    reinit_renderchan()
    if deps[1]:
        bpy.ops.object.rc_load_dialog('INVOKE_DEFAULT')

class RenderChanLibrary():
    def __init__(self):
        from renderchan.file import RenderChanFile
        
        self.main = RenderChan()
        self.main.datadir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates")
        self.is_project = False
        self.items = []

def register():
    # DO NOT REMOVE THIS LINE!! Without it, the plugin becomes a fork bomb.
    if bpy.app.background:
        return
    
    global rcl
    rcl = RenderChanLibrary()
    
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
    if bpy.app.background:
        return
    
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