# -*- mode: python -*-
from PyInstaller.compat import is_darwin

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

pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='sakia',
          debug=True,
          strip=False,
          upx=True,
          console=True )

coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='sakia')

