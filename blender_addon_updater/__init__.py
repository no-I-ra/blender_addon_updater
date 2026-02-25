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
    "version": (2, 1, 0),
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
import addon_utils
import shutil
import importlib
import sys

# --------------------------------------------------
# FUNCTIONS
# --------------------------------------------------
# region functions
def relative_to_absolute_path(relative_path):
    absolute_path = bpy.path.abspath(relative_path)
    normalized_path = os.path.normpath(absolute_path)
    # return r"{}".format(normalized_path.replace("\\", "/"))
    return os.path.normpath(bpy.path.abspath(relative_path))
    


def create_addon_zip(folder_path, zip_path):
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        base_folder = os.path.basename(folder_path)
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, folder_path)
                zipf.write(file_path, os.path.join(base_folder, rel_path))

 
                
def disable_addon(addon_name):
    try:
        bpy.ops.preferences.addon_disable(module=addon_name)
    except Exception:
        print(f"Failed to disable the addon '{addon_name}'")
        pass



def remove_addon(addon_name):
    try:
        bpy.ops.preferences.addon_remove(module=addon_name)
    except Exception:
        print(f"Failed to remove the addon '{addon_name}'")
        pass



def safe_disable_addon(addon_name, report=None):
    """Disable addon and unregister all its classes if it exists."""

    disabled = False
    try:
        for mod_name, is_enabled in addon_utils.modules():
            if mod_name == addon_name and is_enabled:
                # Disable addon
                addon_utils.disable(mod_name)
                disabled = True
                if report:
                    report({'INFO'}, f"Disabled addon '{addon_name}'")
                
                # Unregister all classes in the addon
                for cls in get_addon_classes(addon_name):
                    try:
                        bpy.utils.unregister_class(cls)
                        if report:
                            report({'INFO'}, f"Unregistered class: {cls.__name__}")
                    except Exception:
                        pass

                return True
        return disabled
    except Exception as e:
        if report:
            report({'WARNING'}, f"Failed to disable/unregister addon '{addon_name}': {e}")
        return False



def safe_remove_addon(addon_name, report=None):
    """Delete addon folder safely after unregistering."""

    try:
        # Use keyword args for Blender 5.x compatibility
        addons_path = bpy.utils.user_resource(resource_type='SCRIPTS', path='addons')
        folder_path = os.path.join(addons_path, addon_name)

        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)
            if report:
                report({'INFO'}, f"Deleted old addon folder: {addon_name}")
            return True
        else:
            if report:
                report({'INFO'}, f"No existing addon folder found: {addon_name}")
            return False

    except Exception as e:
        if report:
            report({'ERROR'}, f"Failed to remove addon folder '{addon_name}': {e}")
        return False
       

def get_addon_folder(addon_name):
    addons_base_path = bpy.utils.user_resource(resource_type='SCRIPTS', path='addons')
    folder_path = os.path.join(addons_base_path, addon_name)
    if os.path.exists(folder_path) and os.path.isdir(folder_path):
        return folder_path
    return None



def get_addon_classes(addon_name):
    """Get already loaded registerable classes from sys.modules."""
    classes = []

    for mod_name, module in sys.modules.items():
        if mod_name.startswith(addon_name):
            for obj in vars(module).values():
                if isinstance(obj, type) and issubclass(obj, (
                    bpy.types.Operator,
                    bpy.types.Panel,
                    bpy.types.PropertyGroup,
                    bpy.types.Menu,
                    bpy.types.Header,
                    bpy.types.UIList
                )) and obj not in (
                    bpy.types.Operator,
                    bpy.types.Panel,
                    bpy.types.PropertyGroup,
                    bpy.types.Menu,
                    bpy.types.Header,
                    bpy.types.UIList
                ):
                    classes.append(obj)

    return classes



# def remove_addon_handlers(addon_name):
#     for handler_list in bpy.app.handlers.__dict__.values():
#         if isinstance(handler_list, list):
#             for handler in list(handler_list):
#                 if hasattr(handler, "__module__"):
#                     root = handler.__module__.partition(".")[0]
#                     if root == addon_name:
#                         handler_list.remove(handler)



# def remove_addon_keymaps(addon_name):
#     wm = bpy.context.window_manager
#     kc = wm.keyconfigs.addon

#     prefix = addon_name.split(".")[0] + "."

