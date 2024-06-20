# In development Blender addon updater for Blender 4.x

Add-on for Blender that automatically updates an addon in development.

## Features

Some addons are not properly updated without fully installing them again (addon with preferences for example).
This addon allows you to update an addon without needing to manually uninstall, install and activate it each time you edit its scripts.

`It assumes the addon name is the same as the .zip and addon folder`

The features are:
* Update an addon from its main folder (with scripts under it).
* Update an addon from a .zip file.

## Installing

### Manual Method  
* Download the last release zip file.
* Save the zip somewhere where you can find it again.
* Extract the zip.
* Copy the folder `blender_addon_updater`. Make sure this is the folder with the scripts under it (`blender_custom_addon\__init__.py` etc).
* Paste the `blender_addon_updater` folder into your Blender addons folder. Default path:
```
%APPDATA%\Blender Foundation\Blender\4.0\scripts\addons
```
### Blender Method

* Download the last release zip file.
* Save the zip somewhere where you can find it again.
* In Blender, navigate to Edit -> Preferences -> Add-ons
* Click on `Install...`
* Browse to the zip, select it and click on `Install Add-on`
* In the addon list, search for `Addon Updater`
* Check it to enable the addon. This will add the panel `Addon Updater` to the right of the 3D View

* For more information, please refer to Blender's guide for installing addons here: [Install from File](https://docs.blender.org/manual/en/latest/editors/preferences/addons.html).

## How to use the addon

### Update an addon from its main folder
* In the addon panel, check `Update zip`.
* Click on the button next to`Addon path` and select the addon to update folder with scripts under it.
* Click on `Update addon`: this creates a zip from your addon folder and automatically uninstalls, installs and activates it.

### Update an addon from a zip
* In the addon panel, uncheck `Update zip`.
* Click on the button next to`Addon .zip` and select the addon to update zip file (the .zip should contain a folder with scripts under it).
* Click on `Update addon`: this automatically uninstalls, installs and activates your addon.







