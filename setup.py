#!/usr/bin/python
# -*- coding: utf-8 -*-

# source d'inspiration: http://wiki.wxpython.org/cx_freeze

import sys, os, subprocess, multiprocessing
from cx_Freeze import setup, Executable
from PyQt5 import QtCore

#############################################################################
# preparation des options
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'lib')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

print(sys.path)
includes = ["sip", "re", "json", "logging",
            "hashlib", "os", "urllib",
            "ucoinpy", "pylibscrypt"]
excludes = ['.git']
packages = ["libnacl", "encodings"]

includefiles = []

if sys.platform == "win32":
    app = QtCore.QCoreApplication(sys.argv)
    libEGL_path = ""
    libsodium_path = ""
    print(QtCore.QCoreApplication.libraryPaths())
    for path in QtCore.QCoreApplication.libraryPaths():
        if os.path.isfile(os.path.join(os.path.dirname(path), "libEGL.dll")):
            libEGL_path = os.path.join(os.path.dirname(path), "libEGL.dll")

    if 'CONDA_ENV_PATH' in os.environ:
	# Check if we are in Conda env
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
elif sys.platform == "darwin":
    pass
else:
    libsodium_path = ""
    print(QtCore.QCoreApplication.libraryPaths())
    # Check if we are in Conda env
    if 'CONDA_ENV_PATH' in os.environ:
        libsodium_path = os.path.join(os.environ['CONDA_ENV_PATH'], "lib",
                                      "libsodium.so.13")
        includefiles.append((libsodium_path, "libsodium.so.13"))


options = {"path": sys.path,
           "includes": includes,
           "include_files": includefiles,
           "excludes": excludes,
           "packages": packages,
           }

#############################################################################
# preparation des cibles
base = None
file_type=""
icon="cutecoin.png"
if sys.platform == "win32":
    base = "Win32GUI"
    file_type=".exe"
    icon="cutecoin.ico"

target = Executable(
    script = "src/cutecoin/main.py",
    targetName="cutecoin"+file_type,
    base = base,
    icon = icon,
    )

#############################################################################
# creation du setup
setup(
    name = "cutecoin",
    version = "0.10",
    description = "UCoin client",
    author = "Inso",
    options = {"build_exe": options},
    executables = [target]
    )

