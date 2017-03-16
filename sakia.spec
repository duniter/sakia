# -*- mode: python -*-
from PyInstaller.compat import is_darwin, is_win, is_linux
import ctypes
import subprocess
import os

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
    info = subprocess.check_output(["brew", "info", "libsodium"])
    info = info.decode().splitlines(keepends=False)
    if len(info) > 1:
        library_path = info[3].split(" ")[0]
        libsodium_path = os.path.join(library_path, "lib",
                                      "libsodium.dylib")
        a.binaries = a.binaries + TOC([('lib/libsodium.dylib', libsodium_path, 'BINARY')])
    a.datas = a.datas + [('sakia/root_servers.yml', 'src/sakia/root_servers.yml', 'DATA')]

if is_linux:
    libsodium_path = ctypes.util.find_library('libsodium.so')
    if not libsodium_path:
        if os.path.isfile('/usr/lib/x86_64-linux-gnu/libsodium.so.13'):
            libsodium_path = "/usr/lib/x86_64-linux-gnu/libsodium.so.13"
        if os.path.isfile('/usr/lib/i386-linux-gnu/libsodium.so.13'):
            libsodium_path = "/usr/lib/i386-linux-gnu/libsodium.so.13"

    a.binaries = a.binaries + TOC([('libsodium.so', libsodium_path, 'BINARY')])
    a.datas = a.datas + [('sakia/root_servers.yml', 'src/sakia/root_servers.yml', 'DATA')]

if is_win:
    a.binaries = a.binaries + TOC([('libsodium.dll', ctypes.util.find_library('libsodium.dll'), 'BINARY')])
    a.datas = a.datas + [('sakia\\root_servers.yml', 'src\\/sakia\\root_servers.yml', 'DATA')]


for sql_file in ("meta.sql", "000_add_ud_rythm_parameters.sql", "001_add_contacts.sql"):
    if is_win:
        a.datas = a.datas + [('sakia\\data\\repositories\\{:}'.format(sql_file),
                              'src\\sakia\\data\\repositories\\{:}'.format(sql_file), 'DATA')]
    else:
        a.datas = a.datas + [('sakia/data/repositories/{:}'.format(sql_file),
                              'src/sakia/data/repositories/{:}'.format(sql_file), 'DATA')]

print(a.binaries)

pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

if is_linux or is_darwin:
    exe = EXE(pyz,
              a.scripts,
              exclude_binaries=True,
              name='sakia.bin',
              debug=True,
              strip=False,
              upx=True,
              console=True,
              icon='sakia.ico')
else:
    exe = EXE(pyz,
              a.scripts,
              exclude_binaries=True,
              name='sakia',
              debug=True,
              strip=False,
              upx=True,
              console=True,
              icon='sakia.ico')


coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='sakia')

if is_darwin:
    app = BUNDLE(exe,
         name='sakia.app',
         icon='sakia.ico',
         bundle_identifier=None,
         info_plist={
        'NSHighResolutionCapable': 'True',
        'LSBackgroundOnly': 'False'
        },)


