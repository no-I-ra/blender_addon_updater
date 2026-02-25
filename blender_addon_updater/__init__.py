'''
Copyright (C) 2026 Studio Noira
studionoira@gmail.com

Created by Studio Noira

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
    "author": "Studio Noira",
    "version": (2, 0),
    "blender": (4, 4, 0),
    "location": "View3D > Sidebar > Addon updater",
    "description": (
        "Automatically updates an in-dev addon: creates the zip, uninstalls, installs, enables."
    ),
    "warning": "",
    "doc_url": "",
    "category": "Studio Noira",
}

import bpy
import os
import zipfile
from bpy.types import Operator, Panel, PropertyGroup
from bpy.props import PointerProperty, BoolProperty, StringProperty

# --------------------------------------------------
# FUNCTIONS
# --------------------------------------------------
# region functions
def relative_to_absolute_path(relative_path):
    absolute_path = bpy.path.abspath(relative_path)
    normalized_path = os.path.normpath(absolute_path)
    return r"{}".format(normalized_path.replace("\\", "/"))
    


def create_addon_zip(folder_path, zip_path):
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        base_folder = os.path.basename(folder_path)
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, folder_path)
                zipf.write(file_path, os.path.join(base_folder, rel_path))

        
def safe_disable_addon(addon_name):
    try:
        bpy.ops.preferences.addon_disable(module=addon_name)
    except Exception:
        print(f"Failed to disable the addon '{addon_name}'")
        pass


def safe_remove_addon(addon_name):
    try:
        bpy.ops.preferences.addon_remove(module=addon_name)
    except Exception:
        print(f"Failed to remove the addon '{addon_name}'")
        pass



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
        
# endregion



# --------------------------------------------------
# PROPERTIES
# --------------------------------------------------
# region properties

def update_addon_path(self, context):
    path = relative_to_absolute_path(self.str_addon_path)
    if os.path.isdir(path):
        name = os.path.basename(path)
        self.str_addon_name = name
        self.str_addon_zip_path = os.path.join(
            os.path.dirname(path),
            name + ".zip"
        )


def update_zip_path(self, context):
    path = relative_to_absolute_path(self.str_addon_zip_path)
    if path.lower().endswith(".zip"):
        self.str_addon_name = os.path.splitext(os.path.basename(path))[0]



class ADDONUPDATER_PG_properties(PropertyGroup):

    bool_update_zip: BoolProperty(
        name="Update ZIP",
        default=False
    )

    str_addon_path: StringProperty(
        name="Addon Folder",
        subtype='DIR_PATH',
        update=update_addon_path
    )

    str_addon_zip_path: StringProperty(
        name="Addon ZIP",
        subtype='FILE_PATH',
        update=update_zip_path
    )

    str_addon_name: StringProperty(
        name="Addon Name"
    )

 # endregion


       
# --------------------------------------------------
# OPERATORS
# --------------------------------------------------
# region operators
class ADDONUPDATER_OT_update(Operator):
    bl_idname = "addonupdater.update"
    bl_label = "Update Addon"
    bl_description = "Creates or Load an addon .zip file and install it"

    def execute(self, context):

        props = context.scene.addon_updater
        props.str_addon_path

        addon_name = props.str_addon_name
        addon_folder = relative_to_absolute_path(props.str_addon_path)
        addon_zip = relative_to_absolute_path(props.str_addon_zip_path)

        # Create ZIP if requested
        if props.bool_update_zip:

            if not os.path.isdir(addon_folder):
                self.report({'ERROR'}, "Addon folder path is invalid")
                return {'CANCELLED'}

            os.makedirs(os.path.dirname(addon_zip), exist_ok=True)

            if os.path.exists(addon_zip):
                os.remove(addon_zip)

            create_addon_zip(addon_folder, addon_zip)

        else:
            if not os.path.exists(addon_zip):
                self.report({'ERROR'}, "Addon zip file not found")
                return {'CANCELLED'}

        # Disable & remove old addon
        safe_disable_addon(addon_name)
        safe_remove_addon(addon_name)

        # Install new addon
        bpy.ops.preferences.addon_install(
            overwrite=True,
            filepath=addon_zip
        )

        # Enable addon
        bpy.ops.preferences.addon_enable(module=addon_name)

        self.report({'INFO'}, f"Addon '{addon_name}' updated successfully")
        return {'FINISHED'}

# endregion



# --------------------------------------------------
# PANEL
# --------------------------------------------------
# region panel

class ADDONUPDATER_PT_main(Panel):
    bl_idname = "ADDONUPDATER_PT_main"
    bl_label = "Addon Updater"    
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Studio Noira"

    def draw(self, context):
        layout = self.layout
        props = context.scene.addon_updater
        props.str_addon_path

        layout.prop(props, "bool_update_zip")

        if props.bool_update_zip:
            layout.prop(props, "str_addon_path")
            row = layout.row()
            row.enabled = False
            row.prop(props, "str_addon_zip_path")
        else:
            layout.prop(props, "str_addon_zip_path")

        row = layout.row()
        row.enabled = False
        row.prop(props, "str_addon_name")

        layout.operator("addonupdater.update", icon='FILE_REFRESH')

# endregion



# --------------------------------------------------
# REGISTER
# --------------------------------------------------
# region register

classes = (
    ADDONUPDATER_PG_properties,
    ADDONUPDATER_OT_update,
    ADDONUPDATER_PT_main,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.addon_updater = PointerProperty(type=ADDONUPDATER_PG_properties)


def unregister():

    if hasattr(bpy.types.Scene, "addon_updater"):
        del bpy.types.Scene.addon_updater

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    
   


if __name__ == "__main__":
    register()

# endregion