#     for km in kc.keymaps:
#         for kmi in list(km.keymap_items):
#             if kmi.idname.startswith(prefix):
#                 km.keymap_items.remove(kmi)

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

    str_debug_class_name: StringProperty(
        name="Class name"
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
    bl_options = {'REGISTER'}

    def execute(self, context):

        props = context.scene.addon_updater
        addon_name = props.str_addon_name

        if not addon_name:
            self.report({'ERROR'}, "Addon name is empty")
            return {'CANCELLED'}

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
            self.report({'INFO'}, f"Addon ZIP created at: {addon_zip}")

        elif not os.path.exists(addon_zip):
            self.report({'ERROR'}, "Addon zip file not found")
            return {'CANCELLED'}

        # Disable & remove old addon, even if the folder path has changed
        addon_folder = get_addon_folder(addon_name)
        if addon_folder:
            safe_disable_addon(addon_name, report=self.report)

            # Unregister all classes detected from that folder
            classes_to_unregister = get_addon_classes(addon_name)
            for cls in classes_to_unregister:
                try:
                    bpy.utils.unregister_class(cls)
                    self.report({'INFO'}, f"Unregistered class: {cls.__name__}")
                except Exception as e:
                    self.report({'WARNING'}, f"Failed to unregister class {cls.__name__}: {e}")

            # Remove folder
            safe_remove_addon(addon_name, report=self.report)

        if addon_name in bpy.context.preferences.addons:
                try:
                    bpy.context.preferences.addons.remove(addon_name)
                except Exception as e:
                    self.report({'WARNING'}, f"Failed to remove addon preferences {addon_name}: {e}")

        
        # Install new addon
        try:
            # ensures Blender fully reloads the updated code.
            for mod_name in list(sys.modules.keys()):
                if mod_name.startswith(addon_name):
                    sys.modules.pop(mod_name)

            bpy.ops.preferences.addon_install(
                overwrite=True,
                filepath=addon_zip
            )
        except Exception as e:
            self.report({'ERROR'}, f"Failed to install addon from ZIP: {e}")
            return {'CANCELLED'}


        # Enable addon
        try:
            bpy.ops.preferences.addon_enable(module=addon_name)
        except Exception as e:
            self.report({'ERROR'}, f"Failed to enable addon '{addon_name}': {e}")
            return {'CANCELLED'}

        context.preferences.use_preferences_save = True
        bpy.ops.wm.save_userpref()

        self.report({'INFO'}, f"Addon '{addon_name}' updated successfully")
        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        return context.scene.addon_updater is not None


class ADDONUPDATER_OT_uninstall(Operator):
    bl_idname = "addonupdater.uninstall"
    bl_label = "Uninstall Addon"
    bl_description = "Uninstall the add, including unregister classes and delete the addon folder in Blender"
    bl_options = {'REGISTER'}

    def execute(self, context):

        props = context.scene.addon_updater
        addon_name = props.str_addon_name

        if not addon_name:
            self.report({'ERROR'}, "Addon name is empty")
            return {'CANCELLED'}

        addon_folder = relative_to_absolute_path(props.str_addon_path)
        addon_zip = relative_to_absolute_path(props.str_addon_zip_path)

        disable_addon(addon_name)
        remove_addon(addon_name)

        # Disable & remove old addon, even if the folder path has changed
        addon_folder = get_addon_folder(addon_name)
        if addon_folder:
            safe_disable_addon(addon_name, report=self.report)

            # # Remove addon handlers and keymaps
            # remove_addon_handlers(addon_name)
            # remove_addon_keymaps(addon_name)

            # Unregister all classes detected from that folder
            classes_to_unregister = get_addon_classes(addon_name)
            for cls in classes_to_unregister:
                try:
                    bpy.utils.unregister_class(cls)
                    self.report({'INFO'}, f"Unregistered class: {cls.__name__}")
                except Exception as e:
                    self.report({'WARNING'}, f"Failed to unregister class {cls.__name__}: {e}")

            # Remove folder
            safe_remove_addon(addon_name, report=self.report)

        if addon_name in bpy.context.preferences.addons:
                try:
                    bpy.context.preferences.addons.remove(addon_name)
                except Exception as e:
                    self.report({'WARNING'}, f"Failed to remove addon preferences {addon_name}: {e}")


        


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

        layout.separator()
        layout.operator("addonupdater.uninstall", icon='EVENT_DEL')


# endregion



# --------------------------------------------------
# REGISTER
# --------------------------------------------------
# region register

classes = (
    ADDONUPDATER_PG_properties,
    ADDONUPDATER_OT_update,
    ADDONUPDATER_OT_uninstall,
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