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
packages = ["gnupg"]

options = {"path": sys.path,
           "includes": includes,
           "excludes": excludes,
           "packages": packages,
           }

#############################################################################
# preparation des cibles
base = None
if sys.platform == "win32":
    base = "Win32GUI"

target = Executable(
    script = "src/cutecoin/__init__.py",
    base = base,
    compress = True,
    icon = None,
    )

#############################################################################
# creation du setup
setup(
    name = "cutecoin",
    version = "0.3.0",
    description = "UCoin client",
    author = "Inso",
    options = {"build_exe": options},
    executables = [target]
    )

