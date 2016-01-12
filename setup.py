import sys, os, subprocess, multiprocessing, site
from cx_Freeze import setup, Executable
from PyQt5 import QtCore
from os import listdir
from os.path import isfile, join

#############################################################################
# preparation des options
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

print(sys.path)
print("Environnement:")
print(os.environ)
includes = ["sip", "re", "json", "logging",
            "hashlib", "os", "urllib",
            "ucoinpy", "pylibscrypt", "aiohttp", "asyncio",
            "quamash", "jsonschema"]
exclude = ['.git']
packages = ["libnacl", "encodings"]

includefiles = []
zipincludes = []

if sys.platform == "win32":
    app = QtCore.QCoreApplication(sys.argv)
    libEGL_path = ""
    libsodium_path = ""
    print(QtCore.QCoreApplication.libraryPaths())
    for path in QtCore.QCoreApplication.libraryPaths():
        if os.path.isfile(os.path.join(os.path.dirname(path), "libEGL.dll")):
            libEGL_path = os.path.join(os.path.dirname(path), "libEGL.dll")

    if 'CONDA_DEFAULT_ENV' in os.environ:
            # Check if we are in Conda env
        schemas = os.path.join(site.getsitepackages()[1], "jsonschema", "schemas")

        onlyfiles = [ f for f in listdir(schemas) if isfile(join(schemas,f)) ]
        for f in onlyfiles:
            zipincludes.append((os.path.join(schemas, f), os.path.join("jsonschema", "schemas", f)))

        path = QtCore.QCoreApplication.libraryPaths()[0]
        libEGL_path = os.path.join(path, "Scripts", "libEGL.dll")
        libsodium_path = os.path.join(path, "Scripts", "libsodium.dll")

        files = lambda mypath: [ f for f in os.listdir(mypath) if os.path.isfile(os.path.join(mypath,f)) ]
        for f in files(os.path.join(path, "Scripts", "plugins", "platforms")):
            includefiles.append((os.path.join(path, "Scripts", "plugins", "platforms", f), os.path.join("platforms", f) ))

        for f in files(os.path.join(path, "Scripts", "plugins", "imageformats")):
            includefiles.append((os.path.join(path, "Scripts", "plugins", "imageformats", f), os.path.join("imageformats", f) ))

        for f in files(os.path.join(path, "Scripts", "plugins", "iconengines")):
            includefiles.append((os.path.join(path, "Scripts", "plugins", "iconengines", f), os.path.join("iconengines", f) ))
    includefiles.append(libEGL_path)
    includefiles.append(libsodium_path)
else:
    schemas = os.path.join(site.getsitepackages()[0], "jsonschema", "schemas")
    onlyfiles = [ f for f in listdir(schemas) if isfile(join(schemas,f)) ]
    for f in onlyfiles:
        zipincludes.append((os.path.join(schemas, f), os.path.join("jsonschema", "schemas", f)))

if sys.platform == "darwin":
    info = subprocess.check_output(["brew", "info", "libsodium"])
    info = info.decode().splitlines(keepends=False)
    if len(info) > 1:
        library_path = info[3].split(" ")[0]
        libsodium_path = os.path.join(library_path, "lib",
                                      "libsodium.dylib")
        includefiles.append((libsodium_path, "lib/libsodium.dylib"))
        print(libsodium_path)
    else:
        print("Erreur : libsodium not found. Please install it with brew install libsodium.")

    qtconf_path = os.path.join(os.path.dirname(__file__), "res/osx/qt.conf")
    includefiles.append((qtconf_path, "qt.conf"))

print("Includes : ")
print(includes)
print("Excludes : ")
print(exclude)
print("Include files : ")
print(includefiles)
print("Zip files : ")
print(zipincludes)
print("Packages : ")
print(packages)
print("Sys.path : ")
print(sys.path)

options = {"path": sys.path,
           "includes": includes,
           "include_files": includefiles,
           "excludes": exclude,
           "packages": packages,
           "zip_includes": zipincludes
           }

#############################################################################
# preparation des cibles
base = None
file_type=""
icon="sakia.png"
if sys.platform == "win32":
    base = "Win32GUI"
    file_type=".exe"
    icon="sakia.ico"

target = Executable(
    script = "src/sakia/main.py",
    targetName="sakia"+file_type,
    base = base,
    icon = icon,
    )

#############################################################################
# creation du setup
setup(
    name = "sakia",
    version = "0.11.4",
    description = "UCoin client",
    author = "Inso",
    options = {"build_exe": options},
    executables = [target]
    )

