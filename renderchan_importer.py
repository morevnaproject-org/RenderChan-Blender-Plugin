import bpy
from bpy.types import Operator
from bpy_extras.io_utils import ImportHelper
import subprocess
import os.path
from bpy.props import *

class RenderChanImporter(Operator, ImportHelper):
    bl_idname = "import.renderchan"
    bl_label = "Import with RenderChan"
    
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
    
    def draw(self, context):
        self.layout.prop(self, "profile")
        self.layout.prop(self, "stereo")
        self.layout.prop(self, "render_farm")
        
        if self.render_farm == "puli":
            self.layout.prop(self, "host")
            self.layout.prop(self, "port")
        elif self.render_farm == "afantasy":
            self.layout.prop(self, "cgru_location")
    
    def execute(self, context):
        try:
            subprocess.check_call(["renderchan", self.filepath]);
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
    bl_idname = "testar.renderchan"
    bl_label = "Add with RenderChan"
    
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
    
    def draw(self, context):
        self.layout.prop(self, "profile")
        self.layout.prop(self, "stereo")
        self.layout.prop(self, "render_farm")
        
        if self.render_farm == "puli":
            self.layout.prop(self, "host")
            self.layout.prop(self, "port")
        elif self.render_farm == "afantasy":
            self.layout.prop(self, "cgru_location")
    
    def invoke(self, context, event): # See comments at end  [1]        
        context.window_manager.fileselect_add(self)
        #Open browser, take reference to 'self' read the path to selected 
        #file, put path in predetermined data structure self.filepath
        return {'RUNNING_MODAL'}
    
    def execute(self, context):
        try:
            subprocess.check_call(["renderchan", self.filepath]);
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