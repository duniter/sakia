# -*- mode: python -*-
from PyInstaller.compat import is_darwin, is_win
import ctypes

block_cipher = None



a = Analysis(['src/sakia/main.py'],
             pathex=['.'],
             binaries=None,
             datas=None,
             hiddenimports=['six','packaging', 'packaging.version', 'packaging.specifiers'],
             hookspath=['hooks'],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)

if is_darwin:
    a.binaries = a.binaries - TOC([
     ('/usr/local/lib/libsodium.so', None, None),])

if is_win:
    a.binaries = a.binaries + TOC([('libsodium.dll',  ctypes.util.find_library('libsodium.dll'), 'BINARY')])
    print(a.binaries)

pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='sakia',
          debug=False,
          strip=False,
          upx=True,
          console=False,
          icon='sakia.ico')

coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='sakia')

