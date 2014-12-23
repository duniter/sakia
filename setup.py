#!/usr/bin/python
# -*- coding: utf-8 -*-

# source d'inspiration: http://wiki.wxpython.org/cx_freeze

import sys, os, subprocess, multiprocessing
from cx_Freeze import setup, Executable

#############################################################################
# preparation des options
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'lib')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

print(sys.path)
includes = ["sip", "re", "json", "logging", "hashlib", "os", "urllib", "ucoinpy", "requests"]
excludes = []
packages = ["libnacl", "pylibscrypt"]

includefiles = []

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
if sys.platform == "win32":
    base = "Win32GUI"
    file_type=".exe"

target = Executable(
    script = "src/cutecoin/main.py",
    targetName="cutecoin"+file_type,
    base = base,
    compress = False,
    icon = None,
    )

#############################################################################
# creation du setup
setup(
    name = "cutecoin",
    version = "0.5",
    description = "UCoin client",
    author = "Inso",
    options = {"build_exe": options},
    executables = [target]
    )

