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
    "version": (2, 2),
    "blender": (4, 0, 0),
    "description": "Safely update an in-dev addon: create zip, reinstall, enable",
    "category": "Development",
}

import bpy
import os
import zipfile
from bpy.types import Operator, Panel


# --------------------------------------------------
# Utility Functions
# --------------------------------------------------

def normalize_path(path):
    return os.path.normpath(bpy.path.abspath(path))


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
        pass


def safe_remove_addon(addon_name):
    try:
        bpy.ops.preferences.addon_remove(module=addon_name)
    except Exception:
        pass


# --------------------------------------------------
# Operator
# --------------------------------------------------

class OBJECT_OT_noira_update_addon(Operator):
    bl_idname = "object.noira_update_addon"
    bl_label = "Update Addon"
    bl_description = "Create zip, reinstall and enable addon safely"

    def execute(self, context):

        scene = context.scene
        addon_name = scene.str_addon_name
        addon_folder = normalize_path(scene.str_addon_path)
        addon_zip = normalize_path(scene.str_addon_zip_path)

        # -----------------------------
        # 1️⃣ Create ZIP if requested
        # -----------------------------
        if scene.bool_update_zip:

            if not os.path.isdir(addon_folder):
                self.report({'ERROR'}, "Addon folder path is invalid")
                return {'CANCELLED'}

            # Ensure the destination folder exists
            os.makedirs(os.path.dirname(addon_zip), exist_ok=True)

            # Remove old ZIP if exists
            if os.path.exists(addon_zip):
                os.remove(addon_zip)

            create_addon_zip(addon_folder, addon_zip)

        # -----------------------------
        # 2️⃣ ZIP must exist if not updated
        # -----------------------------
        else:
            if not os.path.exists(addon_zip):
                self.report({'ERROR'}, "Addon zip file not found")
                return {'CANCELLED'}

        # -----------------------------
        # 3️⃣ Disable & remove old addon
        # -----------------------------
        safe_disable_addon(addon_name)
        safe_remove_addon(addon_name)

        # -----------------------------
        # 4️⃣ Install new addon
        # -----------------------------
        bpy.ops.preferences.addon_install(
            overwrite=True,
            filepath=addon_zip
        )

        # -----------------------------
        # 5️⃣ Enable addon
        # -----------------------------
        bpy.ops.preferences.addon_enable(module=addon_name)

        self.report({'INFO'}, f"Addon '{addon_name}' updated successfully")
        return {'FINISHED'}


# --------------------------------------------------
# UI Panel
# --------------------------------------------------

class VIEW3D_PT_noira_addon_updater(Panel):
    bl_label = "Addon Updater"
    bl_idname = "VIEW3D_PT_noira_addon_updater"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Addon Updater"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.prop(scene, "bool_update_zip")

        if scene.bool_update_zip:
            layout.prop(scene, "str_addon_path")
            row = layout.row()
            row.enabled = False
            row.prop(scene, "str_addon_zip_path")
        else:
            layout.prop(scene, "str_addon_zip_path")

        row = layout.row()
        row.enabled = False
        row.prop(scene, "str_addon_name")

        layout.operator("object.noira_update_addon", icon='FILE_REFRESH')


# --------------------------------------------------
# Property Updates
# --------------------------------------------------

def update_addon_path(self, context):
    path = normalize_path(self.str_addon_path)
    if os.path.isdir(path):
        name = os.path.basename(path)
        self.str_addon_name = name
        self.str_addon_zip_path = os.path.join(
            os.path.dirname(path),
            name + ".zip"
        )


def update_zip_path(self, context):
    path = normalize_path(self.str_addon_zip_path)
    if path.lower().endswith(".zip"):
        self.str_addon_name = os.path.splitext(os.path.basename(path))[0]


# --------------------------------------------------
# Registration
# --------------------------------------------------

classes = (
    OBJECT_OT_noira_update_addon,
    VIEW3D_PT_noira_addon_updater,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.bool_update_zip = bpy.props.BoolProperty(
        name="Update ZIP",
        default=False
    )

    bpy.types.Scene.str_addon_path = bpy.props.StringProperty(
        name="Addon Folder",
        subtype='DIR_PATH',
        update=update_addon_path
    )

    bpy.types.Scene.str_addon_zip_path = bpy.props.StringProperty(
        name="Addon ZIP",
        subtype='FILE_PATH',
        update=update_zip_path
    )

    bpy.types.Scene.str_addon_name = bpy.props.StringProperty(
        name="Addon Name"
    )


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.bool_update_zip
    del bpy.types.Scene.str_addon_path
    del bpy.types.Scene.str_addon_zip_path
    del bpy.types.Scene.str_addon_name


if __name__ == "__main__":
    register()
