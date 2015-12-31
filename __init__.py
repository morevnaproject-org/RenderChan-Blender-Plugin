import importlib
import bpy
import renderchan_importer
importlib.reload(renderchan_importer)
from renderchan_importer import *

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

def register():
    bpy.utils.register_class(RenderChanImporter)
    bpy.types.INFO_MT_file_import.append(add_import_button)
 
def unregister():
    bpy.utils.unregister_class(RenderChanImporter)
    bpy.types.INFO_MT_mesh_add.remove(add_import_button)
 
if __name__ == "__main__":
    register()