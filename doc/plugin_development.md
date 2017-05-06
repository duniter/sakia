# Developing a plugin for sakia

## Prepare dev environment

Follow the doc file [Install for developers](https://github.com/duniter/sakia/doc/install_for_developers.md).
You can use the same pyenv environment to develop your plugin.

## Plugin structure

The plugin source code should follow the structure below :

```
/
   [plugin_pkg_name]/
      images/                # The directory containing images used in the widget
         images.qrc          # The qt resources .qrc file describing available images
         [image1.png]        # The list of images
         [image2.png]
      __init__.py            # The __init__ file of the plugin
      [script_1.py]          # Some scripts imported in the __init__ file
      [script_2.py]
      [ui_file.ui]           # ui files designed using QtDesigner
```

The `__init__.py` file must set the following global constants :

```python
PLUGIN_NAME = "Title of the plugin"
PLUGIN_DESCRIPTION = "Description of the plugin"
PLUGIN_VERSION = "0.1"
```

The function below must be present in the `__init__.py` file to initialize the plugin on Sakia startup :

```python

def plugin_exec(app, main_window):
    """
    :param sakia.app.Application app:
    :param sakia.gui.main_window.controller.MainWindowController main_window:
    """
    # Place your init code here
    pass
```icons

## Building your plugin

To build the plugin, you need :

### To generate resources (images, qrc, ...)

Generating resources uses [pyrcc5](http://pyqt.sourceforge.net/Docs/PyQt5/resources.html).
To help you generate your resources, you should copy the `gen_resources.py` file from sakia sources and configure the
 variable `gen_resources`. Replace `'src'` by the name of your plugin package.

### To import your resources in your code

The generation of the resources build the following python files :

 - `filename.ui` -> `filename_uic.py`
 - `filename.qrc` -> `filename_rc.py`

The `filename_uic.py` file should be imported in the file using the designed widget. See the
[dialog of the example plugin](https://github.com/Insoleet/sakia-plugin-example/blob/master/plugin_example/main_dialog.py)

The `filename_rc.py` file should be imported in the `__init__.py` file, on the last line. See the
[__init__.py of the example plugin](https://github.com/Insoleet/sakia-plugin-example/blob/master/plugin_example/__init__.py#L28)

### To generate your plugin

To generate your plugin, you must zip everything (generated resources) in a zip file respecting the structure below :

```
[plugin_name].zip\
    [plugin_name]\
        __init__.py
        [generated files...]
```

The [setup.py](https://github.com/Insoleet/sakia-plugin-example/blob/master/setup.py) file from the
example plugin is available to help you generate correctly the plugin.

