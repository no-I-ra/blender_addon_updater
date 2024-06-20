'''
Copyright (C) 2024 NoiraFayn
noirafaynmodding@gmail.com

Created by NoiraFayn

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''


bl_info = {
    "name": "Addon Updater",
    "author": "NoiraFayn",
    "version": (1, 1),
    "blender": (4, 0, 0),
    "location": "",
    "description": (
        "Automatically updates an in-dev addon: creates the zip, uninstalls, installs, enables."
    ),
    "warning": "",
    "doc_url": "",
    "category": "3D View",
}


import bpy
from bpy.types import Operator, Panel, Menu
import os
import zipfile
import threading


# -- FUNCTIONS -----

def relative_to_absolute_path(relative_path):
    absolute_path = bpy.path.abspath(relative_path)
    normalized_path = os.path.normpath(absolute_path)
    return r"{}".format(normalized_path.replace("\\", "/"))
    
    
def delete_file(file_path):
    try:
        os.remove(file_path)
    except OSError as e:
        print(f"Error: {e.filename} - {e.strerror}")
        
def create_addon_zip(folder_path, zip_path):
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, folder_path)
                zipf.write(file_path, os.path.join(os.path.basename(folder_path), relative_path))

def install_addon(addon_name, addon_filepath):
    print("addon_filepath = " + addon_filepath)
    if os.path.exists(addon_filepath):

        addon_folder_path = bpy.utils.user_resource('SCRIPTS', path="addons")
        addon_dir_path = os.path.join(addon_folder_path, addon_name)
        
        if os.path.exists(addon_dir_path) and os.path.isdir(addon_dir_path):
            bpy.ops.preferences.addon_install(overwrite=True, target='DEFAULT', filepath=addon_filepath, filter_folder=True, filter_python=True, filter_glob='*.zip')
        else:

            if not os.path.exists(addon_folder_path):
                os.makedirs(addon_folder_path)
            
            with zipfile.ZipFile(addon_filepath, 'r') as zip_ref:
                zip_ref.extractall(addon_folder_path)

            bpy.ops.preferences.addon_install(overwrite=True, target='DEFAULT', filepath=addon_filepath, filter_folder=True, filter_python=True, filter_glob='*.zip')
            
        print(f"Addon '{addon_name}' installed and enabled successfully.")
    else:
        print(f"Addon file '{addon_filepath}' does not exist.")
    
def enable_addon(addon_name):
    bpy.ops.preferences.addon_enable(module=addon_name)

def remove_addon(addon_name):
    bpy.ops.preferences.addon_remove(module=addon_name)
    
def refresh_addons():
    bpy.ops.preferences.addon_refresh()
    
def update_addon_name(self, context):
    file_path = context.scene.str_addon_zip_path
    if file_path:
        file_name_without_extension = os.path.splitext(os.path.basename(file_path))[0]
        self.str_addon_name = file_name_without_extension
        
def update_addon_zip_and_name(self, context):

    addon_path = relative_to_absolute_path(self.str_addon_path)
    self.str_addon_path = addon_path
    
    if addon_path:
        parent_dir = os.path.dirname(addon_path)
        folder_name = os.path.basename(addon_path)
        self.str_addon_name = folder_name
        zip_file_name = (folder_name + ".zip")

        addon_zip_path = os.path.join(parent_dir, zip_file_name)
        
        self.str_addon_zip_path = relative_to_absolute_path(addon_zip_path)


# -- OPERATORS -----
class OBJECT_OT_Noira_UpdateAddon(bpy.types.Operator):
    bl_idname = "object.update_addon"
    bl_label = "OBJECT_OT_Noira_UpdateAddon"
    bl_description = "Creates or Load an addon .zip file and install it"
     
    def execute(self, context):

        addon_name = bpy.context.scene.str_addon_name        

        normalized_addon_path = os.path.normpath(bpy.context.scene.str_addon_path)
        addon_path = r"{}".format(normalized_addon_path.replace("\\", "/"))  

        normalized_addon_zip_path = os.path.normpath(bpy.context.scene.str_addon_zip_path)
        addon_zip_path = r"{}".format(normalized_addon_zip_path.replace("\\", "/"))
        
        if bpy.context.scene.bool_update_zip:
            if addon_zip_path:
            
                if os.path.exists(addon_zip_path):
                    thread = threading.Thread(target=delete_file(addon_zip_path))
                    thread.start()
                    thread.join()
                
                thread = threading.Thread(target=create_addon_zip(addon_path,addon_zip_path))
                thread.start()
                thread.join()
        
        thread = threading.Thread(target=remove_addon(addon_name))
        thread.start()
        thread.join()

        thread = threading.Thread(target=install_addon(addon_name,addon_zip_path))
        thread.start()
        thread.join()
        
        thread = threading.Thread(target=enable_addon(addon_name))
        thread.start()
        thread.join()

        return {'FINISHED'}

# -- PANELS -----
class PANEL_PT_Noira_AddonUpdater(Panel):
    bl_idname = "PANEL_PT_Noira_AddonUpdater"
    bl_label = "Addon Updater"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Addon Updater"

    def draw(self, context):
        layout = self.layout
    
        row = layout.row()        
        row.prop(context.scene, "bool_update_zip", text="Update zip")
        
        if context.scene.bool_update_zip:
            row = layout.row()
            row.prop(context.scene, "str_addon_path", text="Addon path")
            row = layout.row()
            row.prop(context.scene, "str_addon_zip_path", text="Addon .zip")
            row.enabled = False
        else:
            row = layout.row()
            row.prop(context.scene, "str_addon_zip_path", text="Addon .zip")
            row.enabled = True
            
        row = layout.row()
        row.prop(context.scene, "str_addon_name")
        row.enabled = False
        
        row = layout.row()
        row.operator("object.update_addon", text="Update addon")
        

# -- REGISTER -----

classes = (
    OBJECT_OT_Noira_UpdateAddon,
    PANEL_PT_Noira_AddonUpdater
)
  
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    
    bpy.types.Scene.str_addon_name = bpy.props.StringProperty \
      (
        name = "Addon name",
        description = "Name of the addon",
        default = ""
      )
    bpy.types.Scene.bool_update_zip = bpy.props.BoolProperty \
      (
        name = "Update .zip",
        description = "Updates the addon .zip file before installing it.",
        default = False
      )
    bpy.types.Scene.str_addon_zip_path = bpy.props.StringProperty \
      (
        name="Folder Path",
        description="Path to the addon .zip",
        default="",
        subtype='FILE_PATH',
        update = update_addon_name
      )
    bpy.types.Scene.str_addon_path = bpy.props.StringProperty \
      (
        name="Folder Path",
        description="Path to the folder to zip",
        default="",
        subtype='DIR_PATH',
        update = update_addon_zip_and_name
      )

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.str_addon_name
    del bpy.types.Scene.bool_update_zip
    del bpy.types.Scene.str_addon_zip_path
    

if __name__ == "__main__":    
    register()