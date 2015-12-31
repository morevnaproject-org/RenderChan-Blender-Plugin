import bpy
from bpy.types import Operator
from bpy_extras.io_utils import ImportHelper
import subprocess
import os.path

class RenderChanImporter(Operator, ImportHelper) :
    bl_idname = "import.renderchan"
    bl_label = "Import with RenderChan"
    
    def execute(self, context) :
        try :
            subprocess.check_call(["renderchan", self.filepath]);
            # Can't use this until RenderChan adds this feature
            # This operation relies on too much code to just copy it over from RenderChan's source
            #outputFile = subprocess.check_output(["renderchan", "--dry-run", "--no-deps", self.filepath])
            # For the moment we can use this naive substitute that assumes the structure and format
            outputFile = os.path.join(os.path.dirname(self.filepath), "render", os.path.basename(self.filepath) + ".png")
        except subprocess.CalledProcessError as e:
            self.report({"ERROR","RenderChan encountered an error"})
            return {"FINISHED"}
        bpy.ops.image.open(filepath=outputFile)
        return {"FINISHED"